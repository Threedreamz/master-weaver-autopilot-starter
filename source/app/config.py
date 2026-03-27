from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import argparse

@dataclass(frozen=True)
class AppConfig:
    window_title: str = "X-Ray Edge Stream (q/ESC)"
    region: Tuple[int, int, int, int] = (560, 40, 800, 990)  # x, y, w, h
    monitor_index: int = 1
    fps: float = 20.0

def parse_args() -> AppConfig:
    parser = argparse.ArgumentParser(description="X-Ray Edge Stream")
    parser.add_argument("--test", action="store_true", help="Enable test offset for region cropping")
    parser.add_argument("--monitor", type=int, default=1, help="Monitor index for capture (default: 1)")
    parser.add_argument("--fps", type=float, default=20.0, help="Target frames per second (default: 20)")
    parser.add_argument("--region", type=int, nargs=4, metavar=('X','Y','W','H'),
                        help="Override capture region as four integers: X Y W H")
    args = parser.parse_args()

    extra = 40 if args.test else 0
    # Original logic: y += 2*extra, h -= extra*3
    default_region = (560, 40 + 2*extra, 800, 990 - extra*3)

    region = tuple(args.region) if args.region else default_region
    return AppConfig(
        region=region,
        monitor_index=args.monitor,
        fps=args.fps,
    )