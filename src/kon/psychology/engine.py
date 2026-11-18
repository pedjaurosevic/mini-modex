"""
Psychology Engine — High-level interface to mini-modex psychology API.

Provides emotion detection, strategy selection, and state management
for therapeutic conversations.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .client import PsychologyClient, PsychologyClientError
from .types import (
    ConversationPattern,
    Emotion,
    EmotionDetection,
    EmotionRecord,
    PsychologyResult,
    PsychologyState,
    StrategySelection,
    TherapeuticGoal,
    TherapeuticStrategy,
)


class PsychologyEngine:
    """
    High-level psychology engine that wraps the mini-modex API client.

    Manages emotion detection, strategy selection, and persistent state.
    Falls back to local detection if API is unavailable.
    """

    def __init__(
        self,
        api_url: str | None = None,
        state_dir: str | None = None,
        enabled: bool = True,
    ) -> None:
        self.client = PsychologyClient(base_url=api_url)
        self.enabled = enabled
        self.state_dir = Path(state_dir or os.path.expanduser("~/.kon/psychology"))
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._state_path = self.state_dir / "state.json"
        self._state = self._load_state()

    # ========================================================================
    # State Management
    # ========================================================================

    def _load_state(self) -> PsychologyState:
        """Load psychology state from disk."""
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text(encoding="utf-8"))
                return self._dict_to_state(data)
            except (json.JSONDecodeError, OSError):
                pass
        return PsychologyState()

    def _save_state(self) -> None:
        """Save psychology state to disk."""
        data = self._state_to_dict(self._state)
        self._state_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _dict_to_state(self, data: dict[str, Any]) -> PsychologyState:
        """Convert dict to PsychologyState."""
        patterns = [
            ConversationPattern(**p) for p in data.get("patterns", [])
        ]
        goals = [
            TherapeuticGoal(**g) for g in data.get("goals", [])
        ]
        emotions = [
            EmotionRecord(**e) for e in data.get("emotion_history", [])
        ]
        return PsychologyState(
            patterns=patterns,
            goals=goals,
            emotion_history=emotions,
            conversation_count=data.get("conversation_count", 0),
            current_emotion=data.get("current_emotion", "neutral"),
            current_intensity=data.get("current_intensity", 0.1),
            trust_level=data.get("trust_level", 0.5),
            rapport_level=data.get("rapport_level", 0.5),
            emotional_trend=data.get("emotional_trend", "stable"),
            concerns=data.get("concerns", []),
            interests=data.get("interests", []),
            last_interaction=data.get("last_interaction", ""),
            session_count=data.get("session_count", 0),
        )

    def _state_to_dict(self, state: PsychologyState) -> dict[str, Any]:
        """Convert PsychologyState to dict."""
        return {
            "patterns": [
                {
                    "id": p.id,
                    "type": p.type,
                    "description": p.description,
                    "effectiveness": p.effectiveness,
                    "usage_count": p.usage_count,
                    "last_used": p.last_used,
                }
                for p in state.patterns
            ],
            "goals": [
                {
                    "id": g.id,
                    "description": g.description,
                    "status": g.status,
                    "created_at": g.created_at,
                    "updated_at": g.updated_at,
                    "milestones": g.milestones,
                }
                for g in state.goals
            ],
            "emotion_history": [
                {
                    "timestamp": e.timestamp,
                    "emotion": e.emotion,
                    "intensity": e.intensity,
                    "trigger": e.trigger,
                    "context": e.context,
                }
                for e in state.emotion_history
            ],
            "conversation_count": state.conversation_count,
            "current_emotion": state.current_emotion,
            "current_intensity": state.current_intensity,
            "trust_level": state.trust_level,
            "rapport_level": state.rapport_level,
            "emotional_trend": state.emotional_trend,
            "concerns": state.concerns,
            "interests": state.interests,
            "last_interaction": state.last_interaction,
            "session_count": state.session_count,
        }

    # ========================================================================
    # Core Methods
    # ========================================================================

    async def detect_emotion(self, message: str) -> EmotionDetection:
        """
        Detect emotion from user message.

        Tries mini-modex API first, falls back to local detection.
        """
        if not self.enabled:
            return EmotionDetection(emotion=Emotion.NEUTRAL, intensity=0.1)

        try:
            data = await self.client.detect_emotion(message)
            return EmotionDetection(
                emotion=Emotion(data.get("emotion", "neutral")),
                intensity=data.get("intensity", 0.1),
                keywords=data.get("keywords", []),
                negated=data.get("negated", False),
                attributed=data.get("attributed", False),
                past_tense=data.get("past_tense", False),
            )
        except PsychologyClientError:
            # Fallback: simple keyword-based detection
            return self._local_detect_emotion(message)

    async def choose_strategy(
        self,
        message: str,
        emotion: Emotion | str,
        conversation_history: list[str] | None = None,
    ) -> StrategySelection:
        """
        Choose therapeutic strategy based on emotion and context.

        Tries mini-modex API first, falls back to local selection.
        """
        if not self.enabled:
            return StrategySelection(strategy=TherapeuticStrategy.VALIDATION)

        emotion_str = emotion.value if isinstance(emotion, Emotion) else emotion

        try:
            data = await self.client.choose_strategy(
                message=message,
                emotion=emotion_str,
                conversation_history=conversation_history,
            )
            return StrategySelection(
                strategy=TherapeuticStrategy(data.get("strategy", "validation")),
                validation=data.get("validation", False),
                socratic=data.get("socratic", False),
                reframing=data.get("reframing", False),
                psychoeducation=data.get("psychoeducation", False),
                behavioral=data.get("behavioral", False),
                boundary=data.get("boundary", False),
                crisis=data.get("crisis", False),
            )
        except PsychologyClientError:
            # Fallback: simple rule-based selection
            return self._local_choose_strategy(emotion_str, conversation_history)

    async def process_turn(
        self,
        message: str,
        conversation_history: list[str] | None = None,
    ) -> PsychologyResult:
        """
        Process a conversation turn: detect emotion, choose strategy.

        Returns complete psychology result with trust change.
        """
        # Detect emotion
        emotion = await self.detect_emotion(message)

        # Choose strategy
        strategy = await self.choose_strategy(
            message=message,
            emotion=emotion.emotion,
            conversation_history=conversation_history,
        )

        # Calculate trust change
        trust_change = self._calculate_trust_change(emotion, strategy)

        # Update state
        self._update_state(message, emotion, strategy, trust_change)

        return PsychologyResult(
            emotion=emotion,
            strategy=strategy,
            trust_change=trust_change,
        )

    # ========================================================================
    # Fallback Local Detection
    # ========================================================================

    def _local_detect_emotion(self, message: str) -> EmotionDetection:
        """Simple keyword-based emotion detection (fallback)."""
        lower = message.lower()

        # English + Serbian emotion keywords
        emotions: dict[Emotion, list[str]] = {
            Emotion.ANXIETY: [
                "anxious", "worried", "worry", "nervous", "stress", "stres",
                "anksiozan", "anksiozna", "briga", "brige", "nervozan",
                "panika", "strah", "plašim se", "nemir", "razmišljam",
                "glava", "petlja", "posao", "brinem se", "teško",
            ],
            Emotion.SADNESS: [
                "sad", "depressed", "down", "unhappy", "tuzan", "tuzna",
                "depresivan", "depresija", "tuga", "usamljen", "sam",
                "plakanje", "jadan", "bez nade", "beznađe",
            ],
            Emotion.ANGER: [
                "angry", "furious", "mad", "irritated", "annoyed", "ljut",
                "ljuta", "ljutnja", "mrzim", "mrzim", "besan", "frustrated",
            ],
            Emotion.JOY: [
                "happy", "joy", "glad", "srećan", "srećna", "radost",
                "srećan sam", "srećna sam", "dobar dan", "odlično",
            ],
            Emotion.FEAR: [
                "afraid", "fear", "plašim se", "strah", "uplašen", "uplašena",
                "bojim se", "panika", "teror",
            ],
            Emotion.EXHAUSTION: [
                "exhausted", "tired", "iscrpljen", "iscrpljena", "umoran",
                "umorna", "umoran sam", "umorna sam", "nema snage",
            ],
        }

        detected: Emotion = Emotion.NEUTRAL
        max_matches = 0
        keywords: list[str] = []

        for emotion, keywords_list in emotions.items():
            matches = sum(1 for kw in keywords_list if kw in lower)
            if matches > max_matches:
                max_matches = matches
                detected = emotion
                keywords = [kw for kw in keywords_list if kw in lower]

        intensity = min(1.0, max_matches * 0.3)

        return EmotionDetection(
            emotion=detected,
            intensity=intensity,
            keywords=keywords,
        )

    def _local_choose_strategy(
        self,
        emotion: str,
        conversation_history: list[str] | None = None,
    ) -> StrategySelection:
        """Simple rule-based strategy selection (fallback)."""
        has_history = conversation_history is not None and len(conversation_history) > 0

        if emotion in ("anxiety", "fear"):
            if has_history:
                return StrategySelection(
                    strategy=TherapeuticStrategy.SOCRATIC,
                    socratic=True,
                    validation=True,
                )
            return StrategySelection(
                strategy=TherapeuticStrategy.REFRAMING,
                reframing=True,
                validation=True,
            )
        elif emotion == "sadness":
            return StrategySelection(
                strategy=TherapeuticStrategy.REFRAMING,
                reframing=True,
                behavioral=True,
                validation=True,
            )
        elif emotion == "anger":
            return StrategySelection(
                strategy=TherapeuticStrategy.SOCRATIC,
                socratic=True,
                validation=True,
            )
        elif emotion == "exhaustion":
            return StrategySelection(
                strategy=TherapeuticStrategy.PSYCHOEDUCATION,
                psychoeducation=True,
                behavioral=True,
                validation=True,
            )
        elif emotion in ("joy", "hope"):
            return StrategySelection(
                strategy=TherapeuticStrategy.VALIDATION,
                validation=True,
            )
        else:
            return StrategySelection(
                strategy=TherapeuticStrategy.VALIDATION,
                validation=True,
            )

    # ========================================================================
    # Trust & State Updates
    # ========================================================================

    def _calculate_trust_change(
        self,
        emotion: EmotionDetection,
        strategy: StrategySelection,
    ) -> float:
        """Calculate trust change based on emotion and strategy."""
        change = 0.0

        # Positive: validation + positive emotion
        if strategy.validation and emotion.emotion in (Emotion.JOY, Emotion.HOPE):
            change += 0.05
        if strategy.validation and emotion.emotion in (Emotion.ANXIETY, Emotion.SADNESS):
            change += 0.03  # Validation helps even with negative emotions

        # Negative: wrong strategy
        if strategy.socratic and emotion.emotion in (Emotion.ANXIETY, Emotion.SADNESS):
            change -= 0.02  # Socratic too early can hurt trust

        # Crisis: boundary setting
        if strategy.crisis or strategy.boundary:
            change += 0.02  # Boundaries build trust

        return max(-0.1, min(0.1, change))

    def _update_state(
        self,
        message: str,
        emotion: EmotionDetection,
        strategy: StrategySelection,
        trust_change: float,
    ) -> None:
        """Update psychology state after a turn."""
        self._state.conversation_count += 1
        self._state.current_emotion = emotion.emotion.value
        self._state.current_intensity = emotion.intensity
        self._state.trust_level = max(0.0, min(1.0, self._state.trust_level + trust_change))
        self._state.last_interaction = datetime.now().isoformat()

        # Update emotional trend
        if self._state.emotion_history:
            recent = self._state.emotion_history[-5:]
            negative_count = sum(
                1 for e in recent
                if e.emotion in ("anxiety", "sadness", "anger", "fear")
            )
            if negative_count >= 4:
                self._state.emotional_trend = "declining"
            elif negative_count <= 1:
                self._state.emotional_trend = "improving"
            else:
                self._state.emotional_trend = "volatile"

        # Add emotion record
        self._state.emotion_history.append(EmotionRecord(
            timestamp=datetime.now().isoformat(),
            emotion=emotion.emotion.value,
            intensity=emotion.intensity,
            trigger=message[:100],
            context=message[:200],
        ))

        # Keep only last 100 emotion records
        if len(self._state.emotion_history) > 100:
            self._state.emotion_history = self._state.emotion_history[-100:]

        # Extract concerns from message
        lower = message.lower()
        concern_keywords = ["problem", "teško", "težak", "teška", "briga", "brige",
                           "stres", "anksiozan", "anksiozna", "depresivan", "depresija",
                           "nesanica", "nesan", "umoran", "umorna", "usamljen"]
        for kw in concern_keywords:
            if kw in lower and kw not in self._state.concerns:
                self._state.concerns.append(kw)
                if len(self._state.concerns) > 20:
                    self._state.concerns = self._state.concerns[-20:]

        self._save_state()

    # ========================================================================
    # Query Methods
    # ========================================================================

    def get_state(self) -> PsychologyState:
        """Get current psychology state."""
        return self._state

    def get_summary(self) -> str:
        """Get human-readable psychology summary."""
        lines = [
            f"Emotion: {self._state.current_emotion} ({self._state.current_intensity:.0%})",
            f"Trust: {self._state.trust_level:.0%}",
            f"Rapport: {self._state.rapport_level:.0%}",
            f"Trend: {self._state.emotional_trend}",
            f"Sessions: {self._state.session_count}",
            f"Conversations: {self._state.conversation_count}",
        ]
        if self._state.concerns:
            lines.append(f"Concerns: {', '.join(self._state.concerns[:5])}")
        return "\n".join(lines)

    async def health_check(self) -> bool:
        """Check if mini-modex API is available."""
        return await self.client.health_check()

    async def close(self) -> None:
        """Close API client."""
        await self.client.close()
