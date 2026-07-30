"""Testes unitários para a Copa do Brasil (mata-mata e byes)."""

import pytest

from garfoot.domain.cup import CupMatch, KnockoutCup
from garfoot.domain.enums import MatchStatus
from garfoot.domain.league import MatchFixture
from garfoot.domain.team import Team


def _make_team(name: str) -> Team:
    return Team(name=name, city="Cidade", budget=100_000)


def test_cup_match_winner_regular_time():
    fixture = MatchFixture(round_number=1, home_team="Flamengo", away_team="Vasco")
    match = CupMatch(fixture=fixture)

    assert match.winner is None

    match.record_result(2, 1)
    assert match.fixture.status == MatchStatus.PLAYED
    assert match.winner == "Flamengo"


def test_cup_match_winner_penalties():
    fixture = MatchFixture(round_number=1, home_team="Flamengo", away_team="Vasco")
    match = CupMatch(fixture=fixture)

    with pytest.raises(ValueError, match="Empate em partida eliminatória exige resultado de pênaltis"):
        match.record_result(1, 1)

    match.record_result(1, 1, home_penalties=5, away_penalties=4)
    assert match.winner == "Flamengo"
    assert match.home_penalties == 5
    assert match.away_penalties == 4


def test_knockout_cup_initial_bracket_with_byes_non_power_of_two():
    # 60 times no torneio (potência de 2 alvo = 64 -> 4 byes)
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 61)]

    # Ranking CBF: Time 01 a Time 04 no topo (posição 1 a 4)
    cbf_ranking = {f"Time {i:02d}": i for i in range(1, 61)}

    cup = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=42)

    # 4 times recebem bye
    assert len(cup.bye_teams) == 4
    assert set(cup.bye_teams) == {"Time 01", "Time 02", "Time 03", "Time 04"}

    # 56 times jogam a 1ª fase -> 28 confrontos
    assert len(cup.rounds) == 1
    first_round = cup.rounds[0]
    assert len(first_round) == 28


def test_advance_winners_pending_match_error():
    teams = [_make_team(f"Time {i}") for i in range(1, 5)]
    cbf_ranking = {f"Time {i}": i for i in range(1, 5)}

    cup = KnockoutCup(name="Copa 4 Times", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=1)

    # Tentar avançar com jogos sem resultado deve lançar erro
    with pytest.raises(ValueError, match="ainda não possui vencedor"):
        cup.advance_winners()


def test_full_cup_simulation():
    # Simulação completa de copa de 60 participantes até a final
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 61)]
    cbf_ranking = {f"Time {i:02d}": i for i in range(1, 61)}

    cup = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=7)

    # Executa a 1ª Fase (28 jogos)
    for m in cup.rounds[0]:
        m.record_result(2, 0)  # Mandante vence todos os jogos da 1ª fase

    # Avança para a 2ª Fase (28 vencedores + 4 byes = 32 times -> 16 jogos)
    round2 = cup.advance_winners(seed=7)
    assert len(round2) == 16

    # Executa da 2ª Fase até a Final
    while len(cup.rounds[-1]) > 1:
        for m in cup.rounds[-1]:
            m.record_result(1, 0)
        cup.advance_winners(seed=7)

    # Na rodada final (1 jogo), grava o resultado
    final_match = cup.rounds[-1][0]
    final_match.record_result(3, 1)

    assert cup.champion is not None
    assert cup.champion == final_match.winner


# ==========================================================================
# Testes do modo FASE PRELIMINAR (80 times — Opção B aprovada)
# ==========================================================================

def test_preliminary_bracket_generated_for_80_teams():
    """Com 80 times, generate_initial_bracket deve usar a fase preliminar."""
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 81)]
    cbf_ranking = {f"Time {i:02d}": i for i in range(1, 81)}

    cup = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=42)

    # Fase preliminar: 32 piores -> 16 confrontos
    assert len(cup.preliminary_round) == 16

    # Os 32 participantes da preliminar devem ser os de ranking 49..80
    prelim_names = {
        name
        for match in cup.preliminary_round
        for name in (match.fixture.home_team, match.fixture.away_team)
    }
    expected_prelim = {f"Time {i:02d}" for i in range(49, 81)}
    assert prelim_names == expected_prelim

    # Fase principal ainda não começou (rounds vazio)
    assert cup.rounds == []

    # Top-48 aguardam a fase principal
    assert len(cup._main_phase_seeds) == 48


