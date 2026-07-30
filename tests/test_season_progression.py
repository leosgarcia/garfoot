"""Testes unitários para a progressão pós-temporada e promoção da base."""

from random import Random

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.season_progression import apply_season_team_progression
from garfoot.domain.team import Team


def test_apply_season_team_progression_aging_and_youth_promotion():
    # Time com um jovem e um veterano prestes a se aposentar
    young = Player(
        name="Jovem Promessa",
        age=20,
        position=PlayerPosition.FORWARD,
        attack=75,
        defense=30,
        fitness=80,
        morale=80,
        value=100_000,
    )
    ancient = Player(
        name="Veterano Aposentado",
        age=39,
        position=PlayerPosition.GOALKEEPER,
        attack=10,
        defense=20,
        fitness=30,
        morale=30,
        value=10_000,
    )

    team = Team(
        name="Flamengo",
        city="Rio de Janeiro",
        budget=1_000_000,
        players=[young, ancient],
        starting_player_names=["Jovem Promessa", "Veterano Aposentado"],
    )

    rng = Random(42)
    updated_team = apply_season_team_progression(team, rng=rng)

    assert len(updated_team.players) == 2  # Quantidade de elenco preservada!

    # O jovem deve ter envelhecido (+1 ano)
    updated_young = next(p for p in updated_team.players if p.name == "Jovem Promessa")
    assert updated_young.age == 21

    # O veterano se aposentou e foi substituído por uma nova promessa da base da mesma posição
    youth = next(p for p in updated_team.players if p.name != "Jovem Promessa")
    assert youth.position == PlayerPosition.GOALKEEPER
    assert 17 <= youth.age <= 19
    assert youth.name.startswith("Base FLA")

    # Aposentado foi removido da lista de titulares
    assert "Veterano Aposentado" not in updated_team.starting_player_names
