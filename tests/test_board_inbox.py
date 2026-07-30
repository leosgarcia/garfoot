"""Testes unitários e de integração para a Caixa de Entrada da Diretoria (Board Inbox)."""

from __future__ import annotations

import pytest

from garfoot.domain.board_inbox import (
    BoardInbox,
    BoardMessage,
    BoardMessageOption,
    BoardMessageStatus,
    BoardMessageType,
    process_board_decision,
    process_round_board_messages,
)
from garfoot.domain.contract import Contract
from garfoot.domain.cup import KnockoutCup
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.game_state import GameState
from garfoot.domain.league import Championship
from garfoot.domain.player import Player
from garfoot.domain.season import LeagueTier
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.domain.team import Team
from garfoot.persistence.save_manager import SaveManager


def make_test_game_state(user_budget: int = 1_000_000, current_round: int = 1) -> GameState:
    """Helper para construir um GameState válido de testes."""

    p1 = Player("Atleta 1", 25, PlayerPosition.GOALKEEPER, 70, 70, 90, 80, 500_000, 50_000, Contract(years_remaining=2))
    p2 = Player("Reserva 1", 22, PlayerPosition.FORWARD, 60, 40, 80, 80, 200_000, 20_000, Contract(years_remaining=2, is_protected=True))

    team_user = Team("Meu Clube", "Cidade X", budget=user_budget, players=[p1, p2])
    team_other = Team("Rival FC", "Cidade Y", budget=500_000, players=[])
    dummy1 = Team("Dummy 1", "Cidade A", budget=500_000, players=[])
    dummy2 = Team("Dummy 2", "Cidade B", budget=500_000, players=[])

    championships = {
        LeagueTier.SERIE_D: Championship(name="Série D", season_year=2026, teams=[team_user, team_other]),
        LeagueTier.SERIE_A: Championship(name="Série A", season_year=2026, teams=[dummy1, dummy2]),
        LeagueTier.SERIE_B: Championship(name="Série B", season_year=2026, teams=[dummy1, dummy2]),
        LeagueTier.SERIE_C: Championship(name="Série C", season_year=2026, teams=[dummy1, dummy2]),
    }

    copa = KnockoutCup("Copa", season_year=2026, teams=[team_user, team_other])
    orchestrator = SeasonOrchestrator(2026, championships, copa)

    return GameState(
        save_name="TestSave",
        player_team_name="Meu Clube",
        current_season=2026,
        current_round=current_round,
        season_orchestrator=orchestrator,
    )


def test_board_message_types_and_serialization():
    opt_a = BoardMessageOption(id="opt_a", text="Prometer Resultados", description="Aumenta otimismo.", effect_type="promise_results")
    msg = BoardMessage(
        id="msg_01",
        message_type=BoardMessageType.RESULTS_WARNING,
        title="Cobrança de Resultados",
        content="Exigimos vitórias.",
        options=(opt_a,),
        round_created=1,
        expires_at_round=3,
        default_option_id_on_timeout="opt_a",
    )

    data = msg.to_dict()
    reconstructed = BoardMessage.from_dict(data)

    assert reconstructed.id == "msg_01"
    assert reconstructed.message_type == BoardMessageType.RESULTS_WARNING
    assert len(reconstructed.options) == 1
    assert reconstructed.options[0].effect_type == "promise_results"


def test_process_board_decision_example_1_results_warning():
    state = make_test_game_state()
    opt_a = BoardMessageOption(id="opt_a", text="Prometer 6 Pontos", description="Eleva moral", effect_type="promise_results")
    opt_b = BoardMessageOption(id="opt_b", text="Pedir Respaldo", description="Reduz moral levemente", effect_type="ask_backing")

    msg = BoardMessage(
        id="msg_ultimatum",
        message_type=BoardMessageType.BOARD_ULTIMATUM,
        title="Ultimato do Presidente",
        content="Reação imediata requerida.",
        options=(opt_a, opt_b),
        round_created=1,
        expires_at_round=3,
        default_option_id_on_timeout="opt_b",
    )
    state.board_inbox.add_message(msg)

    # Aplica Opção A
    user_team = next((t for t in state.season_orchestrator.championships[LeagueTier.SERIE_D].teams if t.name == "Meu Clube"), None)
    initial_morale = user_team.players[0].morale

    process_board_decision(state, "msg_ultimatum", "opt_a")

    assert state.board_inbox.get_message("msg_ultimatum").status == BoardMessageStatus.ACCEPTED
    assert user_team.players[0].morale == initial_morale + 2


