"""Regras e fórmulas puras de economia do jogador (valor de mercado e salário)."""

from __future__ import annotations

from garfoot.domain.enums import PlayerPosition

# Parâmetros padrão nomeados para facilidade de ajuste e balanceamento
DEFAULT_BASE_VALUE_UNIT: int = 300_000
DEFAULT_OVERALL_EXPONENT: float = 5.0
DEFAULT_YOUNG_AGE_BONUS_PER_YEAR: float = 0.08
DEFAULT_AGEING_PENALTY_PER_YEAR: float = 0.12
DEFAULT_MIN_AGE_FACTOR: float = 0.10
DEFAULT_SALARY_RATIO: float = 0.12  # Salário anual = ~12% do valor de mercado (~1% ao mês)

# Fatores de posição na precificação de mercado
POSITION_MARKET_FACTORS: dict[PlayerPosition, float] = {
    PlayerPosition.FORWARD: 1.15,
    PlayerPosition.MIDFIELDER: 1.05,
    PlayerPosition.DEFENDER: 0.95,
    PlayerPosition.GOALKEEPER: 0.85,
}


def calculate_player_market_value(
    overall: int,
    age: int,
    position: PlayerPosition,
    base_unit: int = DEFAULT_BASE_VALUE_UNIT,
    exponent: float = DEFAULT_OVERALL_EXPONENT,
    young_bonus_per_year: float = DEFAULT_YOUNG_AGE_BONUS_PER_YEAR,
    ageing_penalty_per_year: float = DEFAULT_AGEING_PENALTY_PER_YEAR,
    min_age_factor: float = DEFAULT_MIN_AGE_FACTOR,
    economic_index: float = 1.0,
) -> int:
    """Calcula o valor de mercado puro de um jogador, ponderado opcionalmente pelo índice econômico global.

    A valorização cresce exponencialmente com o overall e é ponderada
    pela idade, pela posição e pelo índice inflacionário global.
    """

    # 1. Componente de Overall (não-linear)
    overall_ratio = max(1, overall) / 50.0
    base_value = base_unit * (overall_ratio ** exponent)

    # 2. Fator de Idade
    if age < 23:
        age_factor = 1.0 + (23 - age) * young_bonus_per_year
    elif 23 <= age <= 29:
        age_factor = 1.0
    else:
        age_factor = max(min_age_factor, 1.0 - (age - 29) * ageing_penalty_per_year)

    # 3. Fator de Posição
    pos_factor = POSITION_MARKET_FACTORS.get(position, 1.0)

    final_value = round(base_value * age_factor * pos_factor * economic_index)
    return max(10_000, final_value)


def calculate_initial_salary(market_value: int, salary_ratio: float = DEFAULT_SALARY_RATIO) -> int:
    """Calcula o salário anual padrão inicial para um jogador com base no valor de mercado."""

    return max(12_000, round(market_value * salary_ratio))


def calculate_release_clause(
    market_value: int,
    overall: float,
    age: int,
    years_remaining: int,
    is_protected: bool = False,
    is_starter: bool = False,
) -> int:
    """Calcula o valor puro da cláusula de rescisão contratual do jogador.

    - Retorna 0 se o contrato não for ativo (years_remaining <= 0).
    - Fator base: 2.0.
    - Bônus overall: >= 80 (+1.5), >= 70 (+1.0), >= 60 (+0.5).
    - Bônus idade: <= 21 (+2.0), <= 23 (+1.0).
    - Bônus anos restantes: +0.25 por ano acima de 1.
    - Bônus proteção: +1.0 se is_protected is True.
    - Bônus titular: +0.75 se is_starter is True.
    Multiplicador resultante é limitado entre 1.5 e 8.0.
    """

    if years_remaining <= 0:
        return 0

    factor = 2.0

    # Overall bonus
    if overall >= 80:
        factor += 1.5
    elif overall >= 70:
        factor += 1.0
    elif overall >= 60:
        factor += 0.5

    # Idade bonus
    if age <= 21:
        factor += 2.0
    elif age <= 23:
        factor += 1.0

    # Contrato longo bonus
    if years_remaining > 1:
        factor += (years_remaining - 1) * 0.25

    # Proteção bonus
    if is_protected:
        factor += 1.0

    # Titularidade bonus
    if is_starter:
        factor += 0.75

    factor = max(1.5, min(8.0, factor))
    return round(market_value * factor)
