"""Script utilitário para renderizar e capturar imagens das telas da TUI do Garfoot em modo Headless."""

from __future__ import annotations

import asyncio
from pathlib import Path

from garfoot.domain.cup import KnockoutCup
from garfoot.domain.game_state import GameState
from garfoot.domain.league import Championship
from garfoot.domain.season import LeagueTier
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.ui.app import GarfootApp
from garfoot.ui.data import load_teams


async def capture_tui_screens() -> None:
    print("Iniciando captura headless da TUI do Garfoot...")
    artifacts_dir = Path("/home/leonardo/.gemini/antigravity-ide/brain/d9944b86-0b34-4a1d-9213-63915dd27afb")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    app = GarfootApp()

    # Prepara um GameState completo para renderizar as telas com dados reais
    teams = load_teams()
    teams_a = teams[0:20]
    teams_b = teams[20:40]
    teams_c = teams[40:60]
    teams_d = teams[60:80]

    championships = {
        LeagueTier.SERIE_A: Championship(name="Campeonato Brasileiro Série A", season_year=2026, teams=teams_a),
        LeagueTier.SERIE_B: Championship(name="Campeonato Brasileiro Série B", season_year=2026, teams=teams_b),
        LeagueTier.SERIE_C: Championship(name="Campeonato Brasileiro Série C", season_year=2026, teams=teams_c),
        LeagueTier.SERIE_D: Championship(name="Campeonato Brasileiro Série D", season_year=2026, teams=teams_d),
    }

    copa = KnockoutCup(name="Copa do Brasil", season_year=2026, teams=teams)
    orchestrator = SeasonOrchestrator(season_year=2026, championships=championships, copa_do_brasil=copa)
    orchestrator.start_new_season(cbf_ranking={t.name: 1000 for t in teams}, seed=2026)

    game_state = GameState(
        save_name="Carreira Demo",
        player_team_name="Ferroviário Atlético Clube",
        current_season=2026,
        current_round=1,
        season_orchestrator=orchestrator,
    )
    app.current_game_state = game_state

    # Roda a aplicação Textual em modo Headless de teste para capturar SVG/Screenshots
    async with app.run_test(size=(120, 36)) as pilot:
        # 1. Tela de Abertura (Splash Screen)
        print("Capturando 1. Splash Screen...")
        app.save_screenshot(str(artifacts_dir / "01_splash_screen.svg"))
        await pilot.press("enter")
        await pilot.pause(0.2)

        # 2. Menu Principal (Main Menu)
        print("Capturando 2. Menu Principal...")
        app.save_screenshot(str(artifacts_dir / "02_main_menu.svg"))

        # 3. Hub da Temporada (Season Hub)
        print("Capturando 3. Hub da Temporada...")
        app.switch_screen("season_hub")
        await pilot.pause(0.2)
        app.save_screenshot(str(artifacts_dir / "03_season_hub.svg"))

        # 4. Gestão do Clube e Escalação Tática (Match Prep)
        print("Capturando 4. Gestão e Escalação Tática...")
        app.switch_screen("match_prep")
        await pilot.pause(0.2)
        app.save_screenshot(str(artifacts_dir / "04_match_prep.svg"))

        # 5. Tabela Completa de Classificação (Standings)
        print("Capturando 5. Tabela de Classificação...")
        app.switch_screen("standings")
        await pilot.pause(0.2)
        app.save_screenshot(str(artifacts_dir / "05_standings.svg"))

        # 6. Mercado de Transferências (Market)
        print("Capturando 6. Mercado de Transferências...")
        app.switch_screen("market")
        await pilot.pause(0.2)
        app.save_screenshot(str(artifacts_dir / "06_market.svg"))

    print(f"Todas as 6 telas foram capturadas em: {artifacts_dir}")


def main() -> None:
    asyncio.run(capture_tui_screens())


if __name__ == "__main__":
    main()
