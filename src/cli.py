from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from langchain.callbacks.base import BaseCallbackHandler

console = Console()

class FinnieStream(BaseCallbackHandler):
    """
    One global spinner shared by every nested LLM call.
    The spinner starts when the first LLM begins and stops after the last ends.
    """
    def __init__(self):
        self._live: Live | None = None
        self._spinner: Spinner | None = None
        self._buffer: str = ""
        self._printed_prefix = False
        self._depth = 0                      # NEW: how many LLMs are active

    # ── LLM lifecycle hooks ─────────────────────────────────────────────
    def on_llm_start(self, *_, **__):
        if self._depth == 0:                 # only for the first call
            self._spinner = Spinner("dots", text="thinking…")
            self._live = Live(self._spinner, console=console, refresh_per_second=8)
            self._live.start()
        self._depth += 1                     # track nesting level

    def on_llm_new_token(self, token: str, **__):
        # Accumulate until newline ONLY if we’re in an EVENT
        self._buffer += token

        # ── EVENT line complete? ───────────────────────────────────────────
        if self._buffer.startswith("EVENT:") and "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if self._spinner:
                self._spinner.text = line[6:].strip()
            return

        # ── Normal token: print instantly ─────────────────────────────────
        if not self._buffer.startswith("EVENT:"):
            if not self._printed_prefix:
                self._stop_spinner()
                console.print("[cyan bold]Finnie:[/bold cyan] ", end="")
                self._printed_prefix = True

            console.print(token, style="cyan", end="", soft_wrap=True)
            self._buffer = ""

    def on_llm_end(self, *_, **__):
        self._depth -= 1
        if self._depth == 0:                 # outer-most call finished
            self._stop_spinner()
            if self._printed_prefix:
                console.print()
            self._reset_state()

    def on_llm_error(self, *_, **__):        # NEW: clean up on errors
        self._depth = max(self._depth - 1, 0)
        if self._depth == 0:
            self._stop_spinner()
            self._reset_state()

    # ── helpers ────────────────────────────────────────────────────────
    def _stop_spinner(self):
        if self._live:
            self._live.stop()
            self._live = None
            self._spinner = None

    def _reset_state(self):
        self._buffer = ""
        self._printed_prefix = False
