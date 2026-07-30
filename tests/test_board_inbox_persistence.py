"""Testes de persistência em save/load para a Caixa de Entrada da Diretoria (Board Inbox)."""

from __future__ import annotations

from garfoot.domain.board_inbox import (
    BoardMessage,
    BoardMessageOption,
    BoardMessageStatus,
    BoardMessageType,
)
from garfoot.domain.game_state import GameState
from garfoot.persistence.save_manager import SaveManager
from tests.test_board_inbox import make_test_game_state


def test_board_inbox_persistence_save_and_load(tmp_path):
    save_mgr = SaveManager(save_dir=tmp_path)
    state = make_test_game_state(user_budget=2_000_000, current_round=3)

    opt_a = BoardMessageOption(id="opt_a", text="Opção 1", description="Desc 1", effect_type="promise_results")
    msg1 = BoardMessage(
        id="board_msg_save_test",
        message_type=BoardMessageType.RESULTS_WARNING,
        title="Cobrança de Desempenho",
        content="Comunicado importante.",
        options=(opt_a,),
        round_created=2,
        expires_at_round=5,
        default_option_id_on_timeout="opt_a",
        status=BoardMessageStatus.PENDING,
    )
    state.board_inbox.add_message(msg1)

    # Marca idempotência no ledger
    state.idempotency_ledger.mark("board-decision:board_msg_save_test:opt_a")

    # Salva no disco
    filepath = save_mgr.save_game(state, filename="test_board_save.json")
    assert filepath.exists()

    # Recarrega do disco
    loaded_state = save_mgr.load_game(filepath)

    assert loaded_state.save_name == state.save_name
    assert loaded_state.current_round == 3
    assert len(loaded_state.board_inbox.messages) == 1

    loaded_msg = loaded_state.board_inbox.get_message("board_msg_save_test")
    assert loaded_msg is not None
    assert loaded_msg.title == "Cobrança de Desempenho"
    assert loaded_msg.message_type == BoardMessageType.RESULTS_WARNING
    assert loaded_msg.status == BoardMessageStatus.PENDING
    assert loaded_state.idempotency_ledger.has("board-decision:board_msg_save_test:opt_a")
