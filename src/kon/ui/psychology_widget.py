"""Psychology status widget for kon TUI."""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static


class PsychologyWidget(Static):
    """Small widget showing current psychology state."""

    DEFAULT_CLASSES = "psychology-widget"
    DEFAULT_CSS = """
    PsychologyWidget {
        height: auto;
        padding: 0 1;
        color: $accent;
        display: none;
    }

    PsychologyWidget.-visible {
        display: block;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._emotion = "neutral"
        self._intensity = 0.1
        self._trust = 0.5
        self._trend = "stable"
        self._visible = False

    def update(
        self,
        emotion: str = "neutral",
        intensity: float = 0.1,
        trust: float = 0.5,
        trend: str = "stable",
    ) -> None:
        """Update widget with psychology data."""
        self._emotion = emotion
        self._intensity = intensity
        self._trust = trust
        self._trend = trend
        self._update_display()

    def _update_display(self) -> None:
        """Update the displayed text."""
        emotion_colors = {
            "anxiety": "yellow",
            "sadness": "blue",
            "anger": "red",
            "joy": "green",
            "fear": "magenta",
            "exhaustion": "cyan",
            "neutral": "gray",
        }
        color = emotion_colors.get(self._emotion, "gray")
        trend_icons = {
            "improving": "↑",
            "declining": "↓",
            "volatile": "↕",
            "stable": "→",
        }
        trend_icon = trend_icons.get(self._trend, "→")
        
        self.update_renderable(
            f"[bold cyan]🧠[/bold cyan] "
            f"[bold {color}]{self._emotion}[/bold {color}] "
            f"({self._intensity:.0%}) "
            f"trust: {self._trust:.0%} "
            f"{trend_icon} {self._trend}"
        )

    def toggle_visibility(self, visible: bool) -> None:
        """Show or hide the widget."""
        self._visible = visible
        if visible:
            self.add_class("-visible")
        else:
            self.remove_class("-visible")
        self.refresh()

    def on_mount(self) -> None:
        """Initialize display."""
        self._update_display()
