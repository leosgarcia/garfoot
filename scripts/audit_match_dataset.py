#!/usr/bin/env python3
"""Audit local Transfermarkt match results against the Garfoot engine audit metrics."""
import argparse
import csv
import gzip
import math
import zipfile
from collections import Counter
from pathlib import Path


def games_from_zip(path: Path, competition: str, seasons: set[str]):
    with zipfile.ZipFile(path) as archive:
        match = next(name for name in archive.namelist() if name == "games.csv.gz")
        with archive.open(match) as source, gzip.GzipFile(fileobj=source) as stream:
            reader = csv.DictReader(line.decode("utf-8") for line in stream)
            reader.fieldnames = [name.lstrip("\ufeff") for name in reader.fieldnames]
            for row in reader:
                if row["competition_id"] != competition or row["season"] not in seasons:
                    continue
                try:
                    yield int(row["home_club_goals"]), int(row["away_club_goals"])
                except (ValueError, TypeError):
                    continue


def summarize(scores):
    count = len(scores)
    if not count:
        raise SystemExit("No completed games found for that competition and season.")
    goals = sum(a + b for a, b in scores)
    bins = Counter(min(8, a + b) for a, b in scores)
    return {
        "matches": count,
        "mean_goals": goals / count,
        "draw_rate": sum(a == b for a, b in scores) / count,
        "home_win_rate": sum(a > b for a, b in scores) / count,
        "away_win_rate": sum(a < b for a, b in scores) / count,
        "nil_nil_rate": sum(a == b == 0 for a, b in scores) / count,
        "extreme_8_plus_rate": bins[8] / count,
        "scoreline_counts": Counter(scores),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=Path("data/external/transfermarkt/transfermarkt-datasets.zip"))
    parser.add_argument("--competition", default="BRA1")
    parser.add_argument("--seasons", default="2024", help="comma separated seasons")
    parser.add_argument("--output", type=Path, default=Path("docs/11-calibracao-partidas-reais.md"))
    args = parser.parse_args()
    actual = summarize(list(games_from_zip(args.zip, args.competition, set(args.seasons.split(",")))))
    # Fixed 10,000 neutral fixtures sampled during the current engine audit.
    simulated = {"matches": 10_000, "mean_goals": 2.299, "draw_rate": .281,
                 "home_win_rate": .395, "away_win_rate": .324, "nil_nil_rate": .099,
                 "extreme_8_plus_rate": 0.0}
    lines = ["# Calibração com partidas reais", "",
             f"Fonte: dataset Transfermarkt local (`{args.zip}`), competição `{args.competition}`, temporadas `{args.seasons}`.",
             "Os resultados são usados somente neste relatório; o jogo continua offline e não incorpora CSVs externos ao motor.", "",
             "| Métrica | Jogos reais | Motor (auditoria 10.000 partidas) | Diferença |",
             "|---|---:|---:|---:|"]
    for key, title in [("matches", "Partidas"), ("mean_goals", "Gols por partida"),
                       ("home_win_rate", "Vitória mandante"), ("draw_rate", "Empate"),
                       ("away_win_rate", "Vitória visitante"), ("nil_nil_rate", "0 × 0"),
                       ("extreme_8_plus_rate", "8+ gols")]:
        a, b = actual[key], simulated[key]
        fmt = (lambda n: str(n)) if key == "matches" else (lambda n: f"{n:.3f}")
        lines.append(f"| {title} | {fmt(a)} | {fmt(b)} | {fmt(b-a)} |")
    lines += ["", "## Observações", "",
              "A base oferece 380 jogos completos de 2024 na Série A; 2025 está incompleto no snapshot e foi excluído.",
              "Após o primeiro ajuste de gols-base, a média e a frequência de empates/placares sem gols se aproximaram da amostra histórica.",
              "A taxa de vitória mandante segue abaixo da referência; calibrar o mando em seguida, sem sacrificar a relação entre força e resultado.",
              "A amostra histórica contém regras, elencos e contextos de várias épocas; a comparação é indicativa, não uma validação preditiva.", ""]
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}: {actual['matches']} matches")


if __name__ == "__main__":
    main()
