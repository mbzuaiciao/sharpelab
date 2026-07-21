"""Provenance Agent and deterministic support validation."""

import re

from sharpelab.agents.prompts import role_messages
from sharpelab.agents.provider import TypedProvider
from sharpelab.agents.schemas import AgentRole, ProvenanceOutput
from sharpelab.diagnostics.provenance import ProvenanceCompleteness

PROVENANCE_FIELDS = (
    "trials",
    "parameter_searches",
    "markets_or_universes",
    "start_dates_or_windows",
    "failed_trials_retained",
    "trial_dependence_known",
)
HEDGE_PATTERN = re.compile(
    r"\b(?:about|approximately|around|roughly|maybe|perhaps|nearly|"
    r"at\s+least|at\s+most|more\s+than|less\s+than|over|under|up\s+to)\s*$",
    re.IGNORECASE,
)
COUNT_PATTERNS = {
    "trials": re.compile(r"\b(?P<count>\d+)\s+(?:strategies|trials)\b", re.I),
    "parameter_searches": re.compile(
        r"\b(?P<count>\d+)\s+(?:parameter\s+searches|searches)\b", re.I
    ),
}
BOOLEAN_PATTERNS = {
    "failed_trials_retained": {
        True: re.compile(
            r"(?:retained|kept|recorded)\s+(?:all\s+)?(?:failed|unsuccessful)\s+"
            r"(?:trials|strategies)|(?:failed|unsuccessful)\s+(?:trials|strategies)"
            r"\s+(?:were\s+)?(?:retained|kept|recorded)",
            re.I,
        ),
        False: re.compile(
            r"(?:did\s+not|didn't)\s+(?:retain|keep|record)\s+(?:failed|"
            r"unsuccessful)\s+(?:trials|strategies)|(?:failed|unsuccessful)\s+"
            r"(?:trials|strategies)\s+(?:were\s+)?not\s+(?:retained|kept|"
            r"recorded)|(?:discarded|dropped)\s+(?:failed|unsuccessful)\s+"
            r"(?:trials|strategies)",
            re.I,
        ),
    },
    "trial_dependence_known": {
        True: re.compile(
            r"(?:trial|strategy)\s+dependence\s+(?:is|was)\s+known|"
            r"(?:trials|strategies)\s+(?:were|are)\s+(?:dependent|independent)",
            re.I,
        ),
        False: re.compile(
            r"(?:trial|strategy)\s+dependence\s+(?:is|was)\s+(?:unknown|not\s+known)|"
            r"(?:do\s+not|don't|did\s+not|didn't)\s+know\s+(?:whether\s+)?"
            r"(?:trials|strategies).*(?:dependent|independent)",
            re.I,
        ),
    },
}


def extract_unambiguous_count(prose: str, field_name: str) -> tuple[int, str] | None:
    """Return one literal unhedged count, rejecting ranges and conflicts."""
    pattern = COUNT_PATTERNS[field_name]
    supported: list[tuple[int, str]] = []
    for match in pattern.finditer(prose):
        prefix = prose[max(0, match.start() - 24) : match.start()]
        count_start = match.start("count")
        range_prefix = prose[max(0, count_start - 8) : count_start]
        if HEDGE_PATTERN.search(prefix):
            continue
        if re.search(r"(?:\d\s*(?:-|–|—|to)\s*)$", range_prefix, re.I):
            continue
        supported.append((int(match.group("count")), match.group(0)))
    if not supported or len({value for value, _ in supported}) != 1:
        return None
    return supported[0]


class ProvenanceAgent:
    def __init__(self, provider: TypedProvider) -> None:
        self.provider = provider

    def run(self, prose: str) -> ProvenanceOutput:
        return self.provider.generate_typed(
            role=AgentRole.PROVENANCE,
            messages=role_messages(
                AgentRole.PROVENANCE, prose or "No provenance supplied."
            ),
            output_schema=ProvenanceOutput,
        )


def validate_provenance_support(prose: str, output: ProvenanceOutput) -> None:
    """Reject fields, counts, or excerpts not deterministically supported."""
    support_by_field: dict[str, list[str]] = {field: [] for field in PROVENANCE_FIELDS}
    for support in output.source_support:
        if support.exact_excerpt not in prose:
            raise ValueError(
                "provenance support excerpt is absent from source: "
                f"{support.field_name}"
            )
        support_by_field[support.field_name].append(support.exact_excerpt)
    provenance = output.proposed_provenance
    numeric_fields = {
        "trials": provenance.trials,
        "parameter_searches": provenance.parameter_searches,
    }
    for field_name, value in numeric_fields.items():
        if value is None:
            continue
        extracted = extract_unambiguous_count(prose, field_name)
        excerpts = support_by_field[field_name]
        if (
            extracted is None
            or extracted[0] != value
            or not any(extracted[1] in excerpt for excerpt in excerpts)
        ):
            raise ValueError(f"unsupported provenance number: {field_name}")

    tuple_fields = {
        "markets_or_universes": provenance.markets_or_universes,
        "start_dates_or_windows": provenance.start_dates_or_windows,
    }
    for field_name, values in tuple_fields.items():
        excerpts = support_by_field[field_name]
        if any(not any(value in excerpt for excerpt in excerpts) for value in values):
            raise ValueError(f"unsupported provenance field: {field_name}")

    boolean_fields = {
        "failed_trials_retained": provenance.failed_trials_retained,
        "trial_dependence_known": provenance.trial_dependence_known,
    }
    for field_name, value in boolean_fields.items():
        if value is None:
            continue
        excerpts = support_by_field[field_name]
        matching_values = {
            candidate
            for candidate, pattern in BOOLEAN_PATTERNS[field_name].items()
            if any(pattern.search(excerpt) for excerpt in excerpts)
        }
        if matching_values != {value}:
            raise ValueError(f"unsupported provenance field: {field_name}")

    missing_fields = {
        "trials" if provenance.trials is None else "",
        "parameter_searches" if provenance.parameter_searches is None else "",
        "markets_or_universes" if not provenance.markets_or_universes else "",
        "start_dates_or_windows" if not provenance.start_dates_or_windows else "",
        "failed_trials_retained" if provenance.failed_trials_retained is None else "",
        "trial_dependence_known" if provenance.trial_dependence_known is None else "",
    } - {""}
    if set(output.unresolved_fields) != missing_fields:
        raise ValueError("unresolved provenance fields must match unsupported fields")
    expected_completeness = (
        ProvenanceCompleteness.MISSING
        if len(missing_fields) == len(PROVENANCE_FIELDS)
        else ProvenanceCompleteness.COMPLETE
        if not missing_fields
        else ProvenanceCompleteness.PARTIAL
    )
    if provenance.completeness is not expected_completeness:
        raise ValueError("provenance completeness is overstated or inconsistent")
