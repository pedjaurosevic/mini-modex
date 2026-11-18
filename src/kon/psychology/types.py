"""
Psychology types — emotion detection, strategy selection, state tracking.
Mirrors mini-modex TypeScript types for API compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# =================================================================================================
# Emotion Detection
# =================================================================================================


class Emotion(str, Enum):
    ANXIETY = "anxiety"
    SADNESS = "sadness"
    ANGER = "anger"
    JOY = "joy"
    FEAR = "fear"
    EXHAUSTION = "exhaustion"
    SHAME = "shame"
    HOPE = "hope"
    NEUTRAL = "neutral"


@dataclass
class EmotionDetection:
    """Result of emotion detection from a user message."""
    emotion: Emotion
    intensity: float  # 0.0 to 1.0
    keywords: list[str] = field(default_factory=list)
    negated: bool = False
    attributed: bool = False
    past_tense: bool = False


# =================================================================================================
# Strategy Selection
# =================================================================================================


class TherapeuticStrategy(str, Enum):
    VALIDATION = "validation"
    SOCRATIC = "socratic"
    REFRAMING = "reframing"
    PSYCHOEDUCATION = "psychoeducation"
    BEHAVIORAL = "behavioral"
    METACOGNITIVE = "metacognitive"
    BOUNDARY = "boundary"
    CRISIS = "crisis-intervention"


@dataclass
class StrategySelection:
    """Selected therapeutic strategy and flags."""
    strategy: TherapeuticStrategy
    validation: bool = False
    socratic: bool = False
    reframing: bool = False
    psychoeducation: bool = False
    behavioral: bool = False
    boundary: bool = False
    crisis: bool = False


# =================================================================================================
# Psychology Result
# =================================================================================================


@dataclass
class PsychologyResult:
    """Complete psychology result for a conversation turn."""
    emotion: EmotionDetection
    strategy: StrategySelection
    trust_change: float = 0.0
    response: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


# =================================================================================================
# Psychology State
# =================================================================================================


@dataclass
class EmotionRecord:
    """Historical emotion record."""
    timestamp: str
    emotion: str
    intensity: float
    trigger: str
    context: str


@dataclass
class ConversationPattern:
    """Record of therapeutic pattern usage."""
    id: str
    type: str
    description: str
    effectiveness: float  # 0.0 to 1.0
    usage_count: int = 0
    last_used: str = ""


@dataclass
class TherapeuticGoal:
    """Therapeutic goal with milestones."""
    id: str
    description: str
    status: str = "active"  # active, achieved, abandoned
    created_at: str = ""
    updated_at: str = ""
    milestones: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PsychologyState:
    """Persistent psychology state."""
    patterns: list[ConversationPattern] = field(default_factory=list)
    goals: list[TherapeuticGoal] = field(default_factory=list)
    emotion_history: list[EmotionRecord] = field(default_factory=list)
    conversation_count: int = 0
    current_emotion: str = "neutral"
    current_intensity: float = 0.1
    trust_level: float = 0.5
    rapport_level: float = 0.5
    emotional_trend: str = "stable"  # stable, improving, declining, volatile
    concerns: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    last_interaction: str = ""
    session_count: int = 0
