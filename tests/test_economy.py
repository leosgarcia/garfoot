"""Testes unitários para regras de economia do jogador (valor de mercado, salário e contrato)."""

import pytest

from garfoot.domain.contract import Contract
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.economy import (
    calculate_initial_salary,
    calculate_player_market_value,
)
from garfoot.domain.player import Player, initialize_player_financials


def test_contract_model_properties():
    # Contrato normal de 2 anos (pode ser transferido)
    c1 = Contract(years_remaining=2, is_protected=False, protection_years=0)
    assert c1.can_be_transferred is True

    # Contrato de jogador sem contrato (expirado)
    c2 = Contract(years_remaining=0)
    assert c2.can_be_transferred is False

    # Contrato protegido contra venda
    c3 = Contract(years_remaining=3, is_protected=True)
    assert c3.can_be_transferred is False

    # Contrato com anos de proteção restantes
    c4 = Contract(years_remaining=3, is_protected=False, protection_years=1)
    assert c4.can_be_transferred is False


def test_contract_validation():
    with pytest.raises(ValueError, match="Anos de contrato restantes nao podem ser negativos"):
        Contract(years_remaining=-1)

    with pytest.raises(ValueError, match="Anos de protecao de contrato nao podem ser negativos"):
        Contract(years_remaining=2, protection_years=-1)


def test_market_value_numerical_examples():
    """Valida a fórmula de valor de mercado para perfis diferentes de jogadores."""
    # 1. Jovem promessa (18 anos, atacante, overall 75)
    v_jovem = calculate_player_market_value(overall=75, age=18, position=PlayerPosition.FORWARD)
    # 2. Estrela no auge (27 anos, meia, overall 82)
    v_auge = calculate_player_market_value(overall=82, age=27, position=PlayerPosition.MIDFIELDER)
    # 3. Jogador mediano (25 anos, defensor, overall 58)
    v_mediano = calculate_player_market_value(overall=58, age=25, position=PlayerPosition.DEFENDER)
    # 4. Veterano (36 anos, defensor, overall 78)
    v_veterano = calculate_player_market_value(overall=78, age=36, position=PlayerPosition.DEFENDER)

    # 1. Jovem com alto overall deve valer muito
    assert v_jovem > 3_000_000

    # 2. Estrela no auge com overall 82 deve valer mais que mediano
    assert v_auge > v_mediano
    assert v_auge > 3_500_000

    # 3. Jogador mediano deve valer na faixa de centenas de milhares
    assert 200_000 <= v_mediano <= 800_000

    # 4. Veterano (36 anos) sofre acentuado declínio de mercado em relação ao auge
    assert v_veterano < v_auge


def test_player_property_market_value_integration():
    player = Player(
        name="Endrick",
        age=18,
        position=PlayerPosition.FORWARD,
        attack=80,
        defense=40,
        fitness=80,
        morale=80,
    )

    # market_value é uma property que calcula dinamicamente o valor
    assert player.market_value > 1_000_000
    assert player.salary > 0
    assert player.contract.can_be_transferred is True


def test_initialize_player_financials():
    p = Player(
        name="Jogador Exemplo",
        age=24,
        position=PlayerPosition.MIDFIELDER,
        attack=60,
        defense=60,
        fitness=60,
        morale=60,
    )

    p_init = initialize_player_financials(p)
    assert p_init.value > 0
    assert p_init.salary == calculate_initial_salary(p_init.value)


def test_player_to_dict_from_dict_contract_serialization():
    p = Player(
        name="Jogador Protegido",
        age=22,
        position=PlayerPosition.DEFENDER,
        attack=50,
        defense=70,
        fitness=80,
        morale=80,
        contract=Contract(years_remaining=3, is_protected=True, protection_years=2),
    )

    data = p.to_dict()
    assert data["contract"]["is_protected"] is True
    assert data["contract"]["protection_years"] == 2

    p_recreated = Player.from_dict(data)
    assert p_recreated.contract.is_protected is True
    assert p_recreated.contract.protection_years == 2
    assert p_recreated.contract.can_be_transferred is False
    assert p_recreated.contract.release_clause > 0


def test_calculate_release_clause_factors_and_limits():
    from garfoot.domain.economy import calculate_release_clause

    mkt = 1_000_000

    # 1. Jovem promessa protegida (18 anos, overall 80, 3 anos contrato, protegida) -> Cláusula alta (5x a 8x)
    rel_jovem = calculate_release_clause(mkt, overall=80, age=18, years_remaining=3, is_protected=True)
    assert rel_jovem > mkt * 5

    # 2. Reserva veterano (35 anos, overall 55, 1 ano contrato) -> Cláusula menor (1.5x a 2.5x)
    rel_vet = calculate_release_clause(mkt, overall=55, age=35, years_remaining=1, is_protected=False)
    assert rel_vet < rel_jovem
    assert rel_vet >= round(mkt * 1.5)

    # 3. Jogador sem contrato (0 anos restantes) -> Cláusula = 0
    rel_expired = calculate_release_clause(mkt, overall=70, age=25, years_remaining=0)
    assert rel_expired == 0


def test_contract_release_clause_stability():
    p = Player(
        name="Craque Estável",
        age=20,
        position=PlayerPosition.FORWARD,
        attack=85,
        defense=40,
        fitness=80,
        morale=80,
    )

    initial_clause = p.contract.release_clause
    assert initial_clause > p.market_value

    # Alterar a fadiga altera o overall/valor de mercado, mas a cláusula no contrato permanece estável!
    p.adjust_fitness(-20)
    assert p.contract.release_clause == initial_clause
