from __future__ import annotations

from bot.services.storage import Storage

TOKEN_CHAIN = "robinhood"
NFT_CHAIN = "robinhood-nft"


async def cross_surface_note(storage: Storage, creator: str | None, this_chain: str) -> str | None:
    """Flags when the same creator address also has a launch on the other
    Robinhood surface (token vs NFT collection).

    This is a notable pattern either way it goes: a serious builder shipping
    both a token and a collection, or a coordinated scam reusing one address
    across surfaces to double the take. It says nothing on its own about
    which — callers surface it as a flag for a human or another agent to
    weigh alongside everything else.
    """
    if not creator or this_chain not in (TOKEN_CHAIN, NFT_CHAIN):
        return None
    other_chain = NFT_CHAIN if this_chain == TOKEN_CHAIN else TOKEN_CHAIN
    chains = await storage.creator_chains(creator)
    if other_chain not in chains:
        return None
    other_kind = "an NFT collection" if this_chain == TOKEN_CHAIN else "a token"
    return f"same creator also has {other_kind} on Robinhood Chain - cross-surface activity"
