from collections import defaultdict
from dataclasses import dataclass

from .id2bus_map import Id2BusMap
from .resolver_types import BusResolveState, ResolveResult
from .utils import int_canid_to_hex

UNIQUE_ID_SCORE = 10
SHARED_ID_SCORE = 2
FOREIGN_ID_PENALTY = 1


@dataclass
class ScoreDetails:
    scores: dict[str, int]
    unique_hit_ids: dict[str, set[int]]
    shared_hit_ids: dict[str, set[int]]
    foreign_ids: dict[str, set[int]]


def calculate_score_details(state: BusResolveState, id2bus: Id2BusMap) -> ScoreDetails:
    scores: dict[str, int] = defaultdict(int)
    unique_hit_ids: dict[str, set[int]] = defaultdict(set)
    shared_hit_ids: dict[str, set[int]] = defaultdict(set)
    labels_by_id: dict[int, set[str]] = {}

    for can_id in sorted(state.observed_id_counts.keys()):
        labels = id2bus.get_labels(can_id)
        if not labels:
            continue

        labels_by_id[can_id] = labels
        if len(labels) == 1:
            label = next(iter(labels))
            scores[label] += UNIQUE_ID_SCORE
            unique_hit_ids[label].add(can_id)
            continue

        score = SHARED_ID_SCORE
        for label in labels:
            scores[label] += score
            shared_hit_ids[label].add(can_id)

    foreign_ids: dict[str, set[int]] = defaultdict(set)
    for label in list(scores.keys()):
        for can_id, labels in labels_by_id.items():
            if label in labels:
                continue

            scores[label] -= FOREIGN_ID_PENALTY
            foreign_ids[label].add(can_id)

    return ScoreDetails(
        scores=dict(scores),
        unique_hit_ids={label: set(ids) for label, ids in unique_hit_ids.items()},
        shared_hit_ids={label: set(ids) for label, ids in shared_hit_ids.items()},
        foreign_ids={label: set(ids) for label, ids in foreign_ids.items()},
    )


def sort_score_items(scores: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def format_id_list(ids: set[int]) -> list[str]:
    return [int_canid_to_hex(can_id) for can_id in sorted(ids)]


def format_id_map(items: dict[str, set[int]]) -> dict[str, list[str]]:
    return {
        label: format_id_list(ids)
        for label, ids in sorted(items.items())
        if ids
    }


def resolve_score_result(details: ScoreDetails) -> tuple[ResolveResult, list[str]]:
    ranked_scores = sort_score_items(details.scores)
    if not ranked_scores:
        return ResolveResult.NO_VALID_ID_FOUND, []

    top_label, top_score = ranked_scores[0]
    second_score = ranked_scores[1][1] if len(ranked_scores) > 1 else None
    has_score_margin = second_score is None or top_score > second_score

    if has_score_margin:
        if details.foreign_ids.get(top_label):
            return ResolveResult.RESOLVED_WITH_CONTAMINATION, [top_label]
        return ResolveResult.RESOLVED, [top_label]

    ambiguous_labels = [
        label
        for label, score in ranked_scores
        if top_score == score
    ]
    if len(ambiguous_labels) == 1 and len(ranked_scores) > 1:
        ambiguous_labels.append(ranked_scores[1][0])

    return ResolveResult.MULTIPLE_CANDIDATES, sorted(ambiguous_labels)


def format_score_output(
    states: dict[str, BusResolveState],
    id2bus: Id2BusMap,
    verbosity: int,
) -> list[dict]:
    results: list[dict] = []
    for bus_number in sorted(states.keys(), key=lambda x: int(x)):
        state = states[bus_number]
        details = calculate_score_details(state, id2bus)
        result, labels = resolve_score_result(details)

        result_item = {
            "bus_number": bus_number,
            "result": result.value,
            "labels": labels,
        }

        if verbosity >= 1:
            result_item["matched_ids"] = format_id_list(state.matched_ids)
            result_item["ignored_ids"] = format_id_list(state.ignored_ids)
            result_item["unknown_ids"] = format_id_list(state.unknown_ids)
            result_item["scores"] = {
                label: details.scores[label]
                for label, _score in sort_score_items(details.scores)
            }
            result_item["unique_hit_ids"] = format_id_map(details.unique_hit_ids)
            result_item["shared_hit_ids"] = format_id_map(details.shared_hit_ids)
            result_item["foreign_ids"] = format_id_map(details.foreign_ids)

        results.append(result_item)

    return results
