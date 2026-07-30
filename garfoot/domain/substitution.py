"""Modelo e regras puras de substituição de jogadores em partida."""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Any

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.stable_random import stable_composite_seed
from garfoot.engine.events import SubstitutionEvent, SubstitutionReason

DEFAULT_MAX_SUBSTITUTIONS: int = 5


@dataclass(slots=True)
class TeamMatchLineupState:
    """Estado dos jogadores de um time durante o decorrer da partida."""

    team_name: str
    players_on_pitch: list[Player]
    bench: list[Player]
    substitutions_made: list[SubstitutionEvent] = field(default_factory=list)
    used_player_names: set[str] = field(default_factory=set)
    max_substitutions: int = DEFAULT_MAX_SUBSTITUTIONS

    def __post_init__(self) -> None:
        if not self.used_player_names:
            self.used_player_names = {p.name for p in self.players_on_pitch}

    @property
    def remaining_substitutions(self) -> int:
        return max(0, self.max_substitutions - len(self.substitutions_made))

    def find_player_on_pitch(self, player_name: str) -> Player | None:
        return next((p for p in self.players_on_pitch if p.name == player_name), None)

    def find_player_on_bench(self, player_name: str) -> Player | None:
        return next((p for p in self.bench if p.name == player_name), None)


def can_substitute(
    lineup: TeamMatchLineupState,
    player_out_name: str,
    player_in_name: str,
) -> tuple[bool, str]:
    """Valida se uma substituição é permitida pelas regras da partida."""

    if lineup.remaining_substitutions <= 0:
        return False, "Limite de substituições da equipe já foi atingido (5/5)."

    player_out = lineup.find_player_on_pitch(player_out_name)
    if not player_out:
        return False, f"O jogador {player_out_name} não está em campo."

    player_in = lineup.find_player_on_bench(player_in_name)
    if not player_in:
        return False, f"O jogador {player_in_name} não está disponível no banco de reservas."

    if player_in.is_injured:
        return False, f"O jogador {player_in_name} está lesionado e indisponível."

    if player_in.name in lineup.used_player_names and player_in not in lineup.bench:
        return False, f"O jogador {player_in_name} já jogou ou foi substituído anteriormente nesta partida."

    return True, "Substituição válida."


def apply_substitution(
    lineup: TeamMatchLineupState,
    minute: int,
    player_out_name: str,
    player_in_name: str,
    reason: SubstitutionReason = SubstitutionReason.TACTICAL,
) -> tuple[TeamMatchLineupState, SubstitutionEvent]:
    """Aplica a substituição no estado do time de forma pura, retornando o estado atualizado e o evento."""

    valid, msg = can_substitute(lineup, player_out_name, player_in_name)
    if not valid:
        raise ValueError(msg)

    player_out = lineup.find_player_on_pitch(player_out_name)
    player_in = lineup.find_player_on_bench(player_in_name)

    # Remove do campo e banco
    new_pitch = [p for p in lineup.players_on_pitch if p.name != player_out_name] + [player_in]
    new_bench = [p for p in lineup.bench if p.name != player_in_name]

    new_used = set(lineup.used_player_names)
    new_used.add(player_out_name)
    new_used.add(player_in_name)

    sub_event = SubstitutionEvent(
        minute=minute,
        team_name=lineup.team_name,
        player_out_name=player_out_name,
        player_in_name=player_in_name,
        reason=reason,
    )

    new_subs = list(lineup.substitutions_made) + [sub_event]

    new_lineup = TeamMatchLineupState(
        team_name=lineup.team_name,
        players_on_pitch=new_pitch,
        bench=new_bench,
        substitutions_made=new_subs,
        used_player_names=new_used,
        max_substitutions=lineup.max_substitutions,
    )

    return new_lineup, sub_event


def suggest_cpu_substitution(
    lineup: TeamMatchLineupState,
    minute: int,
    rng: Random | None = None,
) -> tuple[TeamMatchLineupState, SubstitutionEvent] | None:
    """Sugere e aplica uma substituição automática pela CPU por lesão ou fadiga excessiva."""

    if lineup.remaining_substitutions <= 0 or not lineup.bench:
        return None

    random_gen = rng if rng is not None else Random(stable_composite_seed((lineup.team_name, minute), namespace="cpu-substitution"))

    # 1. Procura jogador lesionado em campo
    injured_on_pitch = next((p for p in lineup.players_on_pitch if p.is_injured), None)
    if injured_on_pitch:
        available_bench = [p for p in lineup.bench if p.is_available]
        if available_bench:
            # Tenta encontrar reserva da mesma posição
            same_pos = [p for p in available_bench if p.position == injured_on_pitch.position]
            target_in = same_pos[0] if same_pos else max(available_bench, key=lambda x: x.overall)
            try:
                return apply_substitution(
                    lineup=lineup,
                    minute=minute,
                    player_out_name=injured_on_pitch.name,
                    player_in_name=target_in.name,
                    reason=SubstitutionReason.INJURY,
                )
            except ValueError:
                pass

    # 2. Procura jogador com fadiga muito baixa (fitness < 45)
    fatigued_on_pitch = next((p for p in lineup.players_on_pitch if p.fitness < 45), None)
    if fatigued_on_pitch:
        available_bench = [p for p in lineup.bench if p.is_available]
        if available_bench:
            same_pos = [p for p in available_bench if p.position == fatigued_on_pitch.position]
            target_in = same_pos[0] if same_pos else max(available_bench, key=lambda x: x.overall)
            try:
                return apply_substitution(
                    lineup=lineup,
                    minute=minute,
                    player_out_name=fatigued_on_pitch.name,
                    player_in_name=target_in.name,
                    reason=SubstitutionReason.FITNESS,
                )
            except ValueError:
                pass

    return None
