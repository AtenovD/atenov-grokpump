from __future__ import annotations

import base64
import hashlib
import time
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

from cryptography.fernet import Fernet

from bot.services.oauth import (
    OAuthSettings, TokenCipher, XaiOAuthClient, complete_oauth_callback, generate_pkce,
)
from bot.services.storage import Storage


class OAuthTests(unittest.IsolatedAsyncioTestCase):
    def test_pkce_is_s256_without_padding(self) -> None:
        pair = generate_pkce()
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(pair.verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertEqual(pair.challenge, expected)
        self.assertNotIn("=", pair.challenge)
        self.assertGreaterEqual(len(pair.verifier), 43)

    def test_fernet_round_trip(self) -> None:
        cipher = TokenCipher(Fernet.generate_key().decode())
        encrypted = cipher.encrypt("secret-access-token")
        self.assertNotIn("secret-access-token", encrypted)
        self.assertEqual(cipher.decrypt(encrypted), "secret-access-token")

    async def asyncSetUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.storage = Storage(f"{self.tmp.name}/oauth.db")
        await self.storage.connect()
        self.settings = OAuthSettings(
            "client-id", "client-secret", "https://example.com/oauth/callback",
            Fernet.generate_key().decode(),
        )
        self.client = XaiOAuthClient(self.settings)

    async def asyncTearDown(self) -> None:
        await self.storage.close()
        self.tmp.cleanup()

    async def test_pending_callback_exchange_and_encrypted_storage(self) -> None:
        url = await self.client.begin(self.storage, 12345)
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["redirect_uri"], [self.settings.redirect_uri])

        self.client.exchange_code = AsyncMock(return_value={
            "access_token": "access-plain",
            "refresh_token": "refresh-plain",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "openid offline_access",
        })
        user_id = await complete_oauth_callback(
            self.storage, self.client, object(), query["state"][0], "auth-code"
        )

        self.assertEqual(user_id, 12345)
        record = await self.storage.get_oauth_tokens(user_id)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertNotEqual(record.access_token_encrypted, "access-plain")
        self.assertEqual(self.client.cipher.decrypt(record.access_token_encrypted), "access-plain")
        self.assertGreater(record.expires_at, int(time.time()))
        args = self.client.exchange_code.await_args.args
        self.assertEqual(args[1], "auth-code")
        self.assertGreaterEqual(len(args[2]), 43)
        self.assertIsNone(await self.storage.consume_oauth_pending(query["state"][0]))


if __name__ == "__main__":
    unittest.main()
