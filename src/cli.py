from rich.console import Console
from langchain.callbacks.base import BaseCallbackHandler
import asyncio
import re

console = Console()

class FinnieStream(BaseCallbackHandler):
    async def on_custom_event(self, name, data, run_id, tags=None, metadata=None, **kwargs):
        msg = data["friendly_msg"]

        tokens = re.finditer(r"\S+|\s", msg, re.DOTALL)

        for match in tokens:
            token = match.group(0)
            console.print(token, style="gray23", end="", soft_wrap=True)
            await asyncio.sleep(0.08)
        

    def on_llm_new_token(self, token: str, **__):
        console.print(token, style="cyan", end="", soft_wrap=True)

