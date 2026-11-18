"""
Psychology System Prompt Builder

Adds psychology context to kon's system prompt for therapeutic conversations.
"""

from __future__ import annotations

from .types import Emotion, PsychologyState


def build_psychology_prompt(state: PsychologyState | None = None) -> str:
    """
    Build psychology section for system prompt.

    Provides the LLM with emotion detection guidelines and
    therapeutic strategy selection rules.
    """
    lines = [
        "# Psychology Module",
        "",
        "## Emotion Detection",
        "",
        "Detect the user's emotional state from their messages. Use these emotions:",
        "",
        "- **anxiety**: worry, stress, nervousness, fear of failure",
        "- **sadness**: depression, loneliness, hopelessness, grief",
        "- **anger**: frustration, irritation, rage, hatred",
        "- **joy**: happiness, contentment, satisfaction, gratitude",
        "- **fear**: anxiety about safety, panic, terror",
        "- **exhaustion**: burnout, fatigue, depletion, overwhelm",
        "",
        "## Therapeutic Strategies",
        "",
        "Select appropriate strategies based on detected emotion:",
        "",
        "- **validation**: Acknowledge and normalize feelings (first turn, or when user needs support)",
        "- **socratic questioning**: Ask guiding questions to explore thoughts (when user has insight)",
        "- **reframing**: Help user see situations from different perspectives",
        "- **psychoeducation**: Provide information about mental health concepts",
        "- **behavioral activation**: Suggest concrete actions to improve mood",
        "- **boundary setting**: Set limits when user crosses therapeutic boundaries",
        "- **crisis intervention**: Immediate safety response for self-harm or emergency",
        "",
        "## Strategy Selection Rules",
        "",
        "1. **First turn**: Always start with validation",
        "2. **Anxiety/Fear**: Validation → Reframing → Socratic (if insight detected)",
        "3. **Sadness**: Validation → Behavioral Activation → Reframing",
        "4. **Anger**: Validation → Socratic → Reframing",
        "5. **Exhaustion**: Validation → Psychoeducation → Behavioral Activation",
        "6. **Joy/Hope**: Validation → Reinforcement",
        "",
        "## Safety Guidelines",
        "",
        "- If user mentions self-harm, suicide, or medical emergency: CRISIS INTERVENTION",
        "- Provide crisis resources and encourage professional help",
        "- Never provide medical advice",
        "- Set clear boundaries when appropriate",
        "",
    ]

    if state:
        lines.extend([
            "",
            "## Current User State",
            "",
            f"- Current emotion: {state.current_emotion}",
            f"- Intensity: {state.current_intensity:.0%}",
            f"- Trust level: {state.trust_level:.0%}",
            f"- Emotional trend: {state.emotional_trend}",
        ])
        if state.concerns:
            lines.append(f"- Concerns: {', '.join(state.concerns[:5])}")

    return "\n".join(lines)


def inject_psychology_into_prompt(
    system_prompt: str,
    state: PsychologyState | None = None,
) -> str:
    """
    Inject psychology section into existing system prompt.

    Args:
        system_prompt: Existing system prompt
        state: Current psychology state (optional)

    Returns:
        System prompt with psychology section appended
    """
    psychology_section = build_psychology_prompt(state)
    return f"{system_prompt}\n\n{psychology_section}"
