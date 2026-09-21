"""
Universal Stylometric Evaluation Engine for agent-prose.
Created and maintained by Nitivra.

Evaluates text and markdown files against anti-RLHF stylometric standards:
  - Banned AI-tell vocabulary and filler stems
  - Transition word padding
  - Non-ASCII characters
  - Dialect-specific orthography (-ise vs -ize)
  - Contractions
  - Construction patterns (headlines, false balance, throat-clearing)
  - Em-dash density
  - Serial (Oxford) comma
  - Comma density and interrupter clauses
  - Sentence length limits and section averages
  - Burstiness standard deviation and monotone runs
  - Repeated sentence openers
  - Trailing participial clauses
  - Rule-of-three triads
  - Copula avoidance
  - Sycophancy phrases
  - Process flow arrows
"""
from __future__ import annotations

import json
import os
import re
import statistics
from bisect import bisect_right
from collections import namedtuple
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Pattern, Sequence, Tuple

from agent_prose.profiles.base import DialectProfile
from agent_prose.profiles import resolve_locale

Sentence = namedtuple("Sentence", ["line_num", "text", "word_count", "comma_count", "opener"])
Section = namedtuple("Section", ["heading", "start_line", "sentences"])

# ---------------------------------------------------------------------------
# Universal Constants
# ---------------------------------------------------------------------------

BLOCKING_CHECKS = {
    "non_ascii",
    "ize_spelling",
    "contractions",
    "flow_arrows",
}

DEFAULT_ADVISORY_THRESHOLD = 4

TRANSITION_WORDS = ["moreover", "furthermore", "additionally"]
TRANSITION_THRESHOLD = 3

DASH_DENSITY_THRESHOLD = 3

NON_ASCII_REPLACEMENTS = {
    "\u2014": "--",    # em dash
    "\u2013": "-",     # en dash
    "\u2192": "rewrite the flow in prose (not '->')",    # arrow
    "\u201c": '"',     # curly open double quote
    "\u201d": '"',     # curly close double quote
    "\u2018": "'",     # curly open single quote
    "\u2019": "'",     # curly close single quote
    "\u2022": "*",     # bullet
    "\u2026": "...",   # ellipsis
    "\u00a0": " ",     # non-breaking space
}

IZE_PATTERN = re.compile(r"\b\w+ize[ds]?\b", re.IGNORECASE)
IZE_EXCEPTIONS = {"size", "sized", "sizes", "prize", "prized", "prizes", "seize", "seized", "seizes"}

CONTRACTIONS = re.compile(
    r"\b(it's|don't|can't|won't|isn't|doesn't|wouldn't|shouldn't|couldn't|"
    r"we're|they're|we've|didn't|hasn't|haven't|wasn't|weren't|"
    r"that's|there's|here's|what's|who's|let's)\b",
    re.IGNORECASE,
)

