"""Módulo de domínio da Caixa de Entrada da Diretoria (Board Inbox) — Mensagens e Decisões."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from garfoot.domain.enums import MatchStatus
from garfoot.domain.idempotency import make_idempotency_key


class BoardMessageType(StrEnum):
    """Categorias de mensagens e comunicados da diretoria."""

    RESULTS_WARNING = "results_warning"
    FINANCIAL_ALERT = "financial_alert"
    INVESTMENT_RESPONSE = "investment_response"
    SEASON_CONGRATULATIONS = "season_congratulations"
    BOARD_ULTIMATUM = "board_ultimatum"


class BoardMessageStatus(StrEnum):
    """Estado de processamento de uma mensagem da diretoria."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    INFO_READ = "info_read"


@dataclass(frozen=True, slots=True)
class BoardMessageOption:
    """Representa uma opção de escolha do jogador em uma mensagem decisória da diretoria."""

    id: str
    text: str
    description: str
    effect_type: str  # Ex: "promise_results", "ask_backing", "freeze_bonuses", "sell_reserves", "approve_upgrade", "postpone_upgrade"
    param_value: int = 0


@dataclass(frozen=True, slots=True)
class BoardMessage:
    """Representa um comunicado oficial da diretoria com ou sem opções de decisão."""

    id: str
    message_type: BoardMessageType
    title: str
    content: str
    options: tuple[BoardMessageOption, ...] = ()
    round_created: int = 1
    expires_at_round: int | None = None
    default_option_id_on_timeout: str | None = None
    status: BoardMessageStatus = BoardMessageStatus.PENDING
    selected_option_id: str | None = None

    def is_expired(self, current_round: int) -> bool:
        """Verifica se a mensagem ultrapassou a rodada limite sem resposta."""

        if self.status != BoardMessageStatus.PENDING:
            return False
        if self.expires_at_round is None:
            return False
        return current_round > self.expires_at_round

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "message_type": str(self.message_type),
            "title": self.title,
            "content": self.content,
            "options": [
                {
                    "id": opt.id,
                    "text": opt.text,
                    "description": opt.description,
                    "effect_type": opt.effect_type,
                    "param_value": opt.param_value,
                }
                for opt in self.options
            ],
            "round_created": self.round_created,
            "expires_at_round": self.expires_at_round,
            "default_option_id_on_timeout": self.default_option_id_on_timeout,
            "status": str(self.status),
            "selected_option_id": self.selected_option_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BoardMessage:
        opts = tuple(
            BoardMessageOption(
                id=o["id"],
                text=o["text"],
                description=o["description"],
                effect_type=o["effect_type"],
                param_value=int(o.get("param_value", 0)),
            )
            for o in data.get("options", [])
            if isinstance(o, dict)
        )
        return cls(
            id=data["id"],
            message_type=BoardMessageType(data["message_type"]),
            title=data["title"],
            content=data["content"],
            options=opts,
            round_created=int(data.get("round_created", 1)),
            expires_at_round=int(data["expires_at_round"]) if data.get("expires_at_round") is not None else None,
            default_option_id_on_timeout=data.get("default_option_id_on_timeout"),
            status=BoardMessageStatus(data.get("status", BoardMessageStatus.PENDING)),
            selected_option_id=data.get("selected_option_id"),
        )


