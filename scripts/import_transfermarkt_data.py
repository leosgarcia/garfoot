#!/usr/bin/env python3
"""Normalize the external Transfermarkt CSV snapshot into Garfoot seed JSON."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_INPUT = Path("data/external/transfermarkt/raw")
DEFAULT_OUTPUT = Path("data/processed/transfermarkt")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def normalize_clubs(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "source_id": row["club_id"],
            "name": row["name"],
            "code": clean(row.get("club_code")),
            "competition_id": clean(row.get("domestic_competition_id")),
            "stadium_name": clean(row.get("stadium_name")),
            "stadium_seats": clean(row.get("stadium_seats")),
            "coach_name": clean(row.get("coach_name")),
        }
        for row in rows
    ]


def normalize_players(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "source_id": row["player_id"],
            "name": row["name"],
            "date_of_birth": clean(row.get("date_of_birth")),
            "current_club_id": clean(row.get("current_club_id")),
            "position": clean(row.get("sub_position")) or clean(row.get("position")),
            "foot": clean(row.get("foot")),
            "height_in_cm": clean(row.get("height_in_cm")),
            "citizenship": clean(row.get("country_of_citizenship")),
            "market_value_in_eur": clean(row.get("market_value_in_eur")),
        }
        for row in rows
    ]


def normalize_national_teams(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "source_id": row["national_team_id"],
            "name": row["name"],
            "country_id": clean(row.get("country_id")),
            "country_code": clean(row.get("country_code")),
            "confederation": clean(row.get("confederation")),
            "coach_name": clean(row.get("coach_name")),
        }
        for row in rows
    ]


def write_json(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, help="Limita cada tabela para validação")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    readers = {
        "clubs": ("clubs.csv", normalize_clubs),
        "players": ("players.csv", normalize_players),
        "national_teams": ("national_teams.csv", normalize_national_teams),
    }
    manifest = {
        "source": "dcaribou/transfermarkt-datasets",
        "source_snapshot": "2026-07-06",
        "generated_at": datetime.now(UTC).isoformat(),
        "tables": {},
    }
    for name, (filename, normalizer) in readers.items():
        rows = read_csv(args.input / filename)
        if args.limit:
            rows = rows[: args.limit]
        records = normalizer(rows)
        write_json(args.output / f"{name}.json", records)
        manifest["tables"][name] = {"records": len(records), "source_file": filename}
    write_json(args.output / "manifest.json", manifest)
    print(f"Dados normalizados em {args.output}")
    for name, details in manifest["tables"].items():
        print(f"{name}: {details['records']} registros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
