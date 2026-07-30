"""Modelo de time e regras basicas de elenco."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from garfoot.domain.coach import Coach, CoachBounceEffect
from garfoot.domain.player import Player
from garfoot.domain.stadium import Stadium


@dataclass(frozen=True, slots=True)
class Formation:
    """Formacao tática simples: defensores, meias e atacantes.

    O goleiro e implicito, portanto uma formacao 4-4-2 representa 10 jogadores
    de linha mais 1 goleiro.
    """

    defenders: int
    midfielders: int
    forwards: int

    def __post_init__(self) -> None:
        if self.defenders + self.midfielders + self.forwards != 10:
            raise ValueError("A formacao deve somar 10 jogadores de linha.")
        if min(self.defenders, self.midfielders, self.forwards) < 1:
            raise ValueError("A formacao precisa ter defensores, meias e atacantes.")

    @property
    def label(self) -> str:
        return f"{self.defenders}-{self.midfielders}-{self.forwards}"


@dataclass(slots=True)
class Team:
    """Representa um clube controlavel ou adversario."""

    name: str
    city: str
    budget: int
    players: list[Player] = field(default_factory=list)
    formation: Formation = field(default_factory=lambda: Formation(4, 4, 2))
    starting_player_names: list[str] = field(default_factory=list)
    stadium: Stadium | None = None
    coach: Coach | None = None
    bounce_effect: CoachBounceEffect | None = None
    recent_results: list[str] = field(default_factory=list)
    financial_profile: Any | None = None
    sponsorships: Any = field(default_factory=lambda: None)
    operating_expenses: Any = field(default_factory=lambda: None)
    financial_state: Any = field(default_factory=lambda: None)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.city = self.city.strip()
        if not self.name:
            raise ValueError("O time precisa ter nome.")
        if self.sponsorships is None:
            from garfoot.domain.sponsorship import ClubSponsorshipPortfolio
            self.sponsorships = ClubSponsorshipPortfolio()
        if self.operating_expenses is None:
            from garfoot.domain.operating_expenses import ClubOperatingExpenseProfile
            self.operating_expenses = ClubOperatingExpenseProfile()
        if self.financial_state is None:
            from garfoot.domain.financial_health import ClubFinancialState
            self.financial_state = ClubFinancialState()

    @property
    def squad_strength(self) -> int:
        """Media de forca dos 11 melhores jogadores disponiveis."""

        if not self.players:
            return 0
        best = sorted(self.players, key=lambda player: player.overall, reverse=True)[:11]
        return round(sum(player.overall for player in best) / len(best))

    def add_player(self, player: Player) -> None:
        if self.find_player(player.name) is not None:
            raise ValueError(f"{player.name} ja pertence ao elenco.")
        self.players.append(player)

    def remove_player(self, player_name: str) -> Player:
        for index, player in enumerate(self.players):
            if player.name == player_name:
                self.starting_player_names = [
                    name for name in self.starting_player_names if name != player_name
                ]
                return self.players.pop(index)
        raise ValueError(f"Jogador nao encontrado: {player_name}.")

    def buy_player(self, player: Player) -> None:
        if self.budget < player.value:
            raise ValueError(f"Orcamento insuficiente para contratar {player.name}.")
        self.budget -= player.value
        self.add_player(player)

    def sell_player(self, player_name: str) -> Player:
        player = self.remove_player(player_name)
        self.budget += player.value
        return player

    def average_morale(self) -> int:
        """Calcula a moral media ponderada do elenco, considerando o efeito de chicotada psicologica."""

        if not self.players:
            return 50
        base_morale = round(sum(player.morale for player in self.players) / len(self.players))
        if self.bounce_effect is not None and self.bounce_effect.is_active:
            base_morale = min(100, base_morale + self.bounce_effect.morale_bonus)
        return base_morale

    def estimate_match_income(self, performance: float = 1.0, appeal_context: Any | None = None) -> int:
        """Estima a receita bruta de bilheteria para um jogo de mando deste clube."""

        if self.stadium is None:
            return 0
        return self.stadium.estimate_match_income(self.average_morale(), performance, appeal_context=appeal_context)

    def estimate_home_income(self, performance: float = 0.5, appeal_context: Any | None = None) -> int:
        """Estima a receita de bilheteria em jogos de mando."""

        return self.estimate_match_income(performance, appeal_context=appeal_context)

    def set_starting_lineup(self, player_names: list[str]) -> None:
        if len(player_names) != 11:
            raise ValueError("A escalacao titular deve ter exatamente 11 jogadores.")
        if len(set(player_names)) != 11:
            raise ValueError("A escalacao titular nao pode repetir jogadores.")

        squad_names = {player.name for player in self.players}
        missing = [name for name in player_names if name not in squad_names]
        if missing:
            raise ValueError(f"Jogadores fora do elenco: {', '.join(missing)}.")

        self.starting_player_names = list(player_names)

    def find_player(self, player_name: str) -> Player | None:
        return next((player for player in self.players if player.name == player_name), None)

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["players"] = [player.to_dict() for player in self.players]
        data["formation"] = asdict(self.formation)
        data["stadium"] = self.stadium.to_dict() if self.stadium is not None else None
        data["coach"] = self.coach.to_dict() if self.coach is not None else None
        data["bounce_effect"] = self.bounce_effect.to_dict() if self.bounce_effect is not None else None
        data["recent_results"] = list(self.recent_results)
        data["financial_profile"] = (
            self.financial_profile.value
            if hasattr(self.financial_profile, "value")
            else self.financial_profile
        )
        data["sponsorships"] = (
            self.sponsorships.to_dict()
            if hasattr(self.sponsorships, "to_dict")
            else None
        )
        data["operating_expenses"] = (
            self.operating_expenses.to_dict()
            if hasattr(self.operating_expenses, "to_dict")
            else None
        )
        data["financial_state"] = (
            self.financial_state.to_dict()
            if hasattr(self.financial_state, "to_dict")
            else None
        )
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Team":
        payload = dict(data)
        payload["players"] = [
            Player.from_dict(player_data)
            for player_data in payload.get("players", [])
        ]
        payload["formation"] = Formation(**payload.get("formation", {}))
        stadium_data = payload.get("stadium")
        payload["stadium"] = (
            Stadium.from_dict(stadium_data)
            if isinstance(stadium_data, dict)
            else None
        )
        coach_data = payload.get("coach")
        payload["coach"] = (
            Coach.from_dict(coach_data)
            if isinstance(coach_data, dict)
            else None
        )
        bounce_data = payload.get("bounce_effect")
        payload["bounce_effect"] = (
            CoachBounceEffect.from_dict(bounce_data)
            if isinstance(bounce_data, dict)
            else None
        )
        payload["recent_results"] = list(payload.get("recent_results", []))

        raw_prof = payload.get("financial_profile")
        if raw_prof:
            from garfoot.domain.club_finance import ClubFinancialProfile
            try:
                payload["financial_profile"] = ClubFinancialProfile(str(raw_prof))
            except ValueError:
                payload["financial_profile"] = None
        else:
            payload["financial_profile"] = None

        from garfoot.domain.sponsorship import ClubSponsorshipPortfolio
        spons_data = payload.get("sponsorships")
        payload["sponsorships"] = (
            ClubSponsorshipPortfolio.from_dict(spons_data)
            if isinstance(spons_data, dict)
            else ClubSponsorshipPortfolio()
        )

        from garfoot.domain.operating_expenses import ClubOperatingExpenseProfile
        exp_data = payload.get("operating_expenses")
        payload["operating_expenses"] = (
            ClubOperatingExpenseProfile.from_dict(exp_data)
            if isinstance(exp_data, dict)
            else ClubOperatingExpenseProfile()
        )

        from garfoot.domain.financial_health import ClubFinancialState
        fin_state_data = payload.get("financial_state")
        payload["financial_state"] = (
            ClubFinancialState.from_dict(fin_state_data)
            if isinstance(fin_state_data, dict)
            else ClubFinancialState()
        )

        return cls(**payload)  # type: ignore[arg-type]
