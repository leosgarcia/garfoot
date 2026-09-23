#!/usr/bin/env python3
"""Prototype Transfermarkt ratings and compare their distribution with EAFC26."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

DEFAULT_RAW = Path("data/external/transfermarkt/raw")
DEFAULT_REFERENCE = Path("data/external/eafc26-reference/players.csv")
DEFAULT_OUTPUT = Path("data/processed/ratings-prototype")
SNAPSHOT_DATE = date(2026, 7, 6)
ATTRIBUTES = ("tecnica", "fisico", "mental", "velocidade", "finalizacao", "passe", "marcacao", "potencial")
REFERENCE_FIELDS = {
    "tecnica": ("dribbling", "skill_dribbling"),
    "fisico": ("physic", "power_stamina", "power_strength"),
    "mental": ("mentality_composure", "mentality_reactions"),
    "velocidade": ("pace", "movement_sprint_speed"),
    "finalizacao": ("shooting", "attacking_finishing"),
    "passe": ("passing", "attacking_short_passing"),
    "marcacao": ("defending", "defending_marking_awareness"),
    "potencial": ("potential",),
}
LEVEL_OFFSETS = {
    "elite": (18, 6, 15, 8, 23, 15, 9, 12),
    "alto": (23, 5, 20, 6, 20, 18, 11, 13),
    "profissional": (24, 2, 18, 5, 15, 15, 9, 16),
    "desenvolvimento": (24, 0, 15, 3, 8, 12, 8, 16),
}


def clamp(value: float) -> float:
    return max(20.0, min(100.0, value))


def position_group(row: dict[str, str]) -> str:
    position = (row.get("sub_position") or row.get("position") or "").lower()
    if "goalkeeper" in position:
        return "gol"
    if "defender" in position or "back" in position:
        return "defesa"
    if "midfield" in position or "wing" in position:
        return "meio"
    return "ataque"


def position_value(group: str, values: dict[str, float]) -> float:
    return values[group]


def competitive_level(value: float) -> str:
    if value >= 20_000_000:
        return "elite"
    if value >= 5_000_000:
        return "alto"
    if value >= 500_000:
        return "profissional"
    return "desenvolvimento"


def player_age(row: dict[str, str]) -> int:
    raw_date = (row.get("date_of_birth") or "")[:10]
    if not raw_date:
        return 28
    try:
        birth_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        return 28
    age = SNAPSHOT_DATE.year - birth_date.year
    if (SNAPSHOT_DATE.month, SNAPSHOT_DATE.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def generate(row: dict[str, str], stats: dict[str, int]) -> dict[str, int]:
    age = max(15, min(60, player_age(row)))
    height = int(float(row.get("height_in_cm") or 175))
    market = float(row.get("market_value_in_eur") or 0)
    appearances = stats["appearances"]
    minutes = stats["minutes"]
    goals = stats["goals"]
    assists = stats["assists"]
    caps = int(row.get("international_caps") or 0)
    group = position_group(row)

    market_score = clamp(25 + 18 * math.log10(1 + market / 100_000))
    experience = clamp(25 + min(40, minutes / 500) + min(15, appearances / 20) + min(20, caps * 0.8))
    contribution = 35 if minutes == 0 else clamp(35 + min(1.2, goals * 90 / minutes) * 22 + min(1.0, assists * 90 / minutes) * 16)
    maturity = clamp(58 - abs(age - 28) * 1.3)
    physical_age = 76 - abs(age - 27) * 1.25
    physical_height = 58 + (height - 175) * 0.35
    physical_base = clamp(physical_age * 0.65 + physical_height * 0.35)
    position_priority = position_value(group, {"gol": 62, "defesa": 58, "meio": 82, "ataque": 86})
    finishing_priority = position_value(group, {"gol": 42, "defesa": 42, "meio": 66, "ataque": 86})
    passing_priority = position_value(group, {"gol": 42, "defesa": 55, "meio": 88, "ataque": 68})
    marking_priority = position_value(group, {"gol": 25, "defesa": 88, "meio": 48, "ataque": 28})
    technique = market_score * 0.55 + contribution * 0.25 + experience * 0.20
    physical = physical_base * 0.65 + market_score * 0.20 + position_priority * 0.15
    mental = experience * 0.45 + market_score * 0.30 + maturity * 0.25
    speed = physical_base * 0.55 + position_priority * 0.25 + maturity * 0.10 + market_score * 0.10
    finishing = contribution * 0.55 + technique * 0.25 + finishing_priority * 0.20
    passing = technique * 0.45 + contribution * 0.20 + experience * 0.20 + passing_priority * 0.15
    marking = market_score * 0.25 + mental * 0.25 + physical * 0.20 + marking_priority * 0.30
    potential_age = 92 if age <= 21 else 84 if age <= 24 else 72 if age <= 28 else 58 if age <= 31 else 42
    potential = market_score * 0.45 + potential_age * 0.40 + maturity * 0.15
    level = competitive_level(market)
    offsets = LEVEL_OFFSETS[level]
    values = tuple(value + offset for value, offset in zip(
        (technique, physical, mental, speed, finishing, passing, marking, potential), offsets
    ))
    return dict(zip(ATTRIBUTES, (round(clamp(value)) for value in values)))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = (len(ordered) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def summary(values: list[float]) -> str:
    return " / ".join(f"{quantile(values, q):.1f}" for q in (0.1, 0.5, 0.9))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    appearances = defaultdict(lambda: {"appearances": 0, "minutes": 0, "goals": 0, "assists": 0})
    for row in read_rows(args.raw / "appearances.csv"):
        stats = appearances[row["player_id"]]
        stats["appearances"] += 1
        stats["minutes"] += int(row.get("minutes_played") or 0)
        stats["goals"] += int(row.get("goals") or 0)
        stats["assists"] += int(row.get("assists") or 0)

    generated = []
    for row in read_rows(args.raw / "players.csv"):
        rating = generate(row, appearances[row["player_id"]])
        market = float(row.get("market_value_in_eur") or 0)
        generated.append({
            "player_id": row["player_id"],
            "name": row["name"],
            "grupo_posicao": position_group(row),
            "nivel_competitivo": competitive_level(market),
            **rating,
        })

    reference = read_rows(args.reference)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "generated-ratings.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=generated[0].keys())
        writer.writeheader()
        writer.writerows(generated)

    report = ["# Protótipo de RatingJogador", "", "Quantis P10 / P50 / P90", "", "| Atributo | Garfoot | EAFC26 |", "|---|---:|---:|"]
    for attribute in ATTRIBUTES:
        reference_values = []
        for row in reference:
            for field in REFERENCE_FIELDS[attribute]:
                if row.get(field):
                    reference_values.append(float(row[field]))
                    break
        report.append(f"| `{attribute}` | {summary([row[attribute] for row in generated])} | {summary(reference_values)} |")
    report.extend(["", "## Por nível competitivo", "", "| Nível | Jogadores | Técnica P50 | Mental P50 | Potencial P50 |", "|---|---:|---:|---:|---:|"])
    for level in ("elite", "alto", "profissional", "desenvolvimento"):
        generated_level = [row for row in generated if row["nivel_competitivo"] == level]
        reference_level = [row for row in reference if competitive_level(float(row.get("value_eur") or 0)) == level]
        if not generated_level:
            continue
        report.append(
            f"| `{level}` | {len(generated_level)} | "
            f"{quantile([row['tecnica'] for row in generated_level], .5):.1f} | "
            f"{quantile([row['mental'] for row in generated_level], .5):.1f} | "
            f"{quantile([row['potencial'] for row in generated_level], .5):.1f} |"
        )
        if reference_level:
            report.append(
                f"| `{level}` EAFC26 | {len(reference_level)} | "
                f"{quantile([float(row['dribbling']) for row in reference_level if row.get('dribbling')], .5):.1f} | "
                f"{quantile([float(row['mentality_composure']) for row in reference_level if row.get('mentality_composure')], .5):.1f} | "
                f"{quantile([float(row['potential']) for row in reference_level if row.get('potential')], .5):.1f} |"
            )
    report.extend(["", "A referência EAFC26 serve somente para calibrar distribuição; não é fonte canônica do domínio."])
    (args.output / "distribution-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Gerados: {len(generated)} ratings")
    print(f"Relatório: {args.output / 'distribution-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
