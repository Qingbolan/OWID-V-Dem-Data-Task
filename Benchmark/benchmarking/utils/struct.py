"""Data structures exchanged between datasets, solutions, the processor and evaluators."""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class InputLevel(str, Enum):
    """How much natural-language input a solution receives (see docs/task-definition.md)."""

    TITLE = "title"
    SUBTITLE = "subtitle"
    ARTICLE = "article"
    IMAGE = "image"
    IMAGE_ARTICLE = "image-article"


@dataclass(frozen=True)
class Task:
    """One reproducible figure of one OWID report."""

    task_id: str
    dataset: str
    article_folder: Path
    figure_name: str
    category: str
    title: str
    subtitle: str
    article_text: str
    output_columns: list[str]
    gold_csv: Path
    spec_path: Path
    database: Path
    variant: str | None = None  # golden-program variant of the dataset (e.g. "raw"); None for the full database
    image: str | None = None  # the figure image with its data values covered, relative to the repository root
    supplement: str = ""  # output columns and their precision, appended to every level (docs/task-definition.md)

    def supports(self, level: InputLevel) -> bool:
        """Article levels need a page that shows the chart; image levels need a redacted image."""
        if level in (InputLevel.ARTICLE, InputLevel.IMAGE_ARTICLE) and not self.article_text:
            return False
        return bool(self.image) or level not in (InputLevel.IMAGE, InputLevel.IMAGE_ARTICLE)

    def payload(self, level: InputLevel) -> dict:
        """The exact input a solution receives: one natural-language query, never gold data; the supplement (the
        output columns and their precision) is appended at every level.

        title     the chart title
        subtitle  the chart title and subtitle
        article   the title, the subtitle and the report's full text (figures replaced by [Figure n]; the requested
                  one is marked), without the chart's own notes, units or source
        image     the title, and the figure image with its printed data values covered
        image-article  the article level, and the same image
        """
        query = self.title
        if level in (InputLevel.SUBTITLE, InputLevel.ARTICLE, InputLevel.IMAGE_ARTICLE) and self.subtitle:
            query += "\n" + self.subtitle
        if level in (InputLevel.ARTICLE, InputLevel.IMAGE_ARTICLE):
            if not self.article_text:
                raise ValueError(f"{self.task_id} has no page that shows the chart")
            query += "\n\nThe chart appears in this report:\n\n" + self.article_text
        if level in (InputLevel.IMAGE, InputLevel.IMAGE_ARTICLE):
            if not self.image:
                raise ValueError(f"{self.task_id} has no redacted image")
            return {"query": query + "\n\nThe chart is attached as an image (its printed data values are covered)."
                    + self._supplement(), "image": self.image}
        return {"query": query + self._supplement()}

    def _supplement(self) -> str:
        return f"\n\nSupplementary material:\n{self.supplement}" if self.supplement else ""


@dataclass
class SolutionOutput:
    """What a solution returns for one case."""

    final_sql: str | None
    answer_text: str
    tool_calls: int = 0
    usage: dict | None = None
    model: str | None = None
    error: str | None = None


@dataclass
class CaseRecord:
    """Where one executed case lives and how it ended."""

    task_id: str
    solution: str
    level: InputLevel
    repeat: int
    directory: Path
    state: str
    metadata: dict = field(default_factory=dict)
