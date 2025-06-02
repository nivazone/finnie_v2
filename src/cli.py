from rich.console import Console
from langchain.callbacks.base import BaseCallbackHandler
from rich.live import Live
from rich.spinner import Spinner

console = Console()

class FinnieStream(BaseCallbackHandler):
    """
    Streams LLM tokens in cyan.  Shows a spinner while waiting for first token.
    """
    def __init__(self):
        self._printed_prefix = False
        self._live: Live | None = None

    def on_llm_start(self, *_, **__):
        self._live = Live(
            Spinner("dots", text="thinking…"),
            console=console,
            refresh_per_second=8,
        )
        self._live.start()

    def on_llm_new_token(self, token: str, **__):
        if not self._printed_prefix:
            if self._live:
                self._live.stop()
                self._live = None
            console.print("[cyan bold]Finnie:[/bold cyan] ", end="")
            self._printed_prefix = True

        console.print(token, style="cyan", end="")

    def on_llm_end(self, *_, **__):
        if self._live:
            self._live.stop()
            self._live = None
        if self._printed_prefix:
            console.print()
        self._printed_prefix = False
