"""
Psychology TUI Sidebar Component

Textual widget for displaying psychology state in kon's TUI.
Inspired by mini-modex TUI sidebar design.
"""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static
from textual.binding import Binding


class PsychologySidebar(Widget):
    """
    Sidebar widget displaying psychology state.

    Shows:
    - Current emotion with color coding
    - Strategy selection
    - Trust and rapport levels
    - Emotional trend
    - Conversation metrics
    """

    DEFAULT_CLASSES = "psychology-sidebar"
    DEFAULT_CSS = """
    PsychologySidebar {
        width: 40;
        height: 100%;
        border-left: solid $accent;
        background: $surface;
    }

    PsychologySidebar > .emotion-display {
        height: 3;
        padding: 1;
    }

    PsychologySidebar > .metrics-section {
        height: auto;
        padding: 1;
    }

    PsychologySidebar > .trend-display {
        height: 2;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._emotion = "neutral"
        self._intensity = 0.1
        self._strategy = "validation"
        self._trust = 0.5
        self._rapport = 0.5
        self._trend = "stable"
        self._sessions = 0
        self._conversations = 0
        self._concerns: list[str] = []

    def update(
        self,
        emotion: str,
        intensity: float,
        strategy: str,
        trust: float,
        rapport: float,
        trend: str,
        sessions: int,
        conversations: int,
        concerns: list[str] | None = None,
    ) -> None:
        """Update sidebar with new psychology data."""
        self._emotion = emotion
        self._intensity = intensity
        self._strategy = strategy
        self._trust = trust
        self._rapport = rapport
        self._trend = trend
        self._sessions = sessions
        self._conversations = conversations
        if concerns is not None:
            self._concerns = concerns
        self.refresh()

    def render(self) -> str:
        """Render sidebar content."""
        lines = [
            "[bold cyan]🧠 Psychology[/bold cyan]",
            "",
            f"  Emotion: [bold {self._get_emotion_color()}]{self._emotion}[/bold {self._get_emotion_color()}] ({self._intensity:.0%})",
            f"  Strategy: [cyan]{self._strategy}[/cyan]",
            "",
            "[bold cyan]👤 User Model[/bold cyan]",
            "",
            f"  Trust: {self._render_bar(self._trust)} {self._trust:.0%}",
            f"  Rapport: {self._render_bar(self._rapport)} {self._rapport:.0%}",
            f"  Trend: {self._get_trend_icon()} {self._trend}",
            f"  Sessions: {self._sessions}",
            f"  Conversations: {self._conversations}",
        ]

        if self._concerns:
            lines.extend([
                "",
                "[bold cyan]Concerns[/bold cyan]",
            ])
            for concern in self._concerns[:5]:
                lines.append(f"  • {concern}")

        return "\n".join(lines)

    def _get_emotion_color(self) -> str:
        """Get color for current emotion."""
        colors = {
            "anxiety": "yellow",
            "sadness": "blue",
            "anger": "red",
            "joy": "green",
            "fear": "magenta",
            "exhaustion": "cyan",
            "neutral": "gray",
        }
        return colors.get(self._emotion, "gray")

    def _get_trend_icon(self) -> str:
        """Get icon for emotional trend."""
        icons = {
            "improving": "↑",
            "declining": "↓",
            "volatile": "↕",
            "stable": "→",
        }
        return icons.get(self._trend, "→")

    def _render_bar(self, value: float, width: int = 10) -> str:
        """Render a progress bar."""
        filled = int(value * width)
        empty = width - filled
        return "█" * filled + "░" * empty

    def on_mount(self) -> None:
        """Set initial content."""
        self.render()
