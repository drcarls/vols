#!/usr/bin/env python
"""Run the sensitivity and ablation analysis against a completed run.

Answers the question the system can currently ask about itself: which of its
conclusions survive being wrong about the priors?

Usage:
    python scripts/sensitivity.py                  # latest run
    python scripts/sensitivity.py --run-id 3
    python scripts/sensitivity.py --json > sensitivity.json
    python scripts/sensitivity.py --no-ablations   # sweeps only, faster
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.analysis.sensitivity import analyse, render_text   # noqa: E402
from app.db.base import session_scope                       # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-id", type=int, default=None)
    parser.add_argument("--json", action="store_true",
                        help="emit the full report as JSON instead of text")
    parser.add_argument("--no-ablations", action="store_true")
    args = parser.parse_args()

    with session_scope() as session:
        report = analyse(session, run_id=args.run_id,
                         include_ablations=not args.no_ablations)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, default=str))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