@dataclass(slots=True)
class BoardInbox:
    """Caixa de entrada da diretoria contendo o histórico de comunicados e decisões."""

    messages: list[BoardMessage] = field(default_factory=list)

    def add_message(self, message: BoardMessage) -> None:
        """Adiciona uma nova mensagem à caixa de entrada se ela ainda não existir."""

        if not any(m.id == message.id for m in self.messages):
            self.messages.insert(0, message)  # Mais recente primeiro

    def get_message(self, message_id: str) -> BoardMessage | None:
        """Busca uma mensagem pelo ID."""

        return next((m for m in self.messages if m.id == message_id), None)

    def pending_messages(self) -> list[BoardMessage]:
        """Retorna apenas as mensagens pendentes de resposta."""

        return [m for m in self.messages if m.status == BoardMessageStatus.PENDING]

    def unread_count(self) -> int:
        """Quantidade de mensagens pendentes."""

        return len(self.pending_messages())

    def update_message(self, updated_message: BoardMessage) -> None:
        """Substitui uma mensagem existente pela versão atualizada."""

        for idx, m in enumerate(self.messages):
            if m.id == updated_message.id:
                self.messages[idx] = updated_message
                break

    def to_dict(self) -> dict[str, Any]:
        return {"messages": [m.to_dict() for m in self.messages]}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> BoardInbox:
        if not data or not isinstance(data, dict):
            return cls()
        msgs = [BoardMessage.from_dict(m) for m in data.get("messages", []) if isinstance(m, dict)]
        return cls(messages=msgs)


def apply_option_effect(state: Any, user_team: Any, effect_type: str, param_value: int) -> None:
    """Aplica os efeitos puramente no estado/time do usuário."""

    if effect_type == "promise_results":
        # Eleva moral do time em +2 no otimismo imediato
        for p in user_team.players:
            p.morale = min(100, p.morale + 2)
    elif effect_type == "ask_backing":
        # Reduz moral levemente em -3, mas estabiliza ambiente
        for p in user_team.players:
            p.morale = max(1, p.morale - 3)
    elif effect_type == "freeze_bonuses":
        # Reduz moral em -5 pelo congelamento
        for p in user_team.players:
            p.morale = max(1, p.morale - 5)
    elif effect_type == "sell_reserves":
        # Coloca 1 reserva no mercado de transferências desprotegendo o contrato
        from garfoot.domain.contract import Contract
        starters = set(user_team.starting_player_names)
        if not starters:
            # Se não houver escalação explícita, considera os primeiros 11 como titulares
            starters = {p.name for p in user_team.players[:11]}
        reserves = [p for p in user_team.players if p.name not in starters]
        if not reserves and len(user_team.players) > 1:
            reserves = [user_team.players[-1]]
        if reserves:
            target = reserves[0]
            new_contract = Contract(
                years_remaining=target.contract.years_remaining,
                is_protected=False,
                protection_years=0,
                release_clause=target.contract.release_clause,
            )
            target.contract = new_contract
    elif effect_type == "approve_upgrade":
        # Debita o valor do upgrade do estádio
        cost = param_value if param_value > 0 else 2_500_000
        user_team.budget -= cost
        if user_team.stadium:
            user_team.stadium.capacity += 5000
        else:
            from garfoot.domain.stadium import Stadium
            user_team.stadium = Stadium(name="Estádio do Clube", city=user_team.city, capacity=25000)
    elif effect_type == "postpone_upgrade":
        pass  # Sem custo nem efeito financeiro


def process_board_decision(
    state: Any,
    message_id: str,
    option_id: str,
) -> Any:
    """Aplica a decisão tomada pelo jogador com idempotência garantida por IdempotencyLedger."""

    msg = state.board_inbox.get_message(message_id)
    if not msg or msg.status != BoardMessageStatus.PENDING:
        return state

    selected_option = next((opt for opt in msg.options if opt.id == option_id), None)
    if not selected_option:
        return state

    # Validação e marcação no Ledger de Idempotência
    key = make_idempotency_key("board-decision", message_id, option_id)
    if not state.idempotency_ledger.check_and_mark(key):
        return state

    # Localiza time do usuário
    user_team = None
    from garfoot.domain.season import LeagueTier
    for champ in state.season_orchestrator.championships.values():
        t = next((team for team in champ.teams if team.name == state.player_team_name), None)
        if t:
            user_team = t
            break

    if user_team:
        apply_option_effect(state, user_team, selected_option.effect_type, selected_option.param_value)

    # Atualiza status da mensagem
    new_status = BoardMessageStatus.ACCEPTED if option_id in ("opt_a", "opt_approve", "opt_promise") else BoardMessageStatus.REJECTED
    updated_msg = BoardMessage(
        id=msg.id,
        message_type=msg.message_type,
        title=msg.title,
        content=msg.content,
        options=msg.options,
        round_created=msg.round_created,
        expires_at_round=msg.expires_at_round,
        default_option_id_on_timeout=msg.default_option_id_on_timeout,
        status=new_status,
        selected_option_id=option_id,
    )
    state.board_inbox.update_message(updated_msg)
    return state