CONSTRUCTION_PATTERNS = [
    # 3.5a -- "X -- Y" headline
    (re.compile(r"^[#\s>*-]*[A-Za-z][^\n]{3,60}\s+(?:--|\u2014|\u2013)\s+[A-Za-z][^\n]{3,80}$", re.MULTILINE),
        "subject/headline 'X -- Y' construction (3.5a)"),
    # 3.5b/c -- "Not just X but Y" / "It is not X -- it is Y"
    (re.compile(r"\b(?:it\s+is\s+)?not\s+(?:just|merely|only|simply)\b[^\n.!?]{0,80}\b(?:but|--|\u2014)\b", re.IGNORECASE),
        "'not just X, but Y' construction (3.5b)"),
    (re.compile(r"\bit\s+is\s+not\s+[a-z][^\n.!?]{0,40}(?:--|\u2014)\s*it\s+is\s+", re.IGNORECASE),
        "'it is not X -- it is Y' construction (3.5c)"),
    # 3.5d -- "whether X or Y"
    (re.compile(r"\bwhether\s+(?:you\s+are|the\s+goal|your)\b[^\n.!?]{0,80}\bor\b", re.IGNORECASE),
        "'whether X or Y' framing (3.5d)"),
    # 3.5e -- "From X to Y" headline
    (re.compile(r"^[#\s>*-]*from\s+[A-Z][^\n.!?]{2,40}\s+to\s+[A-Z][^\n.!?]{2,40}$", re.MULTILINE | re.IGNORECASE),
        "'From X to Y' headline (3.5e)"),
    # 3.5f -- "Imagine [scenario]" opener
    (re.compile(r"(?:^|\.\s+)imagine\s+(?:a\s|an\s|the\s|how\s|what\s)", re.IGNORECASE),
        "'Imagine [scenario]' opener (3.5f)"),
    # 3.5g -- fake-conversational scaffolding
    (re.compile(r"\b(?:here\s+is\s+(?:the\s+thing|what\s+i\s+mean)|let\s+me\s+(?:explain|unpack|walk\s+you|be\s+clear))\b", re.IGNORECASE),
        "fake-conversational scaffolding (3.5g)"),
    # 3.5h -- "X is more than just Y"
    (re.compile(r"\bis\s+more\s+than\s+(?:just\s+)?[a-z]", re.IGNORECASE),
        "'X is more than just Y' construction (3.5h)"),
    # 3.5j -- throat-clearing intensifiers
    (re.compile(r"(?:^|[.!?]\s+)(?:the\s+)?(?:reality|truth|fact)\s+is\s+(?:that\s+)?[a-z]", re.IGNORECASE),
        "'the reality/truth/fact is' filler (3.5j)"),
    # 3.5k -- "What has changed is" / "What is different now is"
    (re.compile(r"\bwhat\s+(?:has\s+changed|is\s+different(?:\s+now)?)\b[^.!?\n]{0,40}\bis\b", re.IGNORECASE),
        "'what has changed / is different now' reframing (3.5k)"),
    # 3.5l -- "X has historically meant Y"
    (re.compile(r"\bhas\s+historically\s+(?:meant|been|required)\b", re.IGNORECASE),
        "'has historically meant' framing (3.5l)"),
    # 3.5m -- triple-em-dash interrupted sentence
    (re.compile(r"(?:--|\u2014)(?=[^.!?\n]*[A-Za-z])[^.!?\n]{1,80}(?:--|\u2014)"),
        "triple-em-dash interruption -- two dashes in one sentence (3.5m)"),
    # 3.5p -- "Not only X, but also Y" synthetic balance
    (re.compile(r"\bnot\s+only\b[^\n.!?]{2,80}\bbut\s+(?:also\s+)?[a-z]", re.IGNORECASE),
        "'not only X, but also Y' synthetic balance (3.5p)"),
    # 3.5q -- Fronted gerund paragraph opener
    (re.compile(r"^[#\s>*-]*By\s+[a-z]+ing\b[^\n.!?]{10,60},", re.MULTILINE),
        "fronted gerund paragraph opener 'By ...ing,' (3.5q)"),
    # 3.5r -- Performative structural signposting
    (re.compile(r"(?:^|[.!?]\s+)(?:in\s+this\s+section,?\s+(?:we|we\s+will)|before\s+examining|before\s+we\s+turn\s+to|let\s+us\s+now\s+turn\s+to)\b", re.IGNORECASE),
        "performative structural signposting (3.5r)"),
    # 3.5s -- Concessive throat-clearing hedge
    (re.compile(r"(?:^|[.!?]\s+)(?:that\s+being\s+said|to\s+be\s+sure|while\s+it\s+is\s+true\s+that),?\s+[a-z]", re.IGNORECASE),
        "concessive throat-clearing hedge (3.5s)"),
    # 3.5t -- Prescriptive outro opener
    (re.compile(r"(?:^|[.!?]\s+)(?:moving\s+forward|looking\s+ahead),?\s+(?:we|organisations|teams|enterprises|leadership)\s+(?:must|should|need\s+to)\b", re.IGNORECASE),
        "prescriptive outro cliche (3.5t)"),
]

MIN_SENTENCE_WORDS = 3
SERIAL_COMMA_RE = re.compile(r",\s+(?:and|or)\b", re.IGNORECASE)
SERIAL_COMMA_MIN_COMMAS = 2
SERIAL_COMMA_MAX_ITEM_WORDS = 6

COMMA_DENSITY_THRESHOLD = 3
INTERRUPTER_RE = re.compile(
    r"^(?:[A-Za-z][\w\-]*[\s]){0,4}[A-Za-z][\w\-]*,\s+"
    r"(?:which|who|however|for example|in particular|following[^,]{2,50}|[a-z][^,]{2,50}),\s+"
    r"(?:is|are|was|were|has|have|had|will|would|can|could|must|should|provides?|remains?|includes?|confirmed|agreed|noted|discussed)\b"
)

SENT_MAX_WORDS = 35
SECTION_AVG_MAX_WORDS = 24.0
SECTION_MIN_SENTENCES_FOR_AVG = 3

BURSTINESS_MIN_SENTENCES = 5
BURSTINESS_MIN_STDEV = 6.0
BURSTINESS_MIN_MEAN = 18.0
BURSTINESS_UNIFORM_BAND = (15, 35)
MONOTONE_RUN_LENGTH = 4
MONOTONE_RUN_DELTA = 4
MONOTONE_MIN_WORDS = 10

OPENER_SECTION_THRESHOLD = 3
OPENER_DOC_THRESHOLD = 6
OPENER_MIN_WORDS = 4

TRAILING_PARTICIPIAL_RE = re.compile(r",\s*([A-Za-z]+ing)\b[^.;:!?]*[.!?]?\s*$")
TRAILING_WITH_ABSOLUTE_RE = re.compile(
    r",\s*with\s+(?:[\w\-]+\s+){0,3}([A-Za-z]+ing)\b[^.;:!?]*[.!?]?\s*$", re.IGNORECASE
)
PARTICIPIAL_EXEMPT = {
    "including", "following", "during", "regarding", "concerning", "pending",
    "notwithstanding", "according", "depending", "using", "owing", "barring",
    "excluding", "considering", "assuming", "morning", "evening",
    "everything", "nothing", "something", "anything", "king", "spring", "string",
}
TRAILING_PARTICIPIAL_MIN_WORDS = 8

TRIAD_LINE_RE = re.compile(
    r"^\s*(?:[*_]{0,2})[A-Z][A-Za-z\-]{1,14}\.\s+[A-Z][A-Za-z\-]{1,14}\.\s+[A-Z][A-Za-z\-]{1,14}\.(?:[*_]{0,2})\s*$"
)
TRIAD_TAIL_RE = re.compile(
    r"\b([A-Za-z\-]{3,14}),\s+([A-Za-z\-]{3,14}),?\s+and\s+([A-Za-z\-]{3,14})(?:\s+[A-Za-z\-]{3,20})?[.!?:]"
)
_ADJ_SUFFIX_RE = re.compile(r"(?:able|ible|al|ive|ous|ful|less|ant|ent|ic|ed)$", re.IGNORECASE)

