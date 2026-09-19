"""Base dialect profile schema for agent-prose."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Pattern


@dataclass
class DialectProfile:
    """Configuration for a specific regional dialect or language standard."""

    code: str
    name: str
    allow_serial_comma: bool = False
    allow_ize_spelling: bool = False
    banned_stem_words: List[str] = field(default_factory=list)
    banned_exact_phrases: List[str] = field(default_factory=list)
    context_exemptions: Dict[str, List[Pattern]] = field(default_factory=dict)
    spelling_corrections: Dict[str, str] = field(default_factory=dict)

    def is_exempt(self, label: str, line: str) -> bool:
        """Check if a match in line is shielded by domain context exemptions."""
        exemptions = self.context_exemptions.get(label, [])
        for pattern in exemptions:
            if pattern.search(line):
                return True
        return False