def process_round_board_messages(state: Any) -> Any:
    """Resolve comunicados expirados e avalia novos comunicados ao fim de cada rodada."""

    curr_round = state.current_round

    # 1. Resolve Timeouts em mensagens expiradas
    for msg in list(state.board_inbox.pending_messages()):
        if msg.is_expired(curr_round):
            timeout_opt_id = msg.default_option_id_on_timeout
            if timeout_opt_id:
                # Aplica a opção padrão por timeout de forma idempotente
                process_board_decision(state, msg.id, timeout_opt_id)

            # Garante que a mensagem fique marcada como expirada
            expired_msg = state.board_inbox.get_message(msg.id)
            if expired_msg and expired_msg.status != BoardMessageStatus.EXPIRED:
                state.board_inbox.update_message(
                    BoardMessage(
                        id=expired_msg.id,
                        message_type=expired_msg.message_type,
                        title=expired_msg.title,
                        content=expired_msg.content,
                        options=expired_msg.options,
                        round_created=expired_msg.round_created,
                        expires_at_round=expired_msg.expires_at_round,
                        default_option_id_on_timeout=expired_msg.default_option_id_on_timeout,
                        status=BoardMessageStatus.EXPIRED,
                        selected_option_id=expired_msg.selected_option_id,
                    )
                )

    # 2. Avalia gatilhos de novas mensagens
    user_team = None
    for champ in state.season_orchestrator.championships.values():
        t = next((team for team in champ.teams if team.name == state.player_team_name), None)
        if t:
            user_team = t
            break

    if not user_team:
        return state

    # Gatilho A: Alerta de Estresse Financeiro (saldo negativo por 3 rodadas consecutivas)
    if user_team.budget < 0:
        msg_id = f"board_fin_neg_r{curr_round}"
        if not state.board_inbox.get_message(msg_id):
            opt_a = BoardMessageOption(id="opt_a", text="Congelar Prêmios/Bicho", description="Economiza despesas, mas reduz moral do elenco em -5.", effect_type="freeze_bonuses")
            opt_b = BoardMessageOption(id="opt_b", text="Colocar Atleta no Mercado", description="Mantém estrutura e disponibiliza 1 reserva para venda.", effect_type="sell_reserves")
            msg = BoardMessage(
                id=msg_id,
                message_type=BoardMessageType.FINANCIAL_ALERT,
                title="ALERTA: Saldo Negativo em Caixa",
                content=f"Prezado Gestor, o saldo do {user_team.name} está negativo (R$ {user_team.budget:,}). A diretoria exige uma medida de contenção.",
                options=(opt_a, opt_b),
                round_created=curr_round,
                expires_at_round=curr_round + 2,
                default_option_id_on_timeout="opt_a",
            )
            state.board_inbox.add_message(msg)

    # Gatilho B: Parabenização por Título/Excelente Desempenho ao fim da temporada (rodada 38)
    if curr_round == 38:
        msg_id = f"board_congratulations_s{state.current_season}"
        if not state.board_inbox.get_message(msg_id):
            opt_ok = BoardMessageOption(id="opt_a", text="Agradecer Confiança", description="Recebe o reconhecimento da diretoria.", effect_type="promise_results")
            msg = BoardMessage(
                id=msg_id,
                message_type=BoardMessageType.SEASON_CONGRATULATIONS,
                title="CONGRATULAÇÕES: Encerramento de Temporada",
                content=f"Parabéns pelo trabalho à frente do {user_team.name} na temporada de {state.current_season}! A diretoria renova sua confiança para os próximos desafios.",
                options=(opt_ok,),
                round_created=curr_round,
                expires_at_round=None,
                default_option_id_on_timeout="opt_a",
            )
            state.board_inbox.add_message(msg)

    return state
