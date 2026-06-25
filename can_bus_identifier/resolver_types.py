from collections import Counter
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class BusResolveState:
    bus_number: str
    candidates: set[str] | None = None
    matched_ids: set[int] = field(default_factory=set)
    ignored_ids: set[int] = field(default_factory=set)
    unknown_ids: set[int] = field(default_factory=set)
    observed_id_counts: Counter[int] = field(default_factory=Counter)

    def record_observed(self, can_id: int) -> None:
        self.observed_id_counts[can_id] += 1

    def observe(self, can_id: int, labels: set[str]) -> None:
        if self.candidates is None:
            self.candidates = set(labels)
        else:
            self.candidates &= labels

        self.matched_ids.add(can_id)

    def ignore(self, can_id: int) -> None:
        self.ignored_ids.add(can_id)

    def unknown(self, can_id: int) -> None:
        self.unknown_ids.add(can_id)


class ResolveResult(Enum):
    RESOLVED = "resolved"
    MULTIPLE_CANDIDATES = "multiple candidates"
    NO_CANDIDATES = "no candidates"
    NO_VALID_ID_FOUND = "no valid id found"
    RESOLVED_WITH_CONTAMINATION = "resolved_with_contamination"


class ResolveMode(Enum):
    SCORE = "score"
    STRICT = "strict"
    STRICT_UNIQUE = "strict-unique"
