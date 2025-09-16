import csv
from pathlib import Path

def load_info_alumnos():
    path = Path(__file__).resolve().parents[1] / "resources" / "data" / "infoAlumnos.csv"
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
