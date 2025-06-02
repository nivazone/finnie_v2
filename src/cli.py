from rich.console import Console
from langchain.callbacks.base import BaseCallbackHandler

console = Console()

class FinnieStream(BaseCallbackHandler):
    """Stream LLM tokens to the terminal in cyan with 'Finnie:' prefix."""
    def __init__(self):
        self._printed_prefix = False

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if not self._printed_prefix:
            console.print("[cyan bold]Finnie:[/bold cyan] ", end="")
            self._printed_prefix = True
        console.print(token, style="cyan", end="")

    def on_llm_end(self, *_, **__) -> None:
        console.print()
        self._printed_prefix = False
