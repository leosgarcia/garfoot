"""Testes unitários para a persistência e escrita atômica do SaveManager."""

import pytest

from garfoot.domain.cup import KnockoutCup
from garfoot.domain.game_state import GameState
from garfoot.domain.league import Championship
from garfoot.domain.season import LeagueTier
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.domain.team import Team
from garfoot.persistence.save_manager import InvalidSaveError, SaveManager, slugify


def _make_game_state(save_name: str = "Minha Carreira") -> GameState:
    teams_a = [Team(name="Flamengo", city="Rio", budget=100_000), Team(name="Vasco", city="Rio", budget=100_000)]
    champ_a = Championship(name="Série A 2026", season_year=2026, teams=teams_a)
    champ_a.generate_round_robin_fixtures(double_round=False)

    copa = KnockoutCup(name="Copa 2026", season_year=2026, teams=teams_a)
    copa.generate_initial_bracket(cbf_ranking={"Flamengo": 1, "Vasco": 2}, seed=1)

    orchestrator = SeasonOrchestrator(
        season_year=2026,
        championships={LeagueTier.SERIE_A: champ_a},
        copa_do_brasil=copa,
    )

    return GameState(
        save_name=save_name,
        player_team_name="Flamengo",
        current_season=2026,
        current_round=3,
        season_orchestrator=orchestrator,
    )


def test_slugify():
    assert slugify("Meu Save #1!") == "meu_save_1"
    assert slugify(" Carreira - Flamengo 2026 ") == "carreira_flamengo_2026"


def test_save_and_load_game_roundtrip(tmp_path):
    manager = SaveManager(save_dir=tmp_path)
    state = _make_game_state(save_name="Teste Save")

    path = manager.save_game(state)
    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()  # Arquivo temporário deve ter sido substituído

    loaded_state = manager.load_game(path)
    assert loaded_state.save_name == "Teste Save"
    assert loaded_state.player_team_name == "Flamengo"
    assert loaded_state.current_round == 3


def test_list_saves(tmp_path):
    manager = SaveManager(save_dir=tmp_path)
    state1 = _make_game_state("Save 1")
    state2 = _make_game_state("Save 2")

    manager.save_game(state1, "save1.json")
    manager.save_game(state2, "save2.json")

    saves = manager.list_saves()
    assert len(saves) == 2
    save_names = {s.save_name for s in saves}
    assert "Save 1" in save_names
    assert "Save 2" in save_names


def test_load_invalid_or_corrupted_save(tmp_path):
    manager = SaveManager(save_dir=tmp_path)

    # 1. Arquivo inexistente
    with pytest.raises(InvalidSaveError, match="não encontrado"):
        manager.load_game("inexistente.json")

    # 2. Arquivo corrompido (JSON inválido)
    corrupted_file = tmp_path / "corrupted.json"
    corrupted_file.write_text("{ json invalido: true ", encoding="utf-8")

    with pytest.raises(InvalidSaveError, match="corrompido ou inválido"):
        manager.load_game(corrupted_file)
