"""Centro de notícias e eventos da temporada — modelo puro e serializável."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class NewsCategory(StrEnum):
    """Categorias de notícias e eventos da temporada."""

    TRANSFER = "transfer"
    CONTRACT = "contract"
    INJURY = "injury"
    FINANCE = "finance"
    SPONSORSHIP = "sponsorship"
    COACH = "coach"
    MATCH = "match"
    AWARD = "award"
    RANKING = "ranking"
    STADIUM = "stadium"
    SYSTEM = "system"


class NewsPriority(StrEnum):
    """Nível de prioridade/severidade de uma notícia."""

    LOW = "low"
    NORMAL = "normal"
    IMPORTANT = "important"
    URGENT = "urgent"


# Mapeamento visual de categorias para o estilo retrô
CATEGORY_LABEL: dict[NewsCategory, str] = {
    NewsCategory.TRANSFER: "TRANSF.",
    NewsCategory.CONTRACT: "CONTRATO",
    NewsCategory.INJURY: "LESÃO",
    NewsCategory.FINANCE: "FINANÇAS",
    NewsCategory.SPONSORSHIP: "PATROC.",
    NewsCategory.COACH: "TÉCNICO",
    NewsCategory.MATCH: "PARTIDA",
    NewsCategory.AWARD: "PRÊMIO",
    NewsCategory.RANKING: "RANKING",
    NewsCategory.STADIUM: "ESTÁDIO",
    NewsCategory.SYSTEM: "SISTEMA",
}

PRIORITY_LABEL: dict[NewsPriority, str] = {
    NewsPriority.LOW: "",
    NewsPriority.NORMAL: "",
    NewsPriority.IMPORTANT: "[!]",
    NewsPriority.URGENT: "[!!!]",
}

_NEWS_COUNTER: int = 0  # Contador de sequência para IDs determinísticos


def make_news_id(
    season_year: int,
    round_number: int | None,
    category: NewsCategory,
    sequence: int,
) -> str:
    """Gera um ID estável e determinístico para uma notícia."""

    rnd = round_number if round_number is not None else 0
    return f"{season_year}-R{rnd:02d}-{category.value}-{sequence:04d}"


@dataclass(frozen=True, slots=True)
class NewsItem:
    """Representa um item de notícia/evento da temporada."""

    id: str
    season_year: int
    round_number: int | None
    category: NewsCategory
    priority: NewsPriority
    title: str
    message: str
    team_name: str | None = None
    related_team_name: str | None = None
    player_name: str | None = None
    coach_name: str | None = None
    amount: int | None = None
    is_read: bool = False

    @property
    def priority_label(self) -> str:
        return PRIORITY_LABEL.get(self.priority, "")

    @property
    def category_label(self) -> str:
        return CATEGORY_LABEL.get(self.category, self.category.value.upper())

    @property
    def round_tag(self) -> str:
        return f"R{self.round_number:02d}" if self.round_number is not None else "---"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "season_year": self.season_year,
            "round_number": self.round_number,
            "category": str(self.category),
            "priority": str(self.priority),
            "title": self.title,
            "message": self.message,
            "team_name": self.team_name,
            "related_team_name": self.related_team_name,
            "player_name": self.player_name,
            "coach_name": self.coach_name,
            "amount": self.amount,
            "is_read": self.is_read,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NewsItem:
        return cls(
            id=str(data["id"]),
            season_year=int(data["season_year"]),
            round_number=data.get("round_number"),
            category=NewsCategory(str(data["category"])),
            priority=NewsPriority(str(data["priority"])),
            title=str(data["title"]),
            message=str(data["message"]),
            team_name=data.get("team_name"),
            related_team_name=data.get("related_team_name"),
            player_name=data.get("player_name"),
            coach_name=data.get("coach_name"),
            amount=data.get("amount"),
            is_read=bool(data.get("is_read", False)),
        )


@dataclass(slots=True)
class NewsCenter:
    """Centro de notícias e eventos da temporada. Contém histórico filtrável."""

    items: list[NewsItem] = field(default_factory=list)
    _sequence: int = field(default=0, repr=False)

    def _next_id(
        self,
        season_year: int,
        round_number: int | None,
        category: NewsCategory,
    ) -> str:
        self._sequence += 1
        return make_news_id(season_year, round_number, category, self._sequence)

    def add(self, item: NewsItem) -> None:
        """Adiciona um item ao centro de notícias."""
        self.items.append(item)

    def create_and_add(
        self,
        season_year: int,
        round_number: int | None,
        category: NewsCategory,
        priority: NewsPriority,
        title: str,
        message: str,
        *,
        team_name: str | None = None,
        related_team_name: str | None = None,
        player_name: str | None = None,
        coach_name: str | None = None,
        amount: int | None = None,
        idempotency_key: str | None = None,
        ledger: Any | None = None,
    ) -> NewsItem | None:
        """Cria e registra uma notícia de forma opcionalmente idempotente via ledger."""

        if idempotency_key and ledger is not None and hasattr(ledger, "check_and_mark"):
            if not ledger.check_and_mark(idempotency_key):
                return None

        item = NewsItem(
            id=self._next_id(season_year, round_number, category),
            season_year=season_year,
            round_number=round_number,
            category=category,
            priority=priority,
            title=title,
            message=message,
            team_name=team_name,
            related_team_name=related_team_name,
            player_name=player_name,
            coach_name=coach_name,
            amount=amount,
        )
        self.add(item)
        return item

    def latest(self, limit: int = 10) -> list[NewsItem]:
        """Retorna as últimas notícias em ordem cronológica inversa."""
        return list(reversed(self.items[-limit * 2:]))[:limit]

    def unread(self) -> list[NewsItem]:
        """Retorna todas as notícias ainda não lidas."""
        return [item for item in self.items if not item.is_read]

    def by_category(self, category: NewsCategory, limit: int = 20) -> list[NewsItem]:
        """Retorna notícias filtradas por categoria (mais recentes primeiro)."""
        filtered = [item for item in reversed(self.items) if item.category == category]
        return filtered[:limit]

    def for_team(self, team_name: str, limit: int = 20) -> list[NewsItem]:
        """Retorna notícias relacionadas a um time específico (mais recentes primeiro)."""
        filtered = [
            item for item in reversed(self.items)
            if item.team_name == team_name or item.related_team_name == team_name
        ]
        return filtered[:limit]

    def unread_count(self) -> int:
        """Número de notícias não lidas."""
        return sum(1 for item in self.items if not item.is_read)

    def mark_all_read(self) -> None:
        """Marca todas as notícias como lidas (cria novos objetos imutáveis)."""
        from dataclasses import replace
        self.items = [replace(item, is_read=True) for item in self.items]

    def prune(self, max_items: int = 300, current_season: int | None = None) -> None:
        """Remove notícias antigas de baixa prioridade para limitar o save.

        Regras:
        - Nunca remove notícias URGENT da temporada atual.
        - Remove da cabeça (mais antigas) quando acima do limite.
        """
        self.items = prune_news_items(self.items, max_items, current_season)

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "sequence": self._sequence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> NewsCenter:
        """Desserialização retrocompatível — saves antigos carregam com centro vazio."""

        if not data or not isinstance(data, dict):
            return cls()
        items = [
            NewsItem.from_dict(i)
            for i in data.get("items", [])
            if isinstance(i, dict)
        ]
        return cls(items=items, _sequence=int(data.get("sequence", len(items))))


# ---------------------------------------------------------------------------
# Funções puras de manutenção e relevância
# ---------------------------------------------------------------------------


def prune_news_items(
    items: list[NewsItem],
    max_items: int = 300,
    current_season: int | None = None,
) -> list[NewsItem]:
    """Remove notícias antigas de baixa prioridade para manter o save compacto.

    - Preserva todas as notícias URGENT da temporada atual.
    - Remove primeiro as mais antigas com prioridade LOW, depois NORMAL.
    """

    if len(items) <= max_items:
        return items

    protected: list[NewsItem] = []
    removable: list[NewsItem] = []

    for item in items:
        if current_season and item.season_year == current_season and item.priority == NewsPriority.URGENT:
            protected.append(item)
        else:
            removable.append(item)

    # Ordena removíveis para eliminar os mais antigos e menos prioritários
    priority_order = {
        NewsPriority.LOW: 0,
        NewsPriority.NORMAL: 1,
        NewsPriority.IMPORTANT: 2,
        NewsPriority.URGENT: 3,
    }
    removable.sort(key=lambda i: (priority_order[i.priority], i.season_year, i.round_number or 0))

    keep_count = max(0, max_items - len(protected))
    kept_removable = removable[-keep_count:] if keep_count > 0 else []

    merged = protected + kept_removable
    merged.sort(key=lambda i: (i.season_year, i.round_number or 0))
    return merged


# ---------------------------------------------------------------------------
# Funções fábrica puras (criam NewsItem sem alterar estado)
# ---------------------------------------------------------------------------


def create_news_item(
    season_year: int,
    round_number: int | None,
    category: NewsCategory,
    priority: NewsPriority,
    title: str,
    message: str,
    sequence: int = 0,
    **metadata: Any,
) -> NewsItem:
    """Cria um NewsItem puro sem registrá-lo no NewsCenter."""

    return NewsItem(
        id=make_news_id(season_year, round_number, category, sequence),
        season_year=season_year,
        round_number=round_number,
        category=category,
        priority=priority,
        title=title,
        message=message,
        team_name=metadata.get("team_name"),
        related_team_name=metadata.get("related_team_name"),
        player_name=metadata.get("player_name"),
        coach_name=metadata.get("coach_name"),
        amount=metadata.get("amount"),
    )


def create_transfer_news(
    season_year: int,
    round_number: int | None,
    buyer_team: str,
    player_name: str,
    seller_team: str | None,
    amount: int,
    sequence: int = 0,
    is_release_clause: bool = False,
    is_free_agent: bool = False,
) -> NewsItem:
    """Gera notícia de transferência."""

    if is_free_agent:
        title = f"{buyer_team} contrata agente livre"
        message = f"{player_name} se juntou ao {buyer_team} sem custo de transferência."
        priority = NewsPriority.NORMAL
    elif is_release_clause:
        title = "Cláusula rescisória ativada"
        seller_str = f" do {seller_team}" if seller_team else ""
        message = f"{buyer_team} pagou R$ {amount:,} pela cláusula de {player_name}{seller_str}."
        priority = NewsPriority.IMPORTANT
    else:
        title = f"{buyer_team} anuncia {player_name}"
        seller_str = f" do {seller_team}" if seller_team else ""
        message = f"O jogador {player_name} chegou{seller_str} por R$ {amount:,}."
        priority = NewsPriority.IMPORTANT if amount >= 500_000 else NewsPriority.NORMAL

    return create_news_item(
        season_year, round_number, NewsCategory.TRANSFER, priority, title, message,
        sequence=sequence, team_name=buyer_team, related_team_name=seller_team,
        player_name=player_name, amount=amount,
    )


def create_contract_news(
    season_year: int,
    round_number: int | None,
    team_name: str,
    player_name: str,
    years: int,
    action: str = "renew",
    sequence: int = 0,
) -> NewsItem:
    """Gera notícia de contrato (renovação, expiração ou liberação)."""

    if action == "renew":
        title = "Renovação confirmada"
        message = f"{player_name} renovou com o {team_name} por mais {years} temporada(s)."
        priority = NewsPriority.NORMAL
    elif action == "expire":
        title = "Contrato encerrado"
        message = f"{player_name} deixa o {team_name} com o contrato expirado."
        priority = NewsPriority.NORMAL
    else:  # free
        title = "Jogador livre no mercado"
        message = f"{player_name} está disponível como agente livre após deixar o {team_name}."
        priority = NewsPriority.NORMAL

    return create_news_item(
        season_year, round_number, NewsCategory.CONTRACT, priority, title, message,
        sequence=sequence, team_name=team_name, player_name=player_name,
    )


def create_injury_news(
    season_year: int,
    round_number: int | None,
    team_name: str,
    player_name: str,
    rounds_out: int,
    sequence: int = 0,
) -> NewsItem:
    """Gera notícia de lesão (apenas moderada ou grave)."""

    if rounds_out >= 6:
        title = "Baixa importante"
        priority = NewsPriority.IMPORTANT
        message = f"{player_name} sofreu lesão grave e ficará fora por {rounds_out} rodadas."
    else:
        title = "Jogador lesionado"
        priority = NewsPriority.NORMAL
        message = f"{player_name} se lesionou e ficará fora por {rounds_out} rodadas."

    return create_news_item(
        season_year, round_number, NewsCategory.INJURY, priority, title, message,
        sequence=sequence, team_name=team_name, player_name=player_name,
    )


def create_financial_news(
    season_year: int,
    round_number: int | None,
    team_name: str,
    status: str,
    detail: str,
    sequence: int = 0,
) -> NewsItem:
    """Gera notícia financeira com prioridade baseada no status."""

    urgent_statuses = ("crisis", "insolvent", "crise", "insolvente", "negativo")
    priority = (
        NewsPriority.URGENT
        if any(s in status.lower() for s in urgent_statuses)
        else NewsPriority.IMPORTANT
    )

    title_map = {
        "crisis": "Alerta de crise financeira",
        "crise": "Alerta de crise financeira",
        "insolvent": "Clube insolvente",
        "insolvente": "Clube insolvente",
        "negative": "Orçamento negativo",
        "negativo": "Orçamento negativo",
        "loan": "Empréstimo bancário",
        "emprestimo": "Empréstimo bancário",
        "restriction": "Restrição de mercado",
        "restricao": "Restrição de mercado",
    }
    title = next(
        (v for k, v in title_map.items() if k in status.lower()),
        "Notícia financeira",
    )

    return create_news_item(
        season_year, round_number, NewsCategory.FINANCE, priority, title, detail,
        sequence=sequence, team_name=team_name,
    )


def create_coach_news(
    season_year: int,
    round_number: int | None,
    team_name: str,
    coach_name: str,
    action: str,
    sequence: int = 0,
) -> NewsItem:
    """Gera notícia de técnico (demissão, contratação, chicotada)."""

    action_lower = action.lower()
    if "demit" in action_lower or "fired" in action_lower:
        title = "Troca no comando técnico"
        message = f"{coach_name} foi demitido do {team_name}."
        priority = NewsPriority.IMPORTANT
    elif "contrat" in action_lower or "hired" in action_lower:
        title = "Novo treinador"
        message = f"{coach_name} é o novo técnico do {team_name}."
        priority = NewsPriority.NORMAL
    else:
        title = "Chicotada psicológica"
        message = f"{coach_name} aplicou chicotada para motivar o elenco do {team_name}."
        priority = NewsPriority.NORMAL

    return create_news_item(
        season_year, round_number, NewsCategory.COACH, priority, title, message,
        sequence=sequence, team_name=team_name, coach_name=coach_name,
    )


def create_match_news(
    season_year: int,
    round_number: int | None,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    is_final: bool = False,
    is_classic: bool = False,
    sequence: int = 0,
) -> NewsItem:
    """Gera notícia de partida (goleada, clássico, final, título)."""

    score_diff = abs(home_score - away_score)
    total_goals = home_score + away_score

    if is_final:
        title = "Grande Final"
        priority = NewsPriority.URGENT
    elif is_classic and total_goals >= 4:
        title = "Clássico emocionante"
        priority = NewsPriority.IMPORTANT
    elif is_classic:
        title = "Clássico disputado"
        priority = NewsPriority.NORMAL
    elif score_diff >= 4:
        title = "Goleada"
        priority = NewsPriority.IMPORTANT
    else:
        title = "Resultado do jogo"
        priority = NewsPriority.NORMAL

    message = f"{home_team} {home_score} x {away_score} {away_team}."

    return create_news_item(
        season_year, round_number, NewsCategory.MATCH, priority, title, message,
        sequence=sequence, team_name=home_team, related_team_name=away_team,
    )


def create_award_news(
    season_year: int,
    round_number: int | None,
    team_name: str,
    title: str,
    message: str,
    player_name: str | None = None,
    amount: int | None = None,
    sequence: int = 0,
) -> NewsItem:
    """Gera notícia de premiação (campeão, artilheiro, vice, etc.)."""

    return create_news_item(
        season_year, round_number, NewsCategory.AWARD, NewsPriority.IMPORTANT,
        title, message,
        sequence=sequence, team_name=team_name, player_name=player_name, amount=amount,
    )


def create_stadium_news(
    season_year: int,
    round_number: int | None,
    team_name: str,
    action: str,
    detail: str,
    sequence: int = 0,
) -> NewsItem:
    """Gera notícia de estádio (obra, conclusão, bloqueio)."""

    action_lower = action.lower()
    if "conclu" in action_lower or "finish" in action_lower:
        priority = NewsPriority.IMPORTANT
    elif "bloquei" in action_lower or "block" in action_lower:
        priority = NewsPriority.IMPORTANT
    else:
        priority = NewsPriority.NORMAL

    return create_news_item(
        season_year, round_number, NewsCategory.STADIUM, priority, action, detail,
        sequence=sequence, team_name=team_name,
    )
