import contextlib
import time
from typing import Dict
from rich.console import Console, Group
from rich.live import Live
from rich.progress import Progress
from rich.spinner import Spinner

class GeneticAlgorithmConsoleManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GeneticAlgorithmConsoleManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, 'initialized'):
            self.console = Console()
            self.progress = Progress()
            self.spinners: Dict[str, Spinner] = {}
            self.live = None
            self.ga_bar = None
            self.initialized = True

    def add_spinner(self, text):
        """Add a spinner with the given text."""
        self.spinners[text] = Spinner("dots", text=text)

    def remove_spinner(self, text):
        """Remove a spinner by its text."""
        if text in self.spinners:
            del self.spinners[text]

    @contextlib.contextmanager
    def spinner(self, text):
        """Context manager to add and remove a spinner."""
        try:
            self.add_spinner(text)
            if self.live:
                self.live.update(self._render())
            yield
        finally:
            self.remove_spinner(text)
            if self.live:
                self.live.update(self._render())

    def update_progress(self, advance_amount=1):
        """Update the progress bar and live display."""
        if self.ga_bar is not None:
            self.progress.advance(self.ga_bar, advance_amount)
            if self.live:
                self.live.update(self._render())

    def _render(self):
        """Render the progress bar and spinners."""
        spinners = list(self.spinners.values())
        return Group(
            self.progress,
            *spinners,
        )

    @contextlib.contextmanager
    def __call__(self, total=100):
        """Context manager to setup and manage the progress and live display."""
        try:
            self.ga_bar = self.progress.add_task('Genetic algorithm...', total=total)
            self.live = Live(self._render(), console=self.console, refresh_per_second=10)
            self.live.start()
            yield self
        finally:
            self.progress.stop()
            if self.live:
                self.live.stop()
            # Reset state
            self.live = None
            self.ga_bar = None
            self.spinners.clear()
