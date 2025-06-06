from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from langchain.callbacks.base import BaseCallbackHandler

console = Console()

class FinnieStream(BaseCallbackHandler):
    """
    One Live spinner that keeps running; its text updates on each EVENT line.
    Normal reply tokens stop the spinner and stream in cyan.
    """
    def __init__(self):
        self._live: Live | None = None
        self._spinner: Spinner | None = None
        self._buffer: str = ""
        self._printed_prefix = False

    # ── LLM lifecycle hooks ─────────────────────────────────────────────
    def on_llm_start(self, *_, **__):
        self._spinner = Spinner("dots", text="thinking…")
        self._live = Live(self._spinner, console=console, refresh_per_second=8)
        self._live.start()

    def on_llm_new_token(self, token: str, **__):
        self._buffer += token

        # process complete lines
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)

            # ── EVENT: update spinner text ────────────────────────────
            if line.startswith("EVENT:"):
                if self._spinner:
                    self._spinner.text = line[6:].strip()
                continue

            # ── normal streamed output ───────────────────────────────
            # stop spinner only once, before first visible token
            if not self._printed_prefix:
                self._stop_spinner()
                console.print("[cyan bold]Finnie:[/bold cyan] ", end="")
                self._printed_prefix = True

            console.print(line, style="cyan", end="")

    def on_llm_end(self, *_, **__):
        self._stop_spinner()
        if self._printed_prefix:
            console.print()
            
        # reset state
        self._buffer = ""
        self._printed_prefix = False

    # ── helpers ────────────────────────────────────────────────────────
    def _stop_spinner(self):
        if self._live:
            self._live.stop()
            self._live = None
            self._spinner = None
