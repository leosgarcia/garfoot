"""Modelo de estado global do jogo (GameState) para serialização e persistência."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from garfoot.domain.board_inbox import BoardInbox
from garfoot.domain.economic_context import EconomicContext
from garfoot.domain.game_settings import GameSettings
from garfoot.domain.idempotency import IdempotencyLedger
from garfoot.domain.news import NewsCenter
from garfoot.domain.player import Player
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.domain.statistics import SeasonStatisticsManager


@dataclass(frozen=True, slots=True)
class SaveMetadata:
    """Metadados curtos para exibição em listas de saves sem carregar todo o estado."""

    save_name: str
    player_team_name: str
    season_year: int
    current_round: int
    saved_at: str
    filepath: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "save_name": self.save_name,
            "player_team_name": self.player_team_name,
            "season_year": self.season_year,
            "current_round": self.current_round,
            "saved_at": self.saved_at,
            "filepath": self.filepath,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SaveMetadata:
        return cls(
            save_name=data["save_name"],
            player_team_name=data["player_team_name"],
            season_year=int(data["season_year"]),
            current_round=int(data["current_round"]),
            saved_at=data["saved_at"],
            filepath=data.get("filepath", ""),
        )


@dataclass(slots=True)
class GameState:
    """Representa o estado completo do jogo em um dado momento."""

    save_name: str
    player_team_name: str
    current_season: int
    current_round: int
    season_orchestrator: SeasonOrchestrator
    saved_at: str = ""
    settings: GameSettings = field(default_factory=GameSettings)
    statistics: SeasonStatisticsManager = field(default_factory=SeasonStatisticsManager)
    economic_context: EconomicContext = field(default_factory=EconomicContext)
    free_agents: list[Player] = field(default_factory=list)
    news_center: NewsCenter = field(default_factory=NewsCenter)
    board_inbox: BoardInbox = field(default_factory=BoardInbox)
    idempotency_ledger: IdempotencyLedger = field(default_factory=IdempotencyLedger)

    def __post_init__(self) -> None:
        self.save_name = self.save_name.strip()
        self.player_team_name = self.player_team_name.strip()
        if not self.save_name:
            raise ValueError("O nome do save não pode ser vazio.")
        if not self.player_team_name:
            raise ValueError("O nome do time do jogador não pode ser vazio.")

    def get_metadata(self, filepath: str = "") -> SaveMetadata:
        """Gera metadados resumidos a partir deste GameState."""

        return SaveMetadata(
            save_name=self.save_name,
            player_team_name=self.player_team_name,
            season_year=self.current_season,
            current_round=self.current_round,
            saved_at=self.saved_at,
            filepath=filepath,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "save_name": self.save_name,
            "player_team_name": self.player_team_name,
            "current_season": self.current_season,
            "current_round": self.current_round,
            "season_orchestrator": self.season_orchestrator.to_dict(),
            "saved_at": self.saved_at,
            "settings": self.settings.to_dict(),
            "statistics": self.statistics.to_dict(),
            "economic_context": self.economic_context.to_dict(),
            "free_agents": [p.to_dict() for p in self.free_agents],
            "news_center": self.news_center.to_dict(),
            "board_inbox": self.board_inbox.to_dict(),
            "idempotency_ledger": self.idempotency_ledger.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameState:
        orchestrator = SeasonOrchestrator.from_dict(data["season_orchestrator"])
        settings = GameSettings.from_dict(data.get("settings"))
        statistics = SeasonStatisticsManager.from_dict(data.get("statistics"))
        econ_context = EconomicContext.from_dict(data.get("economic_context"))
        free_agents = [Player.from_dict(p) for p in data.get("free_agents", []) if isinstance(p, dict)]
        news_center = NewsCenter.from_dict(data.get("news_center"))
        board_inbox = BoardInbox.from_dict(data.get("board_inbox"))
        ledger = IdempotencyLedger.from_dict(data.get("idempotency_ledger"))
        return cls(
            save_name=data["save_name"],
            player_team_name=data["player_team_name"],
            current_season=int(data["current_season"]),
            current_round=int(data["current_round"]),
            season_orchestrator=orchestrator,
            saved_at=data.get("saved_at", ""),
            settings=settings,
            statistics=statistics,
            economic_context=econ_context,
            free_agents=free_agents,
            news_center=news_center,
            board_inbox=board_inbox,
            idempotency_ledger=ledger,
        )
