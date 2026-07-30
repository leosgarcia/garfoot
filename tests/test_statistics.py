"""Testes unitários para o gerenciador de estatísticas e rankings da temporada."""

import pytest

from garfoot.domain.coach import Coach
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.game_state import GameState
from garfoot.domain.player import Player
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.domain.statistics import SeasonStatisticsManager, record_match_result_statistics
from garfoot.domain.team import Team
from garfoot.engine.events import GoalEvent
from garfoot.engine.match_engine import MatchResult, simulate_match


def test_record_goal_and_top_scorers_ranking():
    mgr = SeasonStatisticsManager()

    # Registra 3 gols para Gabriel no Flamengo (Série A)
    mgr.record_goal("Gabriel", "Flamengo", "Série A", age=28, overall=85)
    mgr.record_goal("Gabriel", "Flamengo", "Série A", age=28, overall=85)
    mgr.record_goal("Gabriel", "Flamengo", "Série A", age=28, overall=85)

    # Registra 1 gol para Pedro no Flamengo (Série A)
    mgr.record_goal("Pedro", "Flamengo", "Série A", age=26, overall=82)

    # Registra 2 gols para Cano no Fluminense (Copa do Brasil)
    mgr.record_goal("Cano", "Fluminense", "Copa do Brasil", age=35, overall=84)
    mgr.record_goal("Cano", "Fluminense", "Copa do Brasil", age=35, overall=84)

    # 1. Ranking Geral
    general_ranking = mgr.build_top_scorers_ranking()
    assert len(general_ranking) == 3
    assert general_ranking[0].player_name == "Gabriel"
    assert general_ranking[0].goals == 3
    assert general_ranking[1].player_name == "Cano"
    assert general_ranking[1].goals == 2

    # 2. Ranking filtrado pela Série A
    serie_a_ranking = mgr.build_top_scorers_ranking(competition="Série A")
    assert len(serie_a_ranking) == 2
    assert serie_a_ranking[0].player_name == "Gabriel"
    assert serie_a_ranking[1].player_name == "Pedro"


def test_coach_statistics_recording_and_ranking():
    mgr = SeasonStatisticsManager()

    # Treinador A vence Partida 1 por 2x0 na Série A
    mgr.record_match_coach_result("Dorival", "Flamengo", "Série A", goals_for=2, goals_against=0, reputation=85)
    mgr.record_match_coach_result("Abel", "Palmeiras", "Série A", goals_for=0, goals_against=2, reputation=90)

    # Treinador A empata Partida 2 por 1x1 na Série A
    mgr.record_match_coach_result("Dorival", "Flamengo", "Série A", goals_for=1, goals_against=1, reputation=85)
    mgr.record_match_coach_result("Vojvoda", "Fortaleza", "Série A", goals_for=1, goals_against=1, reputation=80)

    ranking = mgr.build_coach_ranking(competition="Série A")
    assert len(ranking) == 3

    # Dorival tem 1V 1E (4 pts em 6 = 66.7% de aproveitamento)
    top = ranking[0]
    assert top.coach_name == "Dorival"
    assert top.matches == 2
    assert top.wins == 1
    assert top.draws == 1
    assert top.points == 4
    assert top.win_percentage == 66.7
    assert top.goal_difference == 2


def test_fired_coaches_preserve_historical_stats():
    mgr = SeasonStatisticsManager()

    # Técnico Dorival acumula 1 vitória antes de ser demitido
    mgr.record_match_coach_result("Dorival", "Flamengo", "Série A", goals_for=3, goals_against=0)

    # Dorival é demitido do Flamengo e assume o São Paulo
    mgr.record_match_coach_result("Dorival", "São Paulo", "Série A", goals_for=1, goals_against=0)

    # Histórico de Dorival deve acumular 2 vitórias e 4 gols pró
    ranking = mgr.build_coach_ranking()
    assert len(ranking) == 1
    st = ranking[0]
    assert st.coach_name == "Dorival"
    assert st.matches == 2
    assert st.wins == 2
    assert st.goals_for == 4
    assert st.win_percentage == 100.0


def test_record_match_result_statistics_integration():
    mgr = SeasonStatisticsManager()

    p_home = [Player(name=f"Home {i}", age=22, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]
    p_away = [Player(name=f"Away {i}", age=22, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]

    c_home = Coach(name="Técnico Home", reputation=70, tactical_skill=70, morale_management=70, pressure_resistance=70)
    c_away = Coach(name="Técnico Away", reputation=70, tactical_skill=70, morale_management=70, pressure_resistance=70)

    home_team = Team(name="Time A", city="Rio", budget=100, players=p_home, coach=c_home)
    away_team = Team(name="Time B", city="SP", budget=100, players=p_away, coach=c_away)

    result = MatchResult(
        home_team_name="Time A",
        away_team_name="Time B",
        home_score=2,
        away_score=1,
        events=(
            GoalEvent(minute=10, team_name="Time A", player_name="Home 0"),
            GoalEvent(minute=30, team_name="Time B", player_name="Away 0"),
            GoalEvent(minute=75, team_name="Time A", player_name="Home 0"),
        ),
        shots_home=6,
        shots_away=4,
        possession_home=55.0,
        possession_away=45.0,
        cards_home=0,
        cards_away=0,
        starters_home=tuple(p.name for p in p_home),
        starters_away=tuple(p.name for p in p_away),
    )

    record_match_result_statistics(mgr, result, "Série D", home_team, away_team)

    # Verifica artilheiro "Home 0" com 2 gols
    scorers = mgr.build_top_scorers_ranking(competition="Série D")
    assert len(scorers) == 2
    assert scorers[0].player_name == "Home 0"
    assert scorers[0].goals == 2

    # Verifica ranking dos técnicos
    coaches = mgr.build_coach_ranking(competition="Série D")
    assert len(coaches) == 2
    assert coaches[0].coach_name == "Técnico Home"
    assert coaches[0].wins == 1


def test_statistics_manager_serialization_and_backwards_compatibility():
    mgr = SeasonStatisticsManager()
    mgr.record_goal("Gabriel", "Flamengo", "Série A", age=28, overall=85)
    mgr.record_match_coach_result("Dorival", "Flamengo", "Série A", goals_for=2, goals_against=0)

    serialized = mgr.to_dict()
    restored = SeasonStatisticsManager.from_dict(serialized)

    assert len(restored.player_stats) == 1
    assert len(restored.coach_stats) == 1

    # Compatibilidade com save antigo sem estatísticas
    from garfoot.domain.cup import KnockoutCup
    dummy_teams = [Team(name="A", city="A", budget=100), Team(name="B", city="B", budget=100)]
    orchestrator = SeasonOrchestrator(season_year=2026, championships={}, copa_do_brasil=KnockoutCup(name="Copa do Brasil", season_year=2026, teams=dummy_teams))
    state = GameState(
        save_name="TestSave",
        player_team_name="Flamengo",
        current_season=2026,
        current_round=1,
        season_orchestrator=orchestrator,
    )
    serialized_state = state.to_dict()
    del serialized_state["statistics"]

    restored_state = GameState.from_dict(serialized_state)
    assert restored_state.statistics is not None
    assert len(restored_state.statistics.player_stats) == 0
