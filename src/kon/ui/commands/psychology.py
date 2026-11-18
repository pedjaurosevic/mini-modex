"""Psychology command: /psychology - show and toggle psychology module state."""

from __future__ import annotations

from kon import config

from ..chat import ChatLog
from ..floating_list import ListItem
from ..selection_mode import SelectionMode
from .base import CommandSupport


class PsychologyCommands(CommandSupport):
    """Handle /psychology slash command."""

    def _handle_psychology_command(self, args: str) -> None:
        chat = self.query_one("#chat-log", ChatLog)

        if not args.strip():
            # Show current state
            self._show_psychology_status(chat)
            return

        requested = args.strip().lower()

        if requested in ("on", "enable", "true"):
            self._toggle_psychology(True, chat)
        elif requested in ("off", "disable", "false"):
            self._toggle_psychology(False, chat)
        elif requested == "status":
            self._show_psychology_status(chat)
        elif requested == "state":
            self._show_psychology_state(chat)
        elif requested == "reset":
            self._reset_psychology_state(chat)
        else:
            chat.add_info_message(
                f"Unknown psychology command: {requested}. "
                f"Use: on, off, status, state, reset",
                error=True,
            )

    def _show_psychology_status(self, chat: ChatLog) -> None:
        enabled = config.psychology.enabled
        status = "enabled" if enabled else "disabled"
        chat.add_info_message(
            f"Psychology module: {status}\n"
            f"API URL: {config.psychology.api_url}\n"
            f"Auto-detect: {config.psychology.auto_detect}\n"
            f"Trust update: {config.psychology.trust_update}\n"
            f"Emotion tracking: {config.psychology.emotion_tracking}\n"
            f"State dir: {config.psychology.state_dir}",
        )

    def _show_psychology_state(self, chat: ChatLog) -> None:
        """Show current psychology state from the engine."""
        if self._runtime.agent is None:
            chat.add_info_message("Agent not initialized", error=True)
            return

        # Try to get psychology state from the agent
        engine = getattr(self._runtime.agent, '_psychology_engine', None)
        if engine is None:
            chat.add_info_message(
                "Psychology engine not initialized. "
                "Make sure the module is enabled in config.",
                error=True,
            )
            return

        try:
            state = engine.get_state()
            summary = engine.get_summary()
            chat.add_info_message(f"Psychology State:\n\n{summary}")
        except Exception as e:
            chat.add_info_message(f"Error reading psychology state: {e}", error=True)

    def _toggle_psychology(self, enabled: bool, chat: ChatLog) -> None:
        """Toggle psychology module on/off."""
        current = config.psychology.enabled
        if current == enabled:
            chat.add_info_message(f"Psychology module is already {'enabled' if enabled else 'disabled'}")
            return

        # Update config
        config.psychology.enabled = enabled
        chat.add_info_message(
            f"Psychology module {'enabled' if enabled else 'disabled'}. "
            f"Change applies on next conversation (use /new) or kon restart.",
            warning=True,
        )

    def _reset_psychology_state(self, chat: ChatLog) -> None:
        """Reset psychology state."""
        engine = getattr(self._runtime.agent, '_psychology_engine', None)
        if engine is None:
            chat.add_info_message("Psychology engine not initialized", error=True)
            return

        try:
            # Reset state by reloading from disk (clear in-memory)
            from pathlib import Path
            state_path = Path(engine.state_dir) / "state.json"
            if state_path.exists():
                state_path.unlink()
                chat.add_info_message("Psychology state reset. New state will be created on next interaction.")
            else:
                chat.add_info_message("No psychology state to reset.")
        except Exception as e:
            chat.add_info_message(f"Error resetting psychology state: {e}", error=True)

    def _build_psychology_items(self) -> list[ListItem]:
        """Build items for psychology settings picker."""
        enabled = config.psychology.enabled
        return [
            ListItem(
                value="toggle",
                label="toggle",
                description="on" if enabled else "off",
            ),
            ListItem(
                value="state",
                label="state",
                description="show current state",
            ),
            ListItem(
                value="reset",
                label="reset",
                description="reset psychology state",
            ),
        ]

    def _handle_psychology_select(self, item_value: str) -> str:
        """Handle psychology picker selection."""
        chat = self.query_one("#chat-log", ChatLog)

        if item_value == "toggle":
            current = config.psychology.enabled
            self._toggle_psychology(not current, chat)
            return "reopened-picker"
        elif item_value == "state":
            self._show_psychology_state(chat)
            return "closed"
        elif item_value == "reset":
            self._reset_psychology_state(chat)
            return "closed"

        return "closed"
