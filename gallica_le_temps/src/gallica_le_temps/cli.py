"""Command-line entry point.

Subcommands:

* ``search DATE``          - SRU-search the Le Temps issue for a date.
* ``run CONFIG.yaml``      - run the full pipeline described by a config file.
* ``crop-url``             - debug helper: build a IIIF crop URL from raw coords.

Network access uses :class:`~gallica_le_temps.client.GallicaClient`; where
Gallica is unreachable (e.g. a restricted egress policy) ``run`` will surface the
network error rather than fabricating data.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .client import GallicaClient
from .config import load_config
from .iiif import PixelRegion, crop_url
from .pipeline import Pipeline, collect, write_csv
from .sru import build_issue_query, build_sru_params, parse_sru_response, SRU_ENDPOINT


def _cmd_search(args: argparse.Namespace) -> int:
    client = GallicaClient()
    query = build_issue_query(args.date, min_ocr_quality=args.min_ocr_quality)
    params = build_sru_params(query, maximum_records=args.max_records)
    xml = client.get_text(SRU_ENDPOINT, params=params)
    records = parse_sru_response(xml)
    if not records:
        print(f"no issue found for {args.date}", file=sys.stderr)
        return 1
    for rec in records:
        q = "" if rec.ocr_quality is None else f" ocr={rec.ocr_quality:.1f}"
        print(f"{rec.date or '????-??-??'}  ark={rec.ark}{q}  {rec.title or ''}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    extractor = None
    if args.ocr:
        from .extract import TesseractExtractor

        extractor = TesseractExtractor()
    pipeline = Pipeline(GallicaClient(), extractor=extractor)
    rows = collect(pipeline.run(config))

    out = args.output or config.output_path
    if out:
        write_csv(rows, out)
        print(f"wrote {len(rows)} rows -> {out}")
    else:
        for row in rows:
            val = row.value if row.value is not None else ""
            print(
                f"{row.date}  {row.target:<24} {row.status:<10} "
                f"{val:<10} {row.crop_url or ''}"
            )
    ok = sum(1 for r in rows if r.status == "ok")
    print(f"{ok}/{len(rows)} located", file=sys.stderr)
    return 0


def _cmd_crop_url(args: argparse.Namespace) -> int:
    region = PixelRegion(args.x, args.y, args.w, args.h)
    print(crop_url(args.ark, args.page, region, size=args.size))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gallica-le-temps",
        description="Locate-with-text extraction of Le Temps quotations from Gallica.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="SRU-search the issue for a date")
    p_search.add_argument("date", help="issue date, YYYY-MM-DD")
    p_search.add_argument("--min-ocr-quality", type=float, default=None)
    p_search.add_argument("--max-records", type=int, default=5)
    p_search.set_defaults(func=_cmd_search)

    p_run = sub.add_parser("run", help="run the full pipeline from a YAML config")
    p_run.add_argument("config", help="path to a YAML run config")
    p_run.add_argument("--output", help="CSV output path (overrides config)")
    p_run.add_argument(
        "--ocr", action="store_true", help="OCR the crops (needs Tesseract)"
    )
    p_run.set_defaults(func=_cmd_run)

    p_crop = sub.add_parser("crop-url", help="build a IIIF crop URL from pixel coords")
    p_crop.add_argument("ark", help="document ark id, e.g. bpt6k...")
    p_crop.add_argument("page", type=int)
    p_crop.add_argument("x", type=int)
    p_crop.add_argument("y", type=int)
    p_crop.add_argument("w", type=int)
    p_crop.add_argument("h", type=int)
    p_crop.add_argument("--size", default="full")
    p_crop.set_defaults(func=_cmd_crop_url)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
