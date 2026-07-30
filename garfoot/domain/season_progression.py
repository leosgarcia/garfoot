"""Orquestração de progressão pós-temporada e promoção da base para times."""

from __future__ import annotations

from dataclasses import replace
from random import Random

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.player_progression import apply_season_aging
from garfoot.domain.stable_random import combine_seed, stable_int_seed
from garfoot.domain.team import Team


def apply_season_team_progression(
    team: Team,
    rng: Random | None = None,
    seed: int | None = None,
) -> Team:
    """Aplica envelhecimento aos jogadores do time e promove promessas da base se houver aposentadoria."""

    if rng is not None:
        random_gen = rng
    elif seed is not None:
        random_gen = Random(combine_seed(seed, team.name, namespace="season-progression"))
    else:
        random_gen = Random(stable_int_seed(team.name, namespace="season-progression"))

    updated_players: list[Player] = []
    retired_names: set[str] = set()

    for player in team.players:
        aged_player = apply_season_aging(player, rng=random_gen)
        if aged_player is None:
            # Jogador se aposentou! Promove promessa da base para repor a posição
            retired_names.add(player.name)
            youth_promoted = _generate_youth_promoted_player(
                team=team,
                position=player.position,
                rng=random_gen,
            )
            updated_players.append(youth_promoted)
        else:
            updated_players.append(aged_player)

    # Limpa nomes de aposentados da escalação titular
    new_starters = [
        name for name in team.starting_player_names if name not in retired_names
    ]

    return replace(
        team,
        players=updated_players,
        starting_player_names=new_starters,
    )


def _generate_youth_promoted_player(
    team: Team,
    position: PlayerPosition,
    rng: Random,
) -> Player:
    """Gera um novo jogador promessa da base (17 a 19 anos) para repor a posição do aposentado."""

    youth_age = rng.randint(17, 19)

    # Base de atributos fundamentada na moral/força atual do time (50 a 70)
    base_ovr = max(50, min(75, round(team.average_morale())))

    if position == PlayerPosition.GOALKEEPER:
        def_val = base_ovr
        att_val = max(1, base_ovr - 40)
    elif position == PlayerPosition.DEFENDER:
        def_val = min(100, base_ovr + rng.randint(1, 5))
        att_val = max(1, base_ovr - rng.randint(15, 25))
    elif position == PlayerPosition.MIDFIELDER:
        def_val = base_ovr
        att_val = base_ovr
    else:  # FORWARD
        att_val = min(100, base_ovr + rng.randint(1, 5))
        def_val = max(1, base_ovr - rng.randint(15, 25))

    youth_name = f"Base {team.name[:3].upper()} {rng.randint(100, 999)}"

    return Player(
        name=youth_name,
        age=youth_age,
        position=position,
        attack=att_val,
        defense=def_val,
        fitness=rng.randint(85, 98),  # Jovem da base chega em boa forma física
        morale=rng.randint(70, 85),
        value=base_ovr * 10_000,
    )
