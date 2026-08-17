from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Pokemon:
    name: str
    id: Optional[int]
    hidden_img_path: Path
    revealed_img_path: Path
    original_img_path: Optional[Path]
