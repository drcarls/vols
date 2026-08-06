"""Bloc capability ratios from NMC — pure logic on synthetic rows."""

import csv

from cow_mid.capability import (
    alliance_ccodes,
    capability_series,
    milex_ratio,
    parse_nmc,
    write_long_csv,
)


def _write_nmc(tmp_path):
    p = tmp_path / "nmc.csv"
    # Entente = 220 France, 365 Russia, 200 UK ; Alliance = 255 Ger, 300 AH, 325 Italy
    rows = [
        # 1910
        ("FRN", 220, 1910, 0.07, 49539),
        ("RUS", 365, 1910, 0.12, 62099),
        ("UK", 200, 1910, 0.11, 61417),
        ("GMY", 255, 1910, 0.14, 60416),
        ("AUH", 300, 1910, 0.04, 23208),
        ("ITA", 325, 1910, 0.03, 22016),
    ]
    with open(p, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stateabb", "ccode", "year", "cinc", "milex"])
        for r in rows:
            w.writerow(r)
    return str(p)


def test_parse_and_bloc_sums(tmp_path):
    nmc = parse_nmc(_write_nmc(tmp_path))
    cy = capability_series(nmc, 1910, 1910)[0]
    assert round(cy.entente_cinc, 2) == 0.30   # .07+.12+.11
    assert round(cy.alliance_cinc, 2) == 0.21   # .14+.04+.03


def test_capratio_and_parity(tmp_path):
    nmc = parse_nmc(_write_nmc(tmp_path))
    cy = capability_series(nmc, 1910, 1910)[0]
    assert cy.capratio == round(0.21 / 0.30, 4) or abs(cy.capratio - 0.7) < 0.02
    assert 0 < cy.parity <= 1
    assert abs(cy.alliance_share - 0.21 / 0.51) < 1e-6


def test_exclude_italy_shrinks_alliance(tmp_path):
    nmc = parse_nmc(_write_nmc(tmp_path))
    incl = capability_series(nmc, 1910, 1910)[0].alliance_cinc
    excl = capability_series(nmc, 1910, 1910, exclude_italy=True)[0].alliance_cinc
    assert excl < incl
    assert 325 not in alliance_ccodes(exclude_italy=True)


def test_milex_ratio_germany_uk(tmp_path):
    nmc = parse_nmc(_write_nmc(tmp_path))
    r = milex_ratio(nmc, 255, 200, 1910)
    assert abs(r - 60416 / 61417) < 1e-6


def test_write_long_csv_schema(tmp_path):
    nmc = parse_nmc(_write_nmc(tmp_path))
    out = tmp_path / "cap.csv"
    n = write_long_csv(nmc, str(out), start=1910, end=1910)
    with open(out, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert n == len(rows)
    assert {"capratio_alliance_entente", "bloc_parity", "milex_germany_uk"} <= {r["series"] for r in rows}
    for r in rows:
        float(r["value"])
