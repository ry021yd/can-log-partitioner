from pathlib import Path

from .asc_frame import parse_asc_frame
from .config import IdentifierConfig
from .id2bus_map import Id2BusMap
from .resolver_types import BusResolveState, ResolveMode, ResolveResult
from .score_resolver import format_score_output
from .utils import int_canid_to_hex


def format_output(states: dict[str, BusResolveState], verbosity: int) -> list[dict]:
    results: list[dict] = []
    for bus_number in sorted(states.keys(), key=lambda x: int(x)):
        state = states[bus_number]

        labels = []
        if state.candidates is None:
            result = ResolveResult.NO_VALID_ID_FOUND
        else:
            labels = sorted(state.candidates)
            label_count = len(labels)
            if label_count == 1:
                result = ResolveResult.RESOLVED
            elif label_count == 0:
                result = ResolveResult.NO_CANDIDATES
            else:
                result = ResolveResult.MULTIPLE_CANDIDATES

        result_item = {
            "bus_number": bus_number,
            "result": result.value,
            "labels": labels,
        }

        if verbosity >= 1:
            result_item["matched_ids"] = [int_canid_to_hex(id) for id in sorted(state.matched_ids)]
            result_item["ignored_ids"] = [int_canid_to_hex(id) for id in sorted(state.ignored_ids)]
            result_item["unknown_ids"] = [int_canid_to_hex(id) for id in sorted(state.unknown_ids)]

        results.append(result_item)

    return results


def apply_unique_label_resolution(states: dict[str, BusResolveState]) -> None:
    changed = True
    while changed:
        changed = False
        resolved_labels = {
            sorted(state.candidates)[0]
            for state in states.values()
            if state.candidates and len(state.candidates) == 1
        }

        for state in states.values():
            if state.candidates is None or len(state.candidates) <= 1:
                continue

            before = set(state.candidates)
            after = before - resolved_labels

            if before != after:
                state.candidates = after
                changed = True


def resolve_bus_labels(
    input_asc: str,
    id2bus_json: str,
    config_json: str | None,
    mode: str | ResolveMode,
    max_frames: int,
    verbosity: int,
    ignore_unknown_ids: bool,
) -> list[dict]:
    resolve_mode = ResolveMode(mode)
    id2bus = Id2BusMap.load_json(id2bus_json)
    ignore_config = IdentifierConfig.load_json(config_json)

    states: dict[str, BusResolveState] = {}

    with Path(input_asc).open("r", encoding="utf-8") as fp:
        parsed_line_cnt = 0
        for line in fp:
            frame = parse_asc_frame(line)
            if frame is None:
                continue

            parsed_line_cnt += 1

            if parsed_line_cnt > max_frames:
                break

            if frame.bus_number not in states:
                states[frame.bus_number] = BusResolveState(
                    bus_number=frame.bus_number
                )
            state = states[frame.bus_number]

            can_id = frame.can_id
            if ignore_config.match_ignore_rules(can_id):
                state.ignore(can_id)
                continue

            state.record_observed(can_id)
            mapped_labels = id2bus.get_labels(frame.can_id)
            if mapped_labels is None:
                state.unknown(can_id)
                if resolve_mode == ResolveMode.SCORE or ignore_unknown_ids:
                    continue
                else:
                    mapped_labels = set()

            state.observe(can_id, mapped_labels)

    if resolve_mode == ResolveMode.SCORE:
        return format_score_output(states, id2bus, verbosity)

    if resolve_mode == ResolveMode.STRICT_UNIQUE:
        apply_unique_label_resolution(states)

    results: list[dict] = format_output(states, verbosity)
    return results
