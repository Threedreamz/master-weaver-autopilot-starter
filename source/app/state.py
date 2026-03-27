from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict

Point = Tuple[int, int]
Line = Tuple[Point, Point]

@dataclass
class RecordState:
    min_t: Optional[int] = None
    line_t: Optional[Line] = None
    min_b: Optional[int] = None
    line_b: Optional[Line] = None
    min_l: Optional[int] = None
    line_l: Optional[Line] = None
    min_r: Optional[int] = None
    line_r: Optional[Line] = None

    def reset(self) -> None:
        self.min_t = self.line_t = None
        self.min_b = self.line_b = None
        self.min_l = self.line_l = None
        self.min_r = self.line_r = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "min_t": self.min_t, "line_t": self.line_t,
            "min_b": self.min_b, "line_b": self.line_b,
            "min_l": self.min_l, "line_l": self.line_l,
            "min_r": self.min_r, "line_r": self.line_r,
        }