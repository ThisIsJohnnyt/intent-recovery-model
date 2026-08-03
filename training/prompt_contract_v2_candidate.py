"""Candidate vNext prompt contract -- typed item markers (###BULLET###/
###ACTION###), replacing bare-newline item boundaries.

NOT the live contract. PROMPT_CONTRACT_VERSION here is deliberately suffixed
"-candidate". Never imported by prepare_data.py or train.py at all. As of
contract_adapters.py's adapter refactor, run_benchmark.py/report_benchmark.py
import this module only lazily, inside select_contract_adapter("v2") --
selecting the default/v1 contract never imports it (confirmed by a fresh-
subprocess test in test_run_benchmark_contract_adapters.py). This module
exists only for the static, no-GPU feasibility package requested in
training/prompt_contract_vnext_joint_alignment_review.md. Do not wire this
into the live training/generation pipeline until Johnny approves promoting
a candidate past the feasibility stage.

Recommended shape, per ChatGPT's vNext decision proposal and the joint
alignment review's Disagreement 1 (typed markers over dash-prefix -- see
that review for why: after newline collapse, "- " has no surviving
start-of-line privilege and collides with naturally-occurring dashes in
real notes, confirmed empirically against this project's own gold corpus,
where raw inputs contain four unrelated "- " occurrences and zero "###"
occurrences):

    ###NARRATIVE###
    coherent narrative
    ###BULLETS###
    ###BULLET### first supported idea
    ###BULLET### second supported idea
    ###ACTIONS###
    ###ACTION### first explicit task
"""

PROMPT_CONTRACT_VERSION = "source-determined-items-v2-candidate"

NARRATIVE_MARKER = "###NARRATIVE###"
BULLETS_MARKER = "###BULLETS###"
BULLET_ITEM_MARKER = "###BULLET###"
ACTIONS_MARKER = "###ACTIONS###"
ACTION_ITEM_MARKER = "###ACTION###"

ALL_MARKERS = (
    NARRATIVE_MARKER,
    BULLETS_MARKER,
    BULLET_ITEM_MARKER,
    ACTIONS_MARKER,
    ACTION_ITEM_MARKER,
)

SYSTEM_PROMPT = (
    "You are a compassionate AI assistant helping someone organize scattered, "
    "fragmented thoughts written under real-world conditions like time "
    "pressure, interruption, or fatigue.\n\n"
    "The user has provided messy, non-linear thoughts below. Your job is to "
    "transform them into three clear, organized views that reduce anxiety "
    "and improve clarity."
)

USER_PROMPT_TEMPLATE = (
    "Respond using exactly these section and item markers, with no other "
    "text before or after the structured response. Newlines may be used "
    "for readability, but marker strings define the structure, not line "
    "breaks:\n\n"
    f"{NARRATIVE_MARKER} "
    "a coherent, flowing narrative that groups related ideas, keeps the "
    "original meaning and tone, and reads less anxiety-inducing than the "
    f"raw thoughts\n{BULLETS_MARKER}\n"
    f"Prefix each source-supported key idea with {BULLET_ITEM_MARKER}, up "
    "to seven. Use fewer when the source supports fewer ideas. Never add, "
    "split, or repeat content to reach a target count.\n"
    f"{ACTIONS_MARKER}\n"
    f"Prefix each explicit supported task with {ACTION_ITEM_MARKER}. If "
    f"the source contains no tasks, emit no {ACTION_ITEM_MARKER} markers."
)


def build_prompt(raw_input: str) -> str:
    sanitized = sanitize_marker_like_text(raw_input)
    return f"{SYSTEM_PROMPT}\n\nUSER'S RAW THOUGHTS:\n{sanitized}\n\n{USER_PROMPT_TEMPLATE}"


def sanitize_marker_like_text(text: str) -> str:
    """Gate 5/7 fix: defang any run of 3+ literal '#' characters in raw
    input before it ever reaches the model, so a note that happens to
    contain marker-like text (e.g. a user pasting example prompt syntax)
    can never be echoed back in a way that's byte-identical to a real
    structural marker. Inserts a zero-width non-joiner (U+200C) every 2
    characters throughout the run -- renders visually indistinguishable in
    virtually every font/context, but guarantees no 3-consecutive-'#'
    substring survives anywhere in the sanitized text, so exact-match
    parsing can never mistake it for a real marker. A single insertion
    point at the start of the run is NOT sufficient -- a long run (e.g. 7+
    '#') still contains a matchable 3+ substring after its first two
    characters; every-2-characters insertion closes that gap. General (any
    3+ '#' run), not hardcoded to the five known marker strings -- future
    marker additions are covered automatically.
    """
    import re

    def defang(match: "re.Match[str]") -> str:
        run = match.group(0)
        return "‌".join(run[i : i + 2] for i in range(0, len(run), 2))

    return re.sub(r"#{3,}", defang, text)
