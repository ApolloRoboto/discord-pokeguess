from dataclasses import dataclass
from pathlib import Path


@dataclass
class Pokemon:
    name: str
    id: int | None
    hidden_img_path: Path
    revealed_img_path: Path
    original_img_path: Path | None
