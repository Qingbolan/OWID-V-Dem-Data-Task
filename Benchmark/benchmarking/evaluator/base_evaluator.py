"""Common interface of all evaluators (mirrors GemBench's BaseEvaluator)."""
from abc import ABC, abstractmethod
from pathlib import Path

from ..utils.struct import Task


class BaseEvaluator(ABC):
    """Scores one executed case directory against its task and writes nothing outside that directory."""

    name: str = "base"

    @abstractmethod
    def evaluate(self, task: Task, case_dir: Path) -> dict:
        """Return a JSON-serialisable result for the case."""
