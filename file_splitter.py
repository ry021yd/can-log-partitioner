from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

class HeaderTarget(Enum):
    ALL = 1
    EXCLUDE_FIRST = 2

@dataclass(frozen=True)
class SegmentSpec:
    name: str

@dataclass(frozen=True)
class SegmentEvent:
    next_segment: SegmentSpec

    @staticmethod
    def split_to(segment_name: str) -> "SegmentEvent":
        return SegmentEvent(next_segment=SegmentSpec(name=segment_name))

@dataclass(frozen=True)
class FileSplitConfig:
    input_file: Path
    output_dir: Path
    header_lines: Optional[tuple[str, ...]] = None
    header_target: HeaderTarget = HeaderTarget.EXCLUDE_FIRST
    initial_segment_name: str = "initial"
    encoding: str = "utf-8"

@dataclass
class SegmentMeta:
    index: int
    name: str
    file_path: Path

class SplitEngine:
    def __init__(
        self,
        input_file: Path,
        output_dir: Path,
        header_lines: Optional[tuple[str, ...]] = None,
        header_target: HeaderTarget = HeaderTarget.EXCLUDE_FIRST,
        initial_segment_name: str = "initial",
        encoding: str = "utf-8"
    ) -> None:
        self.input_stem = Path(input_file).stem
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.encoding = encoding
        self.header_lines = header_lines
        self.header_target = header_target

        self._segment_index = 0
        self._current_segment = SegmentSpec(name=initial_segment_name)
        self._current_meta: Optional[SegmentMeta] = None
        self._current_fp = None
        self._segments: list[SegmentMeta] = []
        self._open_new_segment(self._current_segment)
    
    def _open_new_segment(self, segment: SegmentSpec) -> None:
        self._segment_index += 1
        path = self.output_dir / f"{self._segment_index:04d}_{segment.name}_{self.input_stem}.asc"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._current_fp = path.open("w", encoding=self.encoding, newline="")

        if self.header_lines is not None:
            if self.header_target == HeaderTarget.EXCLUDE_FIRST and self._segment_index == 1:
                pass
            else:
                for line in self.header_lines:
                    self._current_fp.write(line)

        self._current_segment = segment
        self._current_meta = SegmentMeta(
            index=self._segment_index,
            name=segment.name,
            file_path=path
        )
        self._segments.append(self._current_meta)
    
    def _close_current_segment(self) -> None:
        if self._current_fp is not None:
            self._current_fp.close()
            self._current_fp = None
    
    def get_segments(self) -> list[SegmentMeta]:
        return list(self._segments)
    
    def write_line(self, line: str) -> None:
        if self._current_fp is None:
            raise RuntimeError("No open segment to write to")
        self._current_fp.write(line)
    
    def run(self, line: str, event: Optional[SegmentEvent]) -> None:
        if event is None:
            self.write_line(line)
            return

        self._close_current_segment()
        self._open_new_segment(
            event.next_segment
        )
        self.write_line(line)
        return

    def close(self) -> None:
        self._close_current_segment()

class SplitChecker(ABC):
    @abstractmethod
    def check_line(self, line: str) -> Optional[SegmentEvent]:
        raise NotImplementedError()
    
class FileSplitter:
    def __init__(self, checker: SplitChecker, config: FileSplitConfig) -> None:
        self.checker = checker
        self.config = config  

    def split_file(self) -> list[SegmentMeta]:
        file_path = Path(self.config.input_file)
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        if not file_path.is_file():
            raise ValueError(f"Input path is not a file: {file_path}")
        
        engine = SplitEngine(
            input_file=file_path,
            output_dir=self.config.output_dir,
            header_lines=self.config.header_lines,
            header_target=self.config.header_target,
            initial_segment_name=self.config.initial_segment_name,
            encoding=self.config.encoding
        )
        try:
            with file_path.open("r", encoding=self.config.encoding) as f:
                for line in f:
                    event = self.checker.check_line(line)
                    engine.run(line, event)
        finally:
            engine.close()
        return engine.get_segments()