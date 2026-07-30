"""Testes unitários para o GameState e serialização do estado de jogo."""

from garfoot.domain.cup import KnockoutCup
from garfoot.domain.game_state import GameState, SaveMetadata
from garfoot.domain.league import Championship
from garfoot.domain.season import LeagueTier
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.domain.team import Team


def _make_team(name: str) -> Team:
    return Team(name=name, city="Cidade", budget=100_000)


def test_game_state_to_dict_and_from_dict():
    teams_a = [_make_team("Flamengo"), _make_team("Palmeiras")]
    champ_a = Championship(name="Série A 2026", season_year=2026, teams=teams_a)
    champ_a.generate_round_robin_fixtures(double_round=False)

    copa = KnockoutCup(name="Copa 2026", season_year=2026, teams=teams_a)
    cbf_ranking = {"Flamengo": 1, "Palmeiras": 2}
    copa.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=1)

    orchestrator = SeasonOrchestrator(
        season_year=2026,
        championships={LeagueTier.SERIE_A: champ_a},
        copa_do_brasil=copa,
    )

    state = GameState(
        save_name="Meu Save Teste",
        player_team_name="Flamengo",
        current_season=2026,
        current_round=5,
        season_orchestrator=orchestrator,
        saved_at="2026-07-29T00:00:00Z",
    )

    data = state.to_dict()
    reconstructed = GameState.from_dict(data)

    assert reconstructed.save_name == "Meu Save Teste"
    assert reconstructed.player_team_name == "Flamengo"
    assert reconstructed.current_season == 2026
    assert reconstructed.current_round == 5
    assert reconstructed.saved_at == "2026-07-29T00:00:00Z"
    assert LeagueTier.SERIE_A in reconstructed.season_orchestrator.championships


def test_save_metadata():
    meta = SaveMetadata(
        save_name="Save 1",
        player_team_name="Corinthians",
        season_year=2026,
        current_round=10,
        saved_at="2026-07-29T00:00:00Z",
    )

    data = meta.to_dict()
    reconstructed = SaveMetadata.from_dict(data)

    assert reconstructed.save_name == "Save 1"
    assert reconstructed.player_team_name == "Corinthians"
