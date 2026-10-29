"""Repository paths used by the benchmark."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OWID_ROOT = REPO_ROOT / "OWID"
DATABASE = REPO_ROOT / "data" / "sqlite" / "vdem2026.db"
DATASET_ROOT = Path(__file__).resolve().parents[1] / "dataset"
OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "output"
GOLDEN_FOLDER = "golden-processing-program-files"
