#!/usr/bin/env python3
"""Download local image assets referenced by the Transfermarkt snapshot."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import unicodedata
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


DEFAULT_DATA_ROOT = Path("data/external/transfermarkt")
DEFAULT_OUTPUT_ROOT = Path("data/assets/transfermarkt")
USER_AGENT = "Garfoot/0.1 personal project"
COUNTRY_ALIASES = {
    "Bosnia-Herzegovina": "ba",
    "Brunei Darussalam": "bn",
    "Chinese Taipei": "tw",
    "Czech Republic": "cz",
    "England": "gb",
    "Hongkong": "hk",
    "Korea, South": "kr",
    "Scotland": "gb",
    "Türkiye": "tr",
    "Wales": "gb",
    "Northern Ireland": "gb",
    "Kosovo": "xk",
}


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", normalized.lower()).strip()


def get_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def download(url: str, destination: Path, delay: float, force: bool) -> bool:
    if destination.exists() and not force:
        return True

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response, temporary.open("wb") as output:
            output.write(response.read())
        temporary.replace(destination)
        time.sleep(delay)
        return True
    except (HTTPError, URLError, TimeoutError, OSError):
        temporary.unlink(missing_ok=True)
        return False


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def country_code_map(cache_path: Path, names: set[str], force: bool) -> dict[str, str]:
    if cache_path.exists() and not force:
        mapping = json.loads(cache_path.read_text(encoding="utf-8"))
        for name, code in COUNTRY_ALIASES.items():
            mapping[normalize_name(name)] = code
        return mapping

    response = get_json("https://flagcdn.com/en/codes.json")
    mapping: dict[str, str] = {}
    for code, name in response.items():
        mapping[normalize_name(name)] = code.lower()

    for name, code in COUNTRY_ALIASES.items():
        mapping[normalize_name(name)] = code

    result = {
        normalize_name(name): mapping[normalize_name(name)]
        for name in names
        if normalize_name(name) in mapping
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def download_club_badges(rows: list[dict[str, str]], output: Path, delay: float, force: bool) -> list[str]:
    failures = []
    for row in rows:
        club_id = row["club_id"]
        url = f"https://img.a.transfermarkt.technology/wappen/homepage/{club_id}.png"
        if not download(url, output / f"{club_id}.png", delay, force):
            failures.append(f"club:{club_id}")
    return failures


def download_national_badges(rows: list[dict[str, str]], output: Path, delay: float, force: bool) -> list[str]:
    failures = []
    for row in rows:
        url = row.get("team_image_url", "")
        if url and not download(url, output / f"{row['national_team_id']}.png", delay, force):
            failures.append(f"national-team:{row['national_team_id']}")
    return failures


def download_player_photos(rows: list[dict[str, str]], output: Path, delay: float, force: bool) -> list[str]:
    failures = []
    for row in rows:
        url = row.get("image_url", "")
        if not url:
            continue
        suffix = Path(urlparse(url).path).suffix or ".jpg"
        if not download(url, output / f"{row['player_id']}{suffix}", delay, force):
            failures.append(f"player:{row['player_id']}")
    return failures


def download_flags(rows: list[dict[str, str]], output: Path, cache_path: Path, delay: float, force: bool) -> list[str]:
    names = {row["country_name"] for row in rows if row.get("country_name")}
    mapping = country_code_map(cache_path, names, force)
    failures = []
    for name in sorted(names):
        code = mapping.get(normalize_name(name))
        if not code:
            failures.append(f"flag:{name}")
            continue
        url = f"https://flagcdn.com/w320/{code}.png"
        if not download(url, output / f"{code}.png", delay, force):
            failures.append(f"flag:{name}")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--assets",
        default="clubs,flags,national-teams",
        help="Tipos separados por vírgula: clubs, flags, national-teams, players",
    )
    parser.add_argument("--limit", type=int, help="Limita cada tipo de asset")
    parser.add_argument("--delay", type=float, default=0.15)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = {item.strip() for item in args.assets.split(",") if item.strip()}
    raw = args.data_root / "raw"
    args.output_root.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    clubs = read_rows(raw / "clubs.csv")
    national_teams = read_rows(raw / "national_teams.csv")
    players = read_rows(raw / "players.csv")
    countries = read_rows(raw / "countries.csv")

    if args.limit:
        clubs = clubs[: args.limit]
        national_teams = national_teams[: args.limit]
        players = players[: args.limit]

    if "clubs" in selected:
        failures.extend(download_club_badges(clubs, args.output_root / "club-badges", args.delay, args.force))
    if "national-teams" in selected:
        failures.extend(download_national_badges(national_teams, args.output_root / "national-badges", args.delay, args.force))
    if "players" in selected:
        failures.extend(download_player_photos(players, args.output_root / "player-photos", args.delay, args.force))
    if "flags" in selected:
        failures.extend(download_flags(countries, args.output_root / "flags", args.output_root / "country-codes.json", args.delay, args.force))

    report = args.output_root / "download-failures.txt"
    report.write_text("\n".join(failures) + ("\n" if failures else ""), encoding="utf-8")
    print(f"Assets selecionados: {', '.join(sorted(selected))}")
    print(f"Falhas: {len(failures)} (relatório: {report})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())