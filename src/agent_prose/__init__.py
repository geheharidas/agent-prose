"""
agent-prose: Deterministic Anti-RLHF Stylometric Gate for Autonomous Agents.
Created and maintained by Nitivra.
"""
from __future__ import annotations

__version__ = "1.0.2"
__author__ = "Nitivra"

from agent_prose.engine import ProseEngine
from agent_prose.profiles import get_profile, resolve_locale

__all__ = ["ProseEngine", "get_profile", "resolve_locale", "__version__"]