def test_preliminary_bracket_no_byes_for_80_teams():
    """Com 80 times no modo preliminar, bye_teams deve estar vazio."""
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 81)]
    cbf_ranking = {f"Time {i:02d}": i for i in range(1, 81)}

    cup = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=42)

    assert cup.bye_teams == []


def test_advance_preliminary_winners_creates_main_phase_64_teams():
    """Após avançar da preliminar, a fase principal deve ter 32 confrontos (64 times)."""
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 81)]
    cbf_ranking = {f"Time {i:02d}": i for i in range(1, 81)}

    cup = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=42)

    # Simula todos os 16 jogos da preliminar (mandante vence)
    for match in cup.preliminary_round:
        match.record_result(1, 0)

    main_round = cup.advance_preliminary_winners(seed=42)

    # Fase principal: 64 times -> 32 confrontos
    assert len(main_round) == 32
    assert len(cup.rounds) == 1
    assert len(cup.rounds[0]) == 32

    # Seeds já foram consumidos
    assert cup._main_phase_seeds == []


def test_advance_preliminary_winners_error_if_match_pending():
    """advance_preliminary_winners deve lançar erro se houver jogo sem resultado."""
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 81)]
    cbf_ranking = {f"Time {i:02d}": i for i in range(1, 81)}

    cup = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=42)

    # Não grava nenhum resultado na preliminar
    with pytest.raises(ValueError, match="ainda não possui vencedor"):
        cup.advance_preliminary_winners()


def test_advance_preliminary_winners_error_if_no_preliminary():
    """advance_preliminary_winners deve lançar erro se chamado sem fase preliminar."""
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 5)]
    cbf_ranking = {f"Time {i:02d}": i for i in range(1, 5)}

    cup = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=42)

    # Modo clássico não gera fase preliminar
    with pytest.raises(ValueError, match="Não há fase preliminar gerada"):
        cup.advance_preliminary_winners()


def test_full_cup_simulation_80_teams_79_matches():
    """Simulação completa de 80 times: 79 jogos no total, campeão definido."""
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 81)]
    cbf_ranking = {f"Time {i:02d}": i for i in range(1, 81)}

    cup = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=7)

    total_matches = 0

    # Fase Preliminar: 16 jogos
    for m in cup.preliminary_round:
        m.record_result(2, 0)
    total_matches += len(cup.preliminary_round)

    # Avança da preliminar para a fase principal (32 confrontos)
    main_round = cup.advance_preliminary_winners(seed=7)
    assert len(main_round) == 32  # Rodada 1 da fase principal

    # Fase Principal: rodadas 1..6 (32 -> 16 -> 8 -> 4 -> 2 -> 1)
    while True:
        current = cup.rounds[-1]
        for m in current:
            m.record_result(1, 0)
        total_matches += len(current)

        if len(current) == 1:
            break   # Final já jogada

        cup.advance_winners(seed=7)

    # Total: 16 (prelim) + 32 + 16 + 8 + 4 + 2 + 1 = 79
    assert total_matches == 79

    assert cup.champion is not None


def test_full_cup_simulation_80_teams_all_teams_participate():
    """Todos os 80 times devem aparecer em pelo menos um jogo."""
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 81)]
    cbf_ranking = {f"Time {i:02d}": i for i in range(1, 81)}

    cup = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=teams)
    cup.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=99)

    # Coleta nomes dos participantes da fase preliminar
    seen: set[str] = set()
    for m in cup.preliminary_round:
        seen.add(m.fixture.home_team)
        seen.add(m.fixture.away_team)

    # Completa a preliminar
    for m in cup.preliminary_round:
        m.record_result(1, 0)

    # Coleta participantes da fase principal
    cup.advance_preliminary_winners(seed=99)
    for m in cup.rounds[0]:
        seen.add(m.fixture.home_team)
        seen.add(m.fixture.away_team)

    # Todos os 80 times devem ter participado de pelo menos um jogo
    all_team_names = {t.name for t in teams}
    assert seen == all_team_names

