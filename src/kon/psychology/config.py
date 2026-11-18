"""
Psychology configuration for Kon.

Adds psychology settings to kon's config system.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PsychologyConfig(BaseModel):
    """Configuration for the psychology module."""
    enabled: bool = True
    api_url: str = "http://localhost:18083"
    state_dir: str = "~/.kon/psychology"
    auto_detect: bool = True
    auto_strategy: bool = True
    trust_update: bool = True
    emotion_tracking: bool = True
    pattern_recording: bool = True
    max_emotion_history: int = 100
    fallback_enabled: bool = True  # Use local detection if API unavailable