COPULA_AVOIDANCE_RE = re.compile(
    r"\b(serves?\s+as|stands?\s+as|represents?\s+a\b|marks?\s+a\b|boasts?\b|constitutes?\s+a\b|functions?\s+as)\b",
    re.IGNORECASE,
)
COPULA_EXEMPTIONS = [
    re.compile(r"\brepresents?\s+a\s+(client|party|member|stakeholder|risk|change|shift)\b", re.IGNORECASE),
]

SYCOPHANCY_PHRASES = [
    "you're absolutely right", "you are absolutely right", "great question",
    "excellent question", "fantastic question", "i hope this email finds you well",
    "i hope this message finds you well", "i hope this finds you well",
    "please do not hesitate to", "thank you so much for your patience",
    "i appreciate your patience", "happy to help", "i trust this email finds you",
]
SYCOPHANCY_OPENER_RE = re.compile(r"^\s*(?:certainly|absolutely|perfect|great)\s*[!.]", re.IGNORECASE)

INLINE_CODE_RE = re.compile(r"`[^`]*`")
FLOW_ARROW_RE = re.compile(r"(?<![-<>=!])->(?![->])|\u2192")

_ABBREV_RE = re.compile(r"\b(e\.g|i\.e|etc|vs|Dr|Mr|Mrs|Ms|Prof|No|Fig|approx|dept|govt)\.", re.IGNORECASE)
_PAREN_RE = re.compile(r"\([^)]*\)")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_H12_MD_RE = re.compile(r"^#{1,2}\s+(.+)$")
_HTML_H12_RE = re.compile(r"<h[12]\b[^>]*>(.*?)</h[12]>", re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")

OPT_OUT_MARKERS = [
    "agent-prose: off",
    "writing-quality: off",
    "prose: off",
]


@dataclass
class Finding:
    """Individual rule violation record."""

    check_id: str
    severity: str
    message: str
    line_number: int | None = None
    snippet: str = ""


@dataclass
class ScanResult:
    """Consolidated result of a stylometric scan."""

    messages: List[str]
    findings: List[Finding]
    exit_code: int
    is_exempt: bool = False
    profile_code: str = ""

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    @property
    def blocking_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "BLOCKING")

    @property
    def advisory_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "ADVISORY")


