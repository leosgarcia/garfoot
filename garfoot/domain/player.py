"""Modelo de jogador."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from garfoot.domain.contract import Contract
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.injury import Injury

MIN_ATTRIBUTE = 1
MAX_ATTRIBUTE = 100


@dataclass(slots=True)
class Player:
    """Representa um jogador do elenco.

    Os atributos usam escala 1-100 para facilitar simulacao, exibicao e
    balanceamento. A primeira versao evita granularidade excessiva: ataque,
    defesa, forma fisica e moral ja bastam para gerar diferencas de elenco.
    """

    name: str
    age: int
    position: PlayerPosition
    attack: int
    defense: int
    fitness: int
    morale: int
    value: int = 0
    salary: int = 0
    contract: Contract = field(default_factory=Contract)
    injury: Injury | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("O jogador precisa ter nome.")
        if self.age < 15 or self.age > 50:
            raise ValueError("A idade do jogador deve ficar entre 15 e 50.")
        if self.value < 0:
            raise ValueError("O valor de mercado nao pode ser negativo.")
        if self.salary < 0:
            raise ValueError("O salario nao pode ser negativo.")

        for field_name in ("attack", "defense", "fitness", "morale"):
            val = getattr(self, field_name)
            if val < MIN_ATTRIBUTE or val > MAX_ATTRIBUTE:
                raise ValueError(
                    f"{field_name} deve ficar entre {MIN_ATTRIBUTE} e {MAX_ATTRIBUTE}."
                )

        # Se value for 0 na criação, calcula automaticamente o valor de mercado inicial
        if self.value == 0:
            self.value = self.market_value

        # Se salary for 0 na criação, calcula automaticamente o salário anual padrão inicial
        if self.salary == 0:
            from garfoot.domain.economy import calculate_initial_salary
            self.salary = calculate_initial_salary(self.market_value)

        # Se a cláusula de rescisão for 0 mas houver contrato ativo, calcula automaticamente a cláusula
        if self.contract.release_clause == 0 and self.contract.years_remaining > 0:
            from garfoot.domain.economy import calculate_release_clause
            rel_clause = calculate_release_clause(
                market_value=self.market_value,
                overall=self.overall,
                age=self.age,
                years_remaining=self.contract.years_remaining,
                is_protected=self.contract.is_protected,
            )
            object.__setattr__(
                self,
                "contract",
                Contract(
                    years_remaining=self.contract.years_remaining,
                    is_protected=self.contract.is_protected,
                    protection_years=self.contract.protection_years,
                    release_clause=rel_clause,
                ),
            )

    @property
    def is_injured(self) -> bool:
        """Indica se o jogador está lesionado e indisponível."""
        return self.injury is not None and self.injury.is_active

    @property
    def is_available(self) -> bool:
        """Indica se o jogador está 100% disponível para escalação."""
        return not self.is_injured

    @property
    def overall(self) -> int:
        """Forca geral simples, ajustada pela posicao."""

        if self.position == PlayerPosition.GOALKEEPER:
            technical = self.defense
        elif self.position == PlayerPosition.DEFENDER:
            technical = round(self.defense * 0.75 + self.attack * 0.25)
        elif self.position == PlayerPosition.MIDFIELDER:
            technical = round((self.attack + self.defense) / 2)
        else:
            technical = round(self.attack * 0.75 + self.defense * 0.25)

        return round(technical * 0.65 + self.fitness * 0.2 + self.morale * 0.15)

    @property
    def market_value(self) -> int:
        """Calcula dinamicamente o valor de mercado atualizado pela formula pura."""

        from garfoot.domain.economy import calculate_player_market_value
        return calculate_player_market_value(
            overall=self.overall,
            age=self.age,
            position=self.position,
        )

    def adjust_morale(self, amount: int) -> None:
        """Altera a moral respeitando os limites da escala."""

        self.morale = _clamp_attribute(self.morale + amount)

    def adjust_fitness(self, amount: int) -> None:
        """Altera a forma fisica respeitando os limites da escala."""

        self.fitness = _clamp_attribute(self.fitness + amount)

    def to_dict(self) -> dict[str, object]:
        """Representacao pronta para persistencia em JSON."""

        data = asdict(self)
        data["position"] = self.position.value
        data["contract"] = {
            "years_remaining": self.contract.years_remaining,
            "is_protected": self.contract.is_protected,
            "protection_years": self.contract.protection_years,
            "release_clause": self.contract.release_clause,
        }
        data["injury"] = self.injury.to_dict() if self.injury is not None else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Player":
        """Recria um jogador a partir de dados salvos."""

        payload = dict(data)
        payload["position"] = PlayerPosition(str(payload["position"]))

        contract_data = payload.get("contract")
        if isinstance(contract_data, dict):
            payload["contract"] = Contract(
                years_remaining=int(contract_data.get("years_remaining", 2)),
                is_protected=bool(contract_data.get("is_protected", False)),
                protection_years=int(contract_data.get("protection_years", 0)),
                release_clause=int(contract_data.get("release_clause", 0)),
            )
        else:
            payload["contract"] = Contract()

        injury_data = payload.get("injury")
        if isinstance(injury_data, dict):
            payload["injury"] = Injury.from_dict(injury_data)
        else:
            payload["injury"] = None

        return cls(**payload)  # type: ignore[arg-type]


def _clamp_attribute(value: int) -> int:
    return max(MIN_ATTRIBUTE, min(MAX_ATTRIBUTE, value))


def initialize_player_financials(player: Player) -> Player:
    """Garante que um jogador tenha valor de mercado, salário e cláusula configurados."""

    from dataclasses import replace
    from garfoot.domain.economy import calculate_initial_salary, calculate_release_clause

    mkt_val = player.market_value
    sal = player.salary if player.salary > 0 else calculate_initial_salary(mkt_val)
    rel_clause = (
        player.contract.release_clause
        if player.contract.release_clause > 0
        else calculate_release_clause(mkt_val, player.overall, player.age, player.contract.years_remaining, player.contract.is_protected)
    )

    new_contract = Contract(
        years_remaining=player.contract.years_remaining,
        is_protected=player.contract.is_protected,
        protection_years=player.contract.protection_years,
        release_clause=rel_clause,
    )

    return replace(player, value=mkt_val, salary=sal, contract=new_contract)