def test_process_board_decision_example_2_financial_alert():
    state = make_test_game_state(user_budget=-100_000)
    opt_a = BoardMessageOption(id="opt_a", text="Congelar Prêmios", description="Congela prêmios", effect_type="freeze_bonuses")
    opt_b = BoardMessageOption(id="opt_b", text="Vender Reserva", description="Coloca reserva à venda", effect_type="sell_reserves")

    msg = BoardMessage(
        id="msg_fin",
        message_type=BoardMessageType.FINANCIAL_ALERT,
        title="Alerta Financeiro",
        content="Caixa negativo.",
        options=(opt_a, opt_b),
        round_created=1,
        expires_at_round=3,
        default_option_id_on_timeout="opt_a",
    )
    state.board_inbox.add_message(msg)

    # Aplica Opção B (Colocar Atleta Reserva no Mercado)
    user_team = next((t for t in state.season_orchestrator.championships[LeagueTier.SERIE_D].teams if t.name == "Meu Clube"), None)
    reserve = user_team.players[1]
    assert reserve.contract.is_protected is True

    process_board_decision(state, "msg_fin", "opt_b")

    reserve_updated = user_team.players[1]
    assert reserve_updated.contract.is_protected is False


def test_process_board_decision_example_3_stadium_upgrade():
    state = make_test_game_state(user_budget=5_000_000)
    opt_a = BoardMessageOption(id="opt_approve", text="Aprovar Reforma", description="Debita e expande", effect_type="approve_upgrade", param_value=2_500_000)
    opt_b = BoardMessageOption(id="opt_postpone", text="Adiar Reforma", description="Adia obra", effect_type="postpone_upgrade")

    msg = BoardMessage(
        id="msg_upgrade",
        message_type=BoardMessageType.INVESTMENT_RESPONSE,
        title="Resposta sobre o Estádio",
        content="Conselho aprovou a reforma.",
        options=(opt_a, opt_b),
        round_created=1,
        expires_at_round=4,
        default_option_id_on_timeout="opt_postpone",
    )
    state.board_inbox.add_message(msg)

    user_team = next((t for t in state.season_orchestrator.championships[LeagueTier.SERIE_D].teams if t.name == "Meu Clube"), None)
    initial_budget = user_team.budget
    initial_cap = user_team.stadium.capacity if user_team.stadium else 20000

    process_board_decision(state, "msg_upgrade", "opt_approve")

    assert user_team.budget == initial_budget - 2_500_000
    assert user_team.stadium.capacity == initial_cap + 5000


def test_decision_idempotency_prevents_duplicate_effects():
    state = make_test_game_state(user_budget=5_000_000)
    opt_a = BoardMessageOption(id="opt_approve", text="Aprovar Reforma", description="Debita R$ 2.5M", effect_type="approve_upgrade", param_value=2_500_000)

    msg = BoardMessage(
        id="msg_upgrade_dup",
        message_type=BoardMessageType.INVESTMENT_RESPONSE,
        title="Resposta sobre o Estádio",
        content="Reforma aprovada.",
        options=(opt_a,),
        round_created=1,
    )
    state.board_inbox.add_message(msg)

    user_team = next((t for t in state.season_orchestrator.championships[LeagueTier.SERIE_D].teams if t.name == "Meu Clube"), None)

    # Primeira execução: debita R$ 2.500.000
    process_board_decision(state, "msg_upgrade_dup", "opt_approve")
    assert user_team.budget == 2_500_000

    # Segunda execução (simulando reload ou chamada duplicada): NÃO deve debitar de novo
    process_board_decision(state, "msg_upgrade_dup", "opt_approve")
    assert user_team.budget == 2_500_000


def test_timeout_expiration_applies_default_option_idempotently():
    state = make_test_game_state(user_budget=-50_000, current_round=4)
    opt_a = BoardMessageOption(id="opt_a", text="Congelar Prêmios", description="Opção Padrão", effect_type="freeze_bonuses")

    msg = BoardMessage(
        id="msg_timeout_test",
        message_type=BoardMessageType.FINANCIAL_ALERT,
        title="Alerta de Saldo Negativo",
        content="Diretoria aguarda resposta.",
        options=(opt_a,),
        round_created=1,
        expires_at_round=3,  # Já expirou no round 4
        default_option_id_on_timeout="opt_a",
    )
    state.board_inbox.add_message(msg)

    # Processa mensagens expiradas da rodada
    process_round_board_messages(state)

    processed_msg = state.board_inbox.get_message("msg_timeout_test")
    assert processed_msg.status == BoardMessageStatus.EXPIRED

    # Reprocessamento não duplica efeito por causa da idempotência
    user_team = next((t for t in state.season_orchestrator.championships[LeagueTier.SERIE_D].teams if t.name == "Meu Clube"), None)
    morale_after_first = user_team.players[0].morale

    process_round_board_messages(state)
    assert user_team.players[0].morale == morale_after_first
