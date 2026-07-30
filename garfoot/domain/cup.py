"""Modelos e orquestração de competições eliminatórias (Copa do Brasil)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from random import Random
from typing import Any

from garfoot.domain.enums import MatchStatus
from garfoot.domain.league import MatchFixture
from garfoot.domain.team import Team

# Limiar a partir do qual a fase preliminar é ativada automaticamente.
# Com até 64 times: fluxo original (byes para potência de 2).
# Com mais de 64 times: fluxo com fase preliminar (Opção B aprovada).
_PRELIMINARY_THRESHOLD = 64


@dataclass(slots=True)
class CupMatch:
    """Partida eliminatória mata-mata (composição sobre MatchFixture).

    Caso o tempo normal termine empatado, o vencedor é definido por pênaltis.
    """

    fixture: MatchFixture
    home_penalties: int | None = None
    away_penalties: int | None = None

    def record_result(
        self,
        home_goals: int,
        away_goals: int,
        home_penalties: int | None = None,
        away_penalties: int | None = None,
    ) -> None:
        """Registra o placar do tempo normal e os pênaltis se houver empate."""

        self.fixture.record_result(home_goals, away_goals)

        if home_goals == away_goals:
            if home_penalties is None or away_penalties is None:
                raise ValueError("Empate em partida eliminatória exige resultado de pênaltis.")
            if home_penalties < 0 or away_penalties < 0:
                raise ValueError("Pênaltis não podem ser negativos.")
            if home_penalties == away_penalties:
                raise ValueError("Cobrança de pênaltis não pode terminar empatada.")
            self.home_penalties = home_penalties
            self.away_penalties = away_penalties
        else:
            self.home_penalties = None
            self.away_penalties = None

    @property
    def winner(self) -> str | None:
        """Retorna o nome do time vencedor da partida eliminatória."""

        if self.fixture.status != MatchStatus.PLAYED:
            return None
        if self.fixture.home_goals is None or self.fixture.away_goals is None:
            return None

        if self.fixture.home_goals > self.fixture.away_goals:
            return self.fixture.home_team
        if self.fixture.away_goals > self.fixture.home_goals:
            return self.fixture.away_team

        # Empate no tempo normal -> desempate em pênaltis
        if self.home_penalties is not None and self.away_penalties is not None:
            if self.home_penalties > self.away_penalties:
                return self.fixture.home_team
            return self.fixture.away_team

        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture": self.fixture.to_dict(),
            "home_penalties": self.home_penalties,
            "away_penalties": self.away_penalties,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CupMatch:
        fixture = MatchFixture.from_dict(data["fixture"])
        return cls(
            fixture=fixture,
            home_penalties=data.get("home_penalties"),
            away_penalties=data.get("away_penalties"),
        )


@dataclass(slots=True)
class KnockoutCup:
    """Competição eliminatória no estilo Copa do Brasil.

    Suporta dois modos de operação, selecionados automaticamente pelo número
    de times participantes:

    - Modo clássico (até 64 times): aplica isenção (byes) para os clubes com
      melhor posição no ranking CBF até completar uma potência de 2.
      Ex: 60 times -> 4 byes -> 56 jogam a 1ª fase.

    - Modo fase preliminar (mais de 64 times): os 32 clubes com pior ranking
      CBF disputam uma fase preliminar (16 confrontos). Os 16 vencedores
      juntam-se aos 48 melhores ranqueados para a fase principal (64 times,
      sem byes). Exemplo com 80 times:
        Fase Preliminar:  32 times -> 16 jogos  -> 16 vencedores
        Fase Principal:   16 + 48  -> 64 times  -> 6 rodadas -> campeão
        Total de jogos: 16 + 32 + 16 + 8 + 4 + 2 + 1 = 79 jogos

    O campo ``preliminary_round`` armazena os confrontos da fase preliminar
    (lista vazia enquanto o modo clássico estiver ativo).
    O campo ``bye_teams`` armazena os times que receberam bye no modo clássico
    (lista vazia quando o modo de fase preliminar estiver ativo).
    """

    name: str
    season_year: int
    teams: list[Team]
    rounds: list[list[CupMatch]] = field(default_factory=list)
    bye_teams: list[str] = field(default_factory=list)
    # Times que aguardam na fase principal enquanto a preliminar é disputada
    preliminary_round: list[CupMatch] = field(default_factory=list)
    # Times top-48 que esperam os 16 vencedores da preliminar
    _main_phase_seeds: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("A copa precisa ter um nome.")
        if len(self.teams) < 2:
            raise ValueError("A copa precisa de pelo menos dois times.")
        if len({team.name for team in self.teams}) != len(self.teams):
            raise ValueError("Não pode haver times repetidos na copa.")

    def generate_initial_bracket(
        self,
        cbf_ranking: dict[str, int],
        seed: int | None = None,
    ) -> None:
        """Gera o chaveamento inicial da competição.

        A decisão de fluxo é automática com base no número de times:
        - <= 64 times: modo clássico com byes (comportamento original).
        - >  64 times: modo fase preliminar (Opção B: 32 piores na preliminar).
        """

        if len(self.teams) > _PRELIMINARY_THRESHOLD:
            self._generate_with_preliminary(cbf_ranking=cbf_ranking, seed=seed)
        else:
            self._generate_with_byes(cbf_ranking=cbf_ranking, seed=seed)

    # ------------------------------------------------------------------
    # Modo clássico (até 64 times) — comportamento original preservado
    # ------------------------------------------------------------------

    def _generate_with_byes(
        self,
        cbf_ranking: dict[str, int],
        seed: int | None = None,
    ) -> None:
        """Gera o chaveamento com byes para potência de 2 (modo clássico)."""

        # Ordena times pelo ranking CBF (menor valor = melhor ranqueado)
        sorted_teams = sorted(
            self.teams,
            key=lambda t: cbf_ranking.get(t.name, 9999),
        )

        num_teams = len(sorted_teams)
        # Calcula quantos byes são necessários para atingir potência de 2
        # Ex: para 60 times, próxima potência de 2 é 64 -> 4 byes
        target_power_of_two = 1
        while target_power_of_two < num_teams:
            target_power_of_two *= 2

        num_byes = target_power_of_two - num_teams

        # Separa os times de bye e os times da 1ª fase
        byes = [t.name for t in sorted_teams[:num_byes]]
        first_round_teams = [t.name for t in sorted_teams[num_byes:]]

        # Sorteio aleatório dos confrontos da 1ª fase
        rng = Random(seed)
        rng.shuffle(first_round_teams)

        first_round_matches: list[CupMatch] = []
        for index in range(0, len(first_round_teams), 2):
            home = first_round_teams[index]
            away = first_round_teams[index + 1]
            fixture = MatchFixture(
                round_number=1,
                home_team=home,
                away_team=away,
            )
            first_round_matches.append(CupMatch(fixture=fixture))

        self.bye_teams = byes
        self.rounds = [first_round_matches]

    # ------------------------------------------------------------------
    # Modo fase preliminar (mais de 64 times)
    # ------------------------------------------------------------------

    def _generate_with_preliminary(
        self,
        cbf_ranking: dict[str, int],
        seed: int | None = None,
    ) -> None:
        """Gera fase preliminar para os 32 piores ranqueados (modo 80 times).

        Os 48 melhores ranqueados ficam guardados em ``_main_phase_seeds``
        e entram na fase principal após advance_preliminary_winners() ser
        chamado. Os 32 piores disputam 16 confrontos aleatórios.
        """

        # Ordena todos os 80 times pelo ranking (melhor -> pior)
        sorted_teams = sorted(
            self.teams,
            key=lambda t: cbf_ranking.get(t.name, 9999),
        )

        # Os 48 melhores ficam aguardando a fase principal
        top_48 = [t.name for t in sorted_teams[:48]]
        bottom_32 = [t.name for t in sorted_teams[48:]]

        # Sorteio aleatório dos 16 confrontos da fase preliminar
        rng = Random(seed)
        rng.shuffle(bottom_32)

        prelim_matches: list[CupMatch] = []
        for index in range(0, len(bottom_32), 2):
            home = bottom_32[index]
            away = bottom_32[index + 1]
            fixture = MatchFixture(
                round_number=0,   # rodada 0 = fase preliminar
                home_team=home,
                away_team=away,
            )
            prelim_matches.append(CupMatch(fixture=fixture))

        self.preliminary_round = prelim_matches
        self._main_phase_seeds = top_48
        self.rounds = []   # a fase principal ainda não começou
        self.bye_teams = []

    def advance_preliminary_winners(self, seed: int | None = None) -> list[CupMatch]:
        """Avança os vencedores da fase preliminar para a fase principal.

        Junta os 16 vencedores com os 48 melhores ranqueados (top_48)
        e sorteia os 32 confrontos da 1ª rodada da fase principal.

        Lança ValueError se houver qualquer partida da preliminar sem resultado.
        Lança ValueError se não houver fase preliminar gerada.
        """

        if not self.preliminary_round:
            raise ValueError(
                "Não há fase preliminar gerada. "
                "Use generate_initial_bracket() com mais de 64 times primeiro."
            )

        # Coleta vencedores da preliminar
        prelim_winners: list[str] = []
        for match in self.preliminary_round:
            w = match.winner
            if w is None:
                raise ValueError(
                    f"Não é possível avançar da fase preliminar: a partida "
                    f"{match.fixture.home_team} x {match.fixture.away_team} "
                    f"ainda não possui vencedor."
                )
            prelim_winners.append(w)

        # Combina os 16 vencedores com os 48 top e sorteia a fase principal
        all_main_phase = prelim_winners + self._main_phase_seeds

        rng = Random(seed)
        rng.shuffle(all_main_phase)

        main_round_matches: list[CupMatch] = []
        for index in range(0, len(all_main_phase), 2):
            home = all_main_phase[index]
            away = all_main_phase[index + 1]
            fixture = MatchFixture(
                round_number=1,   # 1ª rodada da fase principal
                home_team=home,
                away_team=away,
            )
            main_round_matches.append(CupMatch(fixture=fixture))

        # Limpa os seeds (já consumidos) e inicia a lista de rodadas
        self._main_phase_seeds = []
        self.rounds = [main_round_matches]
        return main_round_matches

    def advance_winners(self, seed: int | None = None) -> list[CupMatch]:
        """Avança os vencedores da última rodada da fase principal para a próxima.

        Lança ValueError se houver qualquer partida pendente (sem vencedor).
        No modo clássico, na 2ª fase inclui também os times que receberam bye.
        """

        if not self.rounds:
            raise ValueError("Não há rodadas geradas para avançar.")

        current_round = self.rounds[-1]
        winners: list[str] = []

        for match in current_round:
            w = match.winner
            if w is None:
                raise ValueError(
                    f"Não é possível avançar de fase: a partida {match.fixture.home_team} x "
                    f"{match.fixture.away_team} ainda não possui vencedor."
                )
            winners.append(w)

        # No modo clássico: transição da 1ª para a 2ª fase inclui os byes
        if len(self.rounds) == 1 and self.bye_teams:
            winners.extend(self.bye_teams)
            self.bye_teams = []

        if len(winners) < 2:
            # Torneio já encerrado
            return []

        # Sorteia/pareia os vencedores em nova rodada
        rng = Random(seed)
        rng.shuffle(winners)

        next_round_number = len(self.rounds) + 1
        next_round_matches: list[CupMatch] = []

        for index in range(0, len(winners), 2):
            home = winners[index]
            away = winners[index + 1]
            fixture = MatchFixture(
                round_number=next_round_number,
                home_team=home,
                away_team=away,
            )
            next_round_matches.append(CupMatch(fixture=fixture))

        self.rounds.append(next_round_matches)
        return next_round_matches

    @property
    def champion(self) -> str | None:
        """Retorna o campeão da Copa do Brasil se o torneio estiver finalizado."""

        if not self.rounds:
            return None
        last_round = self.rounds[-1]
        if len(last_round) == 1:
            return last_round[0].winner
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "season_year": self.season_year,
            "teams": [t.to_dict() for t in self.teams],
            "rounds": [[m.to_dict() for m in r] for r in self.rounds],
            "bye_teams": list(self.bye_teams),
            "preliminary_round": [m.to_dict() for m in self.preliminary_round],
            "main_phase_seeds": list(self._main_phase_seeds),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnockoutCup:
        teams = [Team.from_dict(t) for t in data.get("teams", [])]
        rounds = [
            [CupMatch.from_dict(m) for m in r]
            for r in data.get("rounds", [])
        ]
        preliminary_round = [
            CupMatch.from_dict(m) for m in data.get("preliminary_round", [])
        ]
        instance = cls(
            name=data["name"],
            season_year=data["season_year"],
            teams=teams,
            rounds=rounds,
            bye_teams=data.get("bye_teams", []),
            preliminary_round=preliminary_round,
        )
        instance._main_phase_seeds = data.get("main_phase_seeds", [])
        return instance
