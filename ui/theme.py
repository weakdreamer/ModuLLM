"""Theme management for AppUI: colors, spacing, fonts, and dark mode support."""

from typing import Dict

LIGHT = {
    # softer off-white background
    "bg": "#FBFBFD",
    "msg_bg_user": "#DCF8C6",
    "msg_bg_assistant": "#F6F6F7",
    "text": "#0F1720",
    "muted": "#6B7280",
    "accent": "#1877F2",
    # selection contrast color (distinct from accent)
    "selection": "#0A63D8",
    # history row highlight (gentle, not clashing)
    "history_selected": "#E6F0FF",
    "bubble_radius": 10,
    "padding_x": 12,
    "padding_y": 8,
}

DARK = {
    # softer near-black background
    "bg": "#0F1724",
    "msg_bg_user": "#114E2D",
    "msg_bg_assistant": "#232A2F",
    "text": "#E6EEF6",
    "muted": "#94A3B8",
    "accent": "#4DA3FF",
    # selection contrast color distinct from accent
    "selection": "#5CC6FF",
    # history row highlight (gentle, not clashing)
    "history_selected": "#0F2740",
    "bubble_radius": 10,
    "padding_x": 12,
    "padding_y": 8,
}

THEMES: Dict[str, Dict] = {"light": LIGHT, "dark": DARK}


def get_theme(name: str = "light") -> Dict:
    return THEMES.get(name, LIGHT)
