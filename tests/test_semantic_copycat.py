from __future__ import annotations

import unittest

from bot.services.semantic_copycat import semantic_matches


class FakeEncoder:
    vectors = {
        "DOG Dog Coin": [1.0, 0.0],
        "PUP Puppy Currency": [0.9, 0.1],
        "MOON Lunar Rocket": [0.0, 1.0],
    }

    def encode(self, sentences, *, normalize_embeddings=False):
        self.normalize_embeddings = normalize_embeddings
        return [self.vectors[value] for value in sentences]


class SemanticCopycatTests(unittest.TestCase):
    def test_cosine_threshold_finds_semantic_match(self) -> None:
        model = FakeEncoder()
        matches = semantic_matches(
            "DOG", "Dog Coin",
            [("pup", "PUP", "Puppy Currency"), ("moon", "MOON", "Lunar Rocket")],
            model, 0.85,
        )
        self.assertEqual([mint for mint, _ in matches], ["pup"])
        self.assertTrue(model.normalize_embeddings)

    def test_empty_target_skips_encoder(self) -> None:
        class ExplodingEncoder:
            def encode(self, *args, **kwargs):
                raise AssertionError("encoder must not be called")

        self.assertEqual(
            semantic_matches(None, None, [("mint", "X", "Token")], ExplodingEncoder(), 0.85), []
        )


if __name__ == "__main__":
    unittest.main()
