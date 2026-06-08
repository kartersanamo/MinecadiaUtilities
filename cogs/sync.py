from discord.ext import commands
import json


def _parse_json_safe(text: str):
    """Parse first JSON object from text; handles API returning multiple objects or trailing data."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text)
    return obj

class Sync(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client


async def setup(client:commands.Bot) -> None:
  await client.add_cog(Sync(client))
