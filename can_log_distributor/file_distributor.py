from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TextIO

@dataclass(frozen=True)
class RouteSpec:
    dest: str

@dataclass(frozen=True)
class RouteEvent:
    route: RouteSpec

    @staticmethod
    def route_to(route_dest: str) -> "RouteEvent":
        return RouteEvent(route=RouteSpec(dest=route_dest))

@dataclass(frozen=True)
class FileDistributeConfig:
    input_file: Path
    output_dir: Path
    header_lines: Optional[tuple[str, ...]] = None
    encoding: str = "utf-8"

@dataclass
class RouteMeta:
    name: str
    file_path: Path

class DistributeEngine:
    def __init__(
        self,
        input_file: Path,
        output_dir: Path,
        header_lines: Optional[tuple[str, ...]] = None,
        encoding: str = "utf-8"
    ) -> None:
        self.input_stem = Path(input_file).stem
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.encoding = encoding
        self.header_lines = header_lines

        self._fps : dict[str, TextIO] = {}
        self._routes : dict[str, RouteMeta] = {}
    
    def _open_new_fp(self, route: RouteSpec):
        key = route.dest
        path = self.output_dir / f"{key}" / f"{self.input_stem}.asc"
        path.parent.mkdir(parents=True, exist_ok=True)

        new_fp = path.open("w", encoding=self.encoding, newline="")
        if self.header_lines is not None:
            for line in self.header_lines:
                new_fp.write(line)
        
        self._fps[key] = new_fp
        self._routes[key] = RouteMeta(
            name=key,
            file_path=path
        )

        return new_fp

    def _get_fp(self, route: RouteSpec):
        key = route.dest
        if key in self._fps:
            return self._fps[key]
        
        return self._open_new_fp(route)
    
    def get_routes(self) -> list[RouteMeta]:
        return list(self._routes.values())
    
    def run(self, line: str, event: RouteEvent) -> None:
        route = event.route
        fp = self._get_fp(route)
        fp.write(line)
    
    def close(self) -> None:
        for fp in self._fps.values():
            fp.close()
        self._fps.clear()

class RouteResolver(ABC):
    @abstractmethod
    def check_line(self, line: str) -> Optional[RouteEvent]:
        raise NotImplementedError()

class FileDistributor:
    def __init__(self, resolver: RouteResolver, config: FileDistributeConfig) -> None:
        self.resolver = resolver
        self.config = config
    
    def distribute_file(self) -> list[RouteMeta]:
        file_path = Path(self.config.input_file)
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        if not file_path.is_file():
            raise ValueError(f"Input path is not a file: {file_path}")
        
        engine = DistributeEngine(
            input_file=file_path,
            output_dir=self.config.output_dir,
            header_lines=self.config.header_lines,
            encoding=self.config.encoding
        )
        try:
            with file_path.open("r", encoding=self.config.encoding) as f:
                for line in f:
                    event = self.resolver.check_line(line)
                    if event:
                        engine.run(line, event)
        finally:
            engine.close()
        return engine.get_routes()