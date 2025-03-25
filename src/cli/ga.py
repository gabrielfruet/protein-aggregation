import contextlib
from collections import OrderedDict

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.spinner import Spinner
from rich.text import Text


class GeneticAlgorithmConsoleManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GeneticAlgorithmConsoleManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "initialized"):
            self.console = Console()
            self.main_progress = Progress(
                TextColumn("[progress.description][bright_blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(
                    "[progress.percentage][bright_blue]{task.percentage:>3.0f}%"
                ),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=self.console,
            )
            self.spinners: OrderedDict[str, Spinner] = OrderedDict()
            self.live = None
            self.ga_bar = None
            self.panel = None
            self.initialized = True

    def log(self, text):
        self.console.log(text)

    def add_spinner(self, text, name="dots"):
        """Add a spinner with the given text."""
        self.spinners[text] = Spinner(name, text=text)

    def remove_spinner(self, text):
        """Remove a spinner by its text."""
        if text in self.spinners:
            del self.spinners[text]

    def update_spinner(self, text):
        self.spinners[text].update(text=text)

    @contextlib.contextmanager
    def spinner(self, text, name="dots"):
        """Context manager to add and remove a spinner."""
        try:
            self.add_spinner(text, name)
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
            self.main_progress.advance(self.ga_bar, advance_amount)
            if self.live:
                self.live.update(self._render())

    def _render(self):
        """Render the progress bar and spinners."""
        spinners = list(self.spinners.values())
        return Group(
            self.panel,
            self.main_progress,
            *spinners,
        )

    def metric_after_generation(self, emga):
        # Use GAMetricCalculator to get metrics
        from src.genetic.instance import GAMetricCalculator

        metric_calc = GAMetricCalculator(emga)

        # Prepare metrics
        current_generation = metric_calc.generation()
        best_fitness = metric_calc.best_fitness()
        worst_fitness = metric_calc.worst_fitness()
        mean_fitness = metric_calc.mean()
        std_dev_fitness = metric_calc.std()
        population_size = metric_calc.population_size()

        # Calculate fitness change (if possible)
        try:
            best_fitness_change = metric_calc.change_in_best_fitness()
            worst_fitness_change = metric_calc.change_in_worst_fitness()
        except IndexError:
            best_fitness_change = 0
            worst_fitness_change = 0

        # Create a styled markdown with rich formatting
        markdown_content = Text()
        markdown_content.append(
            "# 🧬 Genetic Algorithm Progress\n\n", style="bold magenta"
        )

        # Generation and Population Info
        markdown_content.append("## 🏁 Generation Overview\n", style="bold green")
        markdown_content.append(f"- **Generation**: {current_generation}\n", style="")
        markdown_content.append(
            f"- **Population Size**: {population_size}\n\n", style=""
        )

        # Fitness Metrics
        markdown_content.append("## 📊 Fitness Metrics\n", style="bold green")

        # Best Fitness with change indicator
        best_change_style = "green" if best_fitness_change >= 0 else "red"
        markdown_content.append(
            f"- **Best Fitness**: {best_fitness:.3f} ", style="bold"
        )
        markdown_content.append(
            f"({'▲' if best_fitness_change >= 0 else '▼'} {abs(best_fitness_change):.3f})\n",
            style=best_change_style,
        )

        # Worst Fitness with change indicator
        worst_change_style = "green" if worst_fitness_change <= 0 else "red"
        markdown_content.append(f"- **Worst Fitness**: {worst_fitness:.3f} ", style="")
        markdown_content.append(
            f"({'▼' if worst_fitness_change <= 0 else '▲'} {abs(worst_fitness_change):.3f})\n",
            style=worst_change_style,
        )

        # Mean and Standard Deviation
        markdown_content.append(f"- **Mean Fitness**: {mean_fitness:.3f}\n", style="")
        markdown_content.append(
            f"- **Fitness Std Dev**: {std_dev_fitness:.3f}\n", style=""
        )

        # Convert to Markdown for Rich rendering
        rich_markdown = Markdown(str(markdown_content))

        # Create a panel with the markdown
        panel = Panel(
            rich_markdown,
            title="Genetic Algorithm Metrics",
            border_style="bold blue",
            expand=False,
        )

        self.panel = panel

    @contextlib.contextmanager
    def __call__(self, emga, total=100):
        """Context manager to setup and manage the progress and live display."""
        try:
            self.ga_bar = self.main_progress.add_task("Running the GA", total=total)
            self.metric_after_generation(emga)
            self.live = Live(
                self._render(), console=self.console, refresh_per_second=10
            )
            self.live.start()
            yield self
        finally:
            self.main_progress.stop()
            if self.live:
                self.live.stop()
            # Reset state
            self.live = None
            self.ga_bar = None
            self.spinners.clear()