class ProseEngine:
    """Stylometric verification engine parameterized by a DialectProfile."""

    def __init__(
        self,
        profile: DialectProfile | None = None,
        strict: bool = False,
        advisory_threshold: int = DEFAULT_ADVISORY_THRESHOLD,
    ) -> None:
        self.profile = profile or resolve_locale()
        self.strict = strict
        self.advisory_threshold = advisory_threshold
        self._compiled_banned_patterns: List[Tuple[Pattern, str]] = self._compile_banned()

    def _compile_banned(self) -> List[Tuple[Pattern, str]]:
        """Precompile regexes for banned stems and phrases."""
        patterns: List[Tuple[Pattern, str]] = []
        stem_suffixes = r"(?:e[ds]?|es|ing|s|d|ly)?"

        for word in self.profile.banned_stem_words:
            if word.endswith("e"):
                base = word[:-1]
                p = re.compile(r"\b" + re.escape(base) + r"(?:e[ds]?|es|ing|s|d|ely)?\b", re.IGNORECASE)
            else:
                p = re.compile(r"\b" + re.escape(word) + stem_suffixes + r"\b", re.IGNORECASE)
            patterns.append((p, word))

        for phrase in self.profile.banned_exact_phrases:
            p = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
            patterns.append((p, phrase))

        patterns.append(
            (re.compile(r"\bin\s+today['\u2019]s\b", re.IGNORECASE), "in today's")
        )
        return patterns

    def has_opt_out(self, lines: Sequence[str], filepath: str = "") -> bool:
        """Check if file opts out via in-band markers or environment settings."""
        if filepath and self._is_file_exempt(filepath):
            return True

        for line in lines[:5]:
            for marker in OPT_OUT_MARKERS:
                if marker in line:
                    allow_opt_out = os.environ.get("AGENT_PROSE_ALLOW_OPT_OUT", "1")
                    return allow_opt_out in ("1", "true", "True")
        return False

    def _is_file_exempt(self, filepath: str) -> bool:
        """Check repository exemption configuration files."""
        if not filepath:
            return False
        try:
            import fnmatch
            target = Path(filepath).resolve()
            candidates = [
                target.parent / ".prose" / "exemptions.json",
                target.parent / ".agent-prose" / "exemptions.json",
                target.parent / ".signal" / "exemptions.json",
            ]
            for p in target.parents:
                candidates.append(p / ".prose" / "exemptions.json")
                candidates.append(p / ".agent-prose" / "exemptions.json")
                candidates.append(p / ".signal" / "exemptions.json")

            for cfg in candidates:
                if cfg.is_file():
                    with open(cfg, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    base = os.path.basename(filepath)
                    for pattern in data.get("exempt_files", []):
                        if fnmatch.fnmatch(base, pattern) or fnmatch.fnmatch(str(target), pattern):
                            return True
        except Exception:
            pass
        return False

    # -----------------------------------------------------------------------
    # Segmentation
    # -----------------------------------------------------------------------

    def segment_sections(self, lines: Sequence[str], is_html: bool = False) -> List[Section]:
        """Segment lines into Sections of Sentences.
        
        Boundary detection relies on H1 and H2 tags or markdown headings.
        Fenced code spans, table rows, and frontmatter are excluded.
        """
        sections: List[Section] = []
        cur_heading = "(document start)"
        cur_start = 1
        cur_sentences: List[Sentence] = []
        block_parts: List[Tuple[int, str]] = []
        in_code = False
        in_frontmatter = False

        def flush_block() -> None:
            nonlocal block_parts
            if block_parts:
                cur_sentences.extend(self._split_block(block_parts))
                block_parts = []

        def flush_section(next_heading: str, next_start: int) -> None:
            nonlocal cur_heading, cur_start, cur_sentences
            flush_block()
            sections.append(Section(cur_heading, cur_start, cur_sentences))
            cur_heading = next_heading
            cur_start = next_start
            cur_sentences = []

        for line_num, raw in enumerate(lines, 1):
            line = raw.rstrip("\n")
            stripped = line.strip()

            if line_num == 1 and stripped == "---":
                in_frontmatter = True
                continue
            if in_frontmatter:
                if stripped == "---":
                    in_frontmatter = False
                continue
            if stripped.startswith("```"):
                in_code = not in_code
                flush_block()
                continue
            if in_code:
                continue
            if stripped.startswith("|") or stripped.startswith("<!--"):
                flush_block()
                continue

            heading_text = None
            if is_html:
                m = _HTML_H12_RE.search(line)
                if m:
                    heading_text = _HTML_TAG_RE.sub("", m.group(1)).strip()
            else:
                m = _H12_MD_RE.match(stripped)
                if m:
                    heading_text = m.group(1).strip()

            if heading_text is not None:
                flush_section(heading_text, line_num)
                continue
            if not is_html and stripped.startswith("#"):
                flush_block()
                continue

            text = _HTML_TAG_RE.sub(" ", line) if is_html else line
            if not text.strip():
                flush_block()
                continue

            if _BULLET_RE.match(text):
                flush_block()
                block_parts = [(line_num, _BULLET_RE.sub("", text, count=1))]
                flush_block()
            else:
                block_parts.append((line_num, text))

        flush_section("(end)", len(lines) + 1)
        if sections and sections[-1].heading == "(end)" and not sections[-1].sentences:
            sections.pop()
        return sections

    def _split_block(self, parts: List[Tuple[int, str]]) -> List[Sentence]:
        """Split a paragraph block into Sentence tuples."""
        if not parts:
            return []
        offsets: List[Tuple[int, int]] = []
        texts: List[str] = []
        pos = 0
        for line_num, text in parts:
            offsets.append((pos, line_num))
            texts.append(text)
            pos += len(text) + 1
        block = " ".join(texts)

        masked = _ABBREV_RE.sub(lambda m: m.group(0).replace(".", "\x00"), block)

        boundaries = [0]
        for m in _SENT_SPLIT_RE.finditer(masked):
            boundaries.append(m.end())
        boundaries.append(len(masked))

        offset_starts = [o[0] for o in offsets]
        sentences: List[Sentence] = []
        for i in range(len(boundaries) - 1):
            seg = masked[boundaries[i]:boundaries[i + 1]].replace("\x00", ".").strip()
            if not seg:
                continue
            words = _WORD_RE.findall(seg)
            alpha_words = [w for w in words if w[0].isalpha()]
            opener = " ".join(alpha_words[:2]).lower() if len(alpha_words) >= 2 else None
            idx = bisect_right(offset_starts, boundaries[i]) - 1
            line_num = offsets[max(idx, 0)][1]
            comma_count = _PAREN_RE.sub("", seg).count(",")
            sentences.append(Sentence(line_num, seg, len(words), comma_count, opener))
        return sentences

    # -----------------------------------------------------------------------
    # Individual Checks
    # -----------------------------------------------------------------------

    @staticmethod
    def _filter_code_lines(lines: Sequence[str]) -> List[Tuple[int, str]]:
        """Return (line_num, line) tuples excluding lines inside fenced code blocks."""
        filtered: List[Tuple[int, str]] = []
        in_code = False
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            filtered.append((line_num, line))
        return filtered

    def scan_banned_words(self, lines: Sequence[str]) -> List[Tuple[int, str, str]]:
        """Find banned AI-tell stems, respecting profile domain exemptions."""
        findings = []
        for line_num, line in self._filter_code_lines(lines):
            for pattern, label in self._compiled_banned_patterns:
                if pattern.search(line):
                    if not self.profile.is_exempt(label, line):
                        findings.append((line_num, label, line.strip()[:100]))
        return findings

    def scan_transitions(self, lines: Sequence[str]) -> List[Tuple[int, str]]:
        """Count transition word overuse."""
        count = 0
        locations = []
        for line_num, line in self._filter_code_lines(lines):
            line_lower = line.lower()
            for tw in TRANSITION_WORDS:
                if re.search(r"\b" + tw + r"\b", line_lower):
                    count += 1
                    locations.append((line_num, tw))
        if count >= TRANSITION_THRESHOLD:
            return locations
        return []

    def scan_non_ascii(self, lines: Sequence[str]) -> List[Tuple[int, str, str]]:
        """Flag non-ASCII characters that require standard ASCII equivalents."""
        findings = []
        for line_num, line in enumerate(lines, 1):
            for char, replacement in NON_ASCII_REPLACEMENTS.items():
                if char in line:
                    name = {
                        "\u2014": "em dash", "\u2013": "en dash", "\u2192": "arrow",
                        "\u201c": "curly open quote", "\u201d": "curly close quote",
                        "\u2018": "curly open single", "\u2019": "curly close single",
                        "\u2022": "bullet", "\u2026": "ellipsis", "\u00a0": "NBSP",
                    }.get(char, f"U+{ord(char):04X}")
                    findings.append((line_num, name, f"replace with: {replacement}"))
        return findings

    def scan_ize_spellings(self, lines: Sequence[str]) -> List[Tuple[int, str, str]]:
        """Flag -ize spellings when prohibited by dialect standard."""
        if self.profile.allow_ize_spelling:
            return []
        findings = []
        for line_num, line in self._filter_code_lines(lines):
            for match in IZE_PATTERN.finditer(line):
                word = match.group().lower()
                if word not in IZE_EXCEPTIONS:
                    findings.append((line_num, match.group(), line.strip()[:100]))
        return findings

    def scan_contractions(self, lines: Sequence[str]) -> List[Tuple[int, str, str]]:
        """Flag informal contractions."""
        findings = []
        for line_num, line in self._filter_code_lines(lines):
            for match in CONTRACTIONS.finditer(line):
                findings.append((line_num, match.group(), line.strip()[:100]))
        return findings

    def scan_dash_density(self, lines: Sequence[str], is_html: bool = False) -> List[Tuple[int, int, str]]:
        """Count em-dashes per section, flagging densities above limit."""
        findings = []
        section_start = 1
        section_heading = "(document start)"
        in_code_fence = False
        em_dash_count = 0

        h_re_html = re.compile(r"<h[12]\b[^>]*>(.*?)</h[12]>", re.IGNORECASE)
        h_re_md = re.compile(r"^#{1,2}\s+(.+)$")

        def count_dashes(line: str) -> int:
            depth = 0
            idx = 0
            count = 0
            while idx < len(line):
                ch = line[idx]
                if ch == "<":
                    depth += 1
                elif ch == ">":
                    depth = max(0, depth - 1)
                elif depth == 0:
                    if line[idx] == "\u2014":
                        count += 1
                    elif idx + 1 < len(line) and line[idx] == "-" and line[idx + 1] == "-":
                        run_end = idx
                        while run_end < len(line) and line[run_end] == "-":
                            run_end += 1
                        if run_end - idx == 2:
                            count += 1
                        idx = run_end - 1
                idx += 1
            return count

        def flush_section(end_line: int) -> None:
            nonlocal section_start, section_heading, em_dash_count
            if em_dash_count > DASH_DENSITY_THRESHOLD:
                findings.append((section_start, em_dash_count, section_heading[:60]))
            em_dash_count = 0
            section_start = end_line + 1

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_fence = not in_code_fence
                continue
            if in_code_fence:
                continue
            if stripped.startswith("|") and re.fullmatch(r"\|[\s\-:|]+\|?", stripped) is not None:
                continue

            heading_match = None
            if is_html:
                m = h_re_html.search(line)
                if m:
                    heading_match = m.group(1).strip()
            else:
                m = h_re_md.match(stripped)
                if m:
                    heading_match = m.group(1).strip()

            if heading_match is not None:
                flush_section(line_num - 1)
                section_heading = heading_match

            em_dash_count += count_dashes(line)

        flush_section(len(lines))
        return findings

    def scan_constructions(self, lines: Sequence[str]) -> List[Tuple[int, str, str]]:
        """Find AI structural construction patterns."""
        findings = []
        cleaned_lines = []
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                cleaned_lines.append("")
                continue
            if in_code:
                cleaned_lines.append("")
            else:
                cleaned_lines.append(line)
        full_text = "\n".join(cleaned_lines)
        for pattern, label in CONSTRUCTION_PATTERNS:
            for match in pattern.finditer(full_text):
                line_num = full_text.count("\n", 0, match.start()) + 1
                snippet = match.group(0).strip()[:80]
                findings.append((line_num, label, snippet))
        return findings

    def scan_serial_comma(self, sections: Sequence[Section]) -> List[Tuple[int, str]]:
        """Flag serial (Oxford) commas when prohibited by dialect standard."""
        if self.profile.allow_serial_comma:
            return []
        findings = []
        for sec in sections:
            for s in sec.sentences:
                if s.comma_count < SERIAL_COMMA_MIN_COMMAS:
                    continue
                for m in SERIAL_COMMA_RE.finditer(s.text):
                    before = s.text[:m.start()]
                    prev = before.rfind(",")
                    if prev == -1:
                        continue
                    between_words = _WORD_RE.findall(before[prev + 1:])
                    if 1 <= len(between_words) <= SERIAL_COMMA_MAX_ITEM_WORDS:
                        findings.append((s.line_num, s.text.strip()[:80]))
                        break
        return findings

    def scan_comma_density(self, sections: Sequence[Section]) -> List[Tuple[int, str, str]]:
        """Flag sentences with 3+ commas or parenthetical interrupters."""
        findings = []
        for sec in sections:
            for s in sec.sentences:
                if s.comma_count >= COMMA_DENSITY_THRESHOLD:
                    findings.append((s.line_num, f"{s.comma_count} commas", s.text.strip()[:80]))
                elif INTERRUPTER_RE.match(s.text):
                    findings.append((s.line_num, "interrupter clause between subject and verb", s.text.strip()[:80]))
        return findings

    def scan_sentence_length(
        self, sections: Sequence[Section]
    ) -> Tuple[List[Tuple[int, int, str]], List[Tuple[int, float, str]]]:
        """Flag sentences exceeding 35 words and sections averaging over 24 words."""
        long_sentences = []
        heavy_sections = []
        for sec in sections:
            counted = [s for s in sec.sentences if s.word_count >= MIN_SENTENCE_WORDS]
            for s in counted:
                if s.word_count > SENT_MAX_WORDS:
                    long_sentences.append((s.line_num, s.word_count, s.text.strip()[:80]))
            if len(counted) >= SECTION_MIN_SENTENCES_FOR_AVG:
                mean = statistics.mean(s.word_count for s in counted)
                if mean > SECTION_AVG_MAX_WORDS:
                    heavy_sections.append((sec.start_line, mean, sec.heading[:50]))
        return long_sentences, heavy_sections

    def scan_burstiness(
        self, sections: Sequence[Section]
    ) -> Tuple[List[Tuple[int, int, float, float, str]], List[Tuple[int, int, int]]]:
        """Flag uniform sentence distributions (low variance) and monotone length runs."""
        uniform = []
        for sec in sections:
            counted = [s for s in sec.sentences if s.word_count >= MIN_SENTENCE_WORDS]
            if len(counted) < BURSTINESS_MIN_SENTENCES:
                continue
            wcs = [s.word_count for s in counted]
            stdev = statistics.pstdev(wcs)
            mean = statistics.mean(wcs)
            lo, hi = BURSTINESS_UNIFORM_BAND
            all_in_band = all(lo <= w <= hi for w in wcs)
            if (stdev < BURSTINESS_MIN_STDEV and mean >= BURSTINESS_MIN_MEAN) or all_in_band:
                uniform.append((sec.start_line, len(wcs), mean, stdev, sec.heading[:50]))

        runs = []
        ordered = [s for sec in sections for s in sec.sentences]
        run: List[Sentence] = []
        for s in ordered:
            if s.word_count < MONOTONE_MIN_WORDS:
                if len(run) >= MONOTONE_RUN_LENGTH:
                    runs.append((run[0].line_num, run[-1].line_num, len(run)))
                run = []
                continue
            if run and abs(s.word_count - run[-1].word_count) <= MONOTONE_RUN_DELTA:
                run.append(s)
            else:
                if len(run) >= MONOTONE_RUN_LENGTH:
                    runs.append((run[0].line_num, run[-1].line_num, len(run)))
                run = [s]
        if len(run) >= MONOTONE_RUN_LENGTH:
            runs.append((run[0].line_num, run[-1].line_num, len(run)))
        return uniform, runs

    def scan_repeated_openers(self, sections: Sequence[Section]) -> List[Tuple[int, str, int, str]]:
        """Flag repeated first-two-word sentence openers."""
        findings = []
        doc_counts: Dict[str, int] = {}
        doc_lines: Dict[str, int] = {}
        for sec in sections:
            sec_counts: Dict[str, int] = {}
            sec_lines: Dict[str, int] = {}
            for s in sec.sentences:
                if s.word_count < OPENER_MIN_WORDS or not s.opener:
                    continue
                sec_counts[s.opener] = sec_counts.get(s.opener, 0) + 1
                sec_lines.setdefault(s.opener, s.line_num)
                doc_counts[s.opener] = doc_counts.get(s.opener, 0) + 1
                doc_lines.setdefault(s.opener, s.line_num)
            for opener, count in sec_counts.items():
                if count >= OPENER_SECTION_THRESHOLD:
                    findings.append((sec_lines[opener], opener, count, sec.heading[:50]))
        flagged = {f[1] for f in findings}
        for opener, count in doc_counts.items():
            if count >= OPENER_DOC_THRESHOLD and opener not in flagged:
                findings.append((doc_lines[opener], opener, count, "(document-wide)"))
        return findings

    def scan_trailing_participial(self, sections: Sequence[Section]) -> List[Tuple[int, str, str]]:
        """Flag trailing participial clauses."""
        findings = []
        for sec in sections:
            for s in sec.sentences:
                if s.word_count < TRAILING_PARTICIPIAL_MIN_WORDS:
                    continue
                word = None
                m = TRAILING_PARTICIPIAL_RE.search(s.text)
                if m:
                    word = m.group(1)
                else:
                    m = TRAILING_WITH_ABSOLUTE_RE.search(s.text)
                    if m:
                        word = m.group(1)
                if word and word.lower() not in PARTICIPIAL_EXEMPT:
                    findings.append((s.line_num, word, s.text.strip()[:80]))
        return findings

    def scan_rule_of_three(self, lines: Sequence[str]) -> List[Tuple[int, str]]:
        """Flag rule-of-three triads."""
        findings = []
        in_code = False
        for line_num, raw in enumerate(lines, 1):
            stripped = raw.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code or stripped.startswith("|"):
                continue
            if TRIAD_LINE_RE.match(stripped):
                findings.append((line_num, stripped[:60]))
                continue
            for m in TRIAD_TAIL_RE.finditer(raw):
                items = [m.group(1), m.group(2), m.group(3)]
                adj_like = sum(1 for w in items if _ADJ_SUFFIX_RE.search(w))
                if adj_like >= 2:
                    findings.append((line_num, m.group(0).strip()[:60]))
                    break
        return findings

    def scan_copula_avoidance(self, lines: Sequence[str]) -> List[Tuple[int, str, str]]:
        """Flag avoidance of direct copula verbs (such as 'serves as', 'boasts')."""
        findings = []
        for line_num, line in self._filter_code_lines(lines):
            for m in COPULA_AVOIDANCE_RE.finditer(line):
                if any(ex.search(line) for ex in COPULA_EXEMPTIONS):
                    continue
                findings.append((line_num, m.group(0), line.strip()[:80]))
        return findings

    def scan_sycophancy(self, lines: Sequence[str]) -> List[Tuple[int, str]]:
        """Flag sycophancy and performative conversational openers."""
        findings = []
        for line_num, line in self._filter_code_lines(lines):
            lower = line.lower()
            for phrase in SYCOPHANCY_PHRASES:
                if phrase in lower:
                    findings.append((line_num, phrase))
            if SYCOPHANCY_OPENER_RE.match(line):
                findings.append((line_num, line.strip()[:30] + " (performative opener)"))
        return findings

    def scan_flow_arrows(self, sections: Sequence[Section]) -> List[Tuple[int, str]]:
        """Flag flow arrow notation in narrative prose."""
        findings = []
        for sec in sections:
            for s in sec.sentences:
                text = INLINE_CODE_RE.sub(" ", s.text)
                if FLOW_ARROW_RE.search(text):
                    findings.append((s.line_num, s.text.strip()[:80]))
        return findings

    # -----------------------------------------------------------------------
    # Comprehensive Scan Runner
    # -----------------------------------------------------------------------

    def check(self, lines: Sequence[str], filepath: str = "") -> ScanResult:
        """Run all stylometric evaluations and return a ScanResult."""
        if self.has_opt_out(lines, filepath):
            return ScanResult(
                messages=[f"File opted out of prose quality scan: {filepath or '(buffer)'}"],
                findings=[],
                exit_code=0,
                is_exempt=True,
                profile_code=self.profile.code,
            )

        messages: List[str] = []
        findings_records: List[Finding] = []
        ext = os.path.splitext(filepath)[1].lower() if filepath else ".md"
        is_html = ext == ".html"

        def record(check_id: str, desc_msg: str, line_no: int | None = None, snippet: str = "") -> None:
            severity = "BLOCKING" if check_id in BLOCKING_CHECKS else "ADVISORY"
            findings_records.append(Finding(
                check_id=check_id,
                severity=severity,
                message=desc_msg,
                line_number=line_no,
                snippet=snippet,
            ))
            prefix = "[BLOCKING]" if severity == "BLOCKING" else "[ADVISORY]"
            messages.append(f"{prefix} {desc_msg}")

        # 1. Banned words
        banned = self.scan_banned_words(lines)
        if banned:
            word_list = ", ".join(f"'{w}' (L{n})" for n, w, _ in banned[:8])
            remaining = len(banned) - 8
            msg = f"AI-tell words: {word_list}"
            if remaining > 0:
                msg += f" (+{remaining} more)"
            record("banned_words", msg, banned[0][0], banned[0][2])

        # 2. Transition overuse
        transitions = self.scan_transitions(lines)
        if transitions:
            record(
                "transition_padding",
                f"Transition padding: {len(transitions)} instances of moreover/furthermore/additionally",
                transitions[0][0],
            )

        # 3. Non-ASCII characters
        non_ascii = self.scan_non_ascii(lines)
        if non_ascii:
            chars = ", ".join(f"{name} (L{n}, {repl})" for n, name, repl in non_ascii[:5])
            record("non_ascii", f"Non-ASCII characters: {chars}", non_ascii[0][0], non_ascii[0][2])

        # 4. -ize spellings
        ize = self.scan_ize_spellings(lines)
        if ize:
            words = ", ".join(f"'{w}' (L{n})" for n, w, _ in ize[:5])
            record("ize_spelling", f"{self.profile.name}: use -ise not -ize: {words}", ize[0][0], ize[0][2])

        # 5. Contractions
        contractions = self.scan_contractions(lines)
        if contractions:
            words = ", ".join(f"'{w}' (L{n})" for n, w, _ in contractions[:5])
            record("contractions", f"Contractions found (expand these): {words}", contractions[0][0], contractions[0][2])

        # 6. AI construction patterns
        constructions = self.scan_constructions(lines)
        if constructions:
            labels = ", ".join(f"{label} (L{n})" for n, label, _ in constructions[:4])
            remaining = len(constructions) - 4
            msg = f"AI construction patterns: {labels}"
            if remaining > 0:
                msg += f" (+{remaining} more)"
            record("construction_patterns", msg, constructions[0][0], constructions[0][2])

        # 7. Em-dash density per section
        dash_findings = self.scan_dash_density(lines, is_html)
        if dash_findings:
            details = ", ".join(
                f"section '{h}' (L{n}, {c} dashes)" for n, c, h in dash_findings[:3]
            )
            remaining = len(dash_findings) - 3
            msg = f"Em-dash density above {DASH_DENSITY_THRESHOLD} per section: {details}"
            if remaining > 0:
                msg += f" (+{remaining} more)"
            record("em_dash_density", msg, dash_findings[0][0])

        # H. Copula avoidance
        copula = self.scan_copula_avoidance(lines)
        if copula:
            details = ", ".join(f"'{w}' (L{n})" for n, w, _ in copula[:4])
            record("copula_avoidance", f"Copula avoidance (write plain 'is'): {details}", copula[0][0], copula[0][2])

        # I. Sycophancy phrases
        syco = self.scan_sycophancy(lines)
        if syco:
            details = ", ".join(f"'{p}' (L{n})" for n, p in syco[:4])
            record("sycophancy", f"Sycophancy/filler phrases: {details}", syco[0][0])

        # Prose rhythm checks
        sections = self.segment_sections(lines, is_html)

        serial = self.scan_serial_comma(sections)
        if serial:
            details = ", ".join(f"L{n}" for n, _ in serial[:6])
            record(
                "serial_comma",
                f"Serial (Oxford) comma ({self.profile.name} style bans comma before and/or in lists): "
                f"{len(serial)} instances ({details})",
                serial[0][0],
            )

        dense = self.scan_comma_density(sections)
        if dense:
            details = ", ".join(f"L{n} ({what})" for n, what, _ in dense[:4])
            remaining = len(dense) - 4
            msg = f"Comma-dense sentences (3+ commas -- split them): {details}"
            if remaining > 0:
                msg += f" (+{remaining} more)"
            record("comma_density", msg, dense[0][0], dense[0][2])

        long_sentences, heavy_sections = self.scan_sentence_length(sections)
        if long_sentences:
            details = ", ".join(f"L{n} ({wc}w)" for n, wc, _ in long_sentences[:5])
            remaining = len(long_sentences) - 5
            msg = f"Sentences over {SENT_MAX_WORDS} words (split them): {details}"
            if remaining > 0:
                msg += f" (+{remaining} more)"
            record("sentence_length", msg, long_sentences[0][0], long_sentences[0][2])
        if heavy_sections:
            details = ", ".join(f"'{h}' avg {m:.1f}w" for _, m, h in heavy_sections[:3])
            record(
                "section_length",
                f"Section average sentence length over {SECTION_AVG_MAX_WORDS:.0f} words: {details}",
                heavy_sections[0][0],
            )

        uniform, runs = self.scan_burstiness(sections)
        if uniform:
            details = ", ".join(
                f"'{h}' ({n} sentences, mean {m:.1f}w, stdev {sd:.1f})"
                for _, n, m, sd, h in uniform[:3]
            )
            record("burstiness", f"Uniform sentence rhythm (vary lengths deliberately): {details}", uniform[0][0])
        if runs:
            details = ", ".join(f"L{a}-L{b} ({k} sentences)" for a, b, k in runs[:3])
            record("monotone_runs", f"Monotone runs of similar-length sentences: {details}", runs[0][0])

        openers = self.scan_repeated_openers(sections)
        if openers:
            details = ", ".join(f"'{op}' x{c} in {h}" for _, op, c, h in openers[:3])
            record("repeated_openers", f"Repeated sentence openers: {details}", openers[0][0])

        participial = self.scan_trailing_participial(sections)
        if participial:
            details = ", ".join(f"', {w}...' (L{n})" for n, w, _ in participial[:4])
            remaining = len(participial) - 4
            msg = f"Trailing participial clauses -- split into own sentence (3.5n): {details}"
            if remaining > 0:
                msg += f" (+{remaining} more)"
            record("trailing_participial", msg, participial[0][0], participial[0][2])

        triads = self.scan_rule_of_three(lines)
        if triads:
            details = ", ".join(f"L{n} '{s}'" for n, s in triads[:3])
            record("rule_of_three", f"Rule-of-three triads (3.5i): {details}", triads[0][0], triads[0][1])

        flow = self.scan_flow_arrows(sections)
        if flow:
            details = ", ".join(f"L{n}" for n, _ in flow[:6])
            remaining = len(flow) - 6
            msg = (
                "Process/flow arrow notation '->' (write the relation in prose -- "
                f"'then', 'feeds', 'maps to', or use a numbered list/diagram): {len(flow)} instances ({details})"
            )
            if remaining > 0:
                msg += f" (+{remaining} more)"
            record("flow_arrows", msg, flow[0][0], flow[0][1])

        # Severity resolution
        blocking_count = sum(1 for r in findings_records if r.severity == "BLOCKING")
        advisory_count = sum(1 for r in findings_records if r.severity == "ADVISORY")

        if self.strict:
            exit_code = 1 if (blocking_count > 0 or advisory_count > 0) else 0
        else:
            if blocking_count > 0:
                exit_code = 1
            elif advisory_count >= self.advisory_threshold:
                exit_code = 2
            else:
                exit_code = 0

        return ScanResult(
            messages=messages,
            findings=findings_records,
            exit_code=exit_code,
            is_exempt=False,
            profile_code=self.profile.code,
        )

    def check_text(self, text: str, filename: str = "document.md") -> ScanResult:
        """Scan a raw string containing document text."""
        lines = text.splitlines()
        return self.check(lines, filepath=filename)
