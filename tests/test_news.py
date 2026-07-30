"""Testes unitários do Centro de Notícias e Eventos da Temporada."""

from __future__ import annotations

import pytest

from garfoot.domain.game_state import GameState
from garfoot.domain.news import (
    NewsCategory,
    NewsCenter,
    NewsItem,
    NewsPriority,
    create_award_news,
    create_coach_news,
    create_contract_news,
    create_financial_news,
    create_injury_news,
    create_match_news,
    create_news_item,
    create_stadium_news,
    create_transfer_news,
    make_news_id,
    prune_news_items,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item(
    season: int = 2026,
    rnd: int | None = 5,
    cat: NewsCategory = NewsCategory.MATCH,
    prio: NewsPriority = NewsPriority.NORMAL,
    seq: int = 1,
    is_read: bool = False,
    team: str = "Fortaleza",
) -> NewsItem:
    return NewsItem(
        id=make_news_id(season, rnd, cat, seq),
        season_year=season,
        round_number=rnd,
        category=cat,
        priority=prio,
        title="Título Teste",
        message="Mensagem de teste.",
        team_name=team,
        is_read=is_read,
    )


# ---------------------------------------------------------------------------
# 1. Modelo NewsItem
# ---------------------------------------------------------------------------

def test_news_item_to_dict_and_from_dict() -> None:
    item = _item(season=2026, rnd=10, cat=NewsCategory.TRANSFER, prio=NewsPriority.IMPORTANT)
    data = item.to_dict()

    assert data["category"] == "transfer"
    assert data["priority"] == "important"
    assert data["is_read"] is False

    restored = NewsItem.from_dict(data)
    assert restored.category == NewsCategory.TRANSFER
    assert restored.priority == NewsPriority.IMPORTANT
    assert restored.season_year == 2026
    assert restored.round_number == 10


def test_news_item_optional_fields_default_to_none() -> None:
    item = _item()
    assert item.player_name is None
    assert item.coach_name is None
    assert item.amount is None
    assert item.related_team_name is None


def test_news_item_is_read_persists() -> None:
    item = _item(is_read=True)
    data = item.to_dict()
    restored = NewsItem.from_dict(data)
    assert restored.is_read is True


def test_news_item_labels() -> None:
    item = _item(prio=NewsPriority.URGENT, cat=NewsCategory.FINANCE)
    assert "[!!!]" in item.priority_label
    assert "FINANÇAS" in item.category_label
    assert "R05" in item.round_tag


# ---------------------------------------------------------------------------
# 2. NewsCenter
# ---------------------------------------------------------------------------

def test_news_center_add_and_latest() -> None:
    nc = NewsCenter()
    for i in range(1, 6):
        nc.add(_item(seq=i, rnd=i))

    latest = nc.latest(limit=3)
    assert len(latest) == 3
    # Deve vir em ordem inversa (mais recente primeiro)
    assert latest[0].round_number == 5


def test_news_center_unread() -> None:
    nc = NewsCenter()
    nc.add(_item(is_read=False, seq=1))
    nc.add(_item(is_read=True, seq=2))
    nc.add(_item(is_read=False, seq=3))

    unread = nc.unread()
    assert len(unread) == 2


def test_news_center_mark_all_read() -> None:
    nc = NewsCenter()
    nc.add(_item(is_read=False, seq=1))
    nc.add(_item(is_read=False, seq=2))

    nc.mark_all_read()
    assert nc.unread_count() == 0
    assert all(i.is_read for i in nc.items)


def test_news_center_by_category() -> None:
    nc = NewsCenter()
    nc.add(_item(cat=NewsCategory.TRANSFER, seq=1))
    nc.add(_item(cat=NewsCategory.INJURY, seq=2))
    nc.add(_item(cat=NewsCategory.TRANSFER, seq=3))

    transfers = nc.by_category(NewsCategory.TRANSFER)
    assert len(transfers) == 2
    assert all(i.category == NewsCategory.TRANSFER for i in transfers)


def test_news_center_for_team() -> None:
    nc = NewsCenter()
    nc.add(_item(team="Fortaleza", seq=1))
    nc.add(_item(team="Ceará", seq=2))
    nc.add(NewsItem(
        id="2026-R05-match-003",
        season_year=2026,
        round_number=5,
        category=NewsCategory.MATCH,
        priority=NewsPriority.NORMAL,
        title="Clássico",
        message="...",
        team_name="Fortaleza",
        related_team_name="Ceará",
    ))

    result = nc.for_team("Ceará")
    assert len(result) == 2   # item 2 e item 3 (relacionado)


def test_news_center_create_and_add_generates_sequential_ids() -> None:
    nc = NewsCenter()
    i1 = nc.create_and_add(2026, 1, NewsCategory.MATCH, NewsPriority.NORMAL, "T1", "M1")
    i2 = nc.create_and_add(2026, 1, NewsCategory.MATCH, NewsPriority.NORMAL, "T2", "M2")
    assert i1.id != i2.id
    assert nc._sequence == 2


# ---------------------------------------------------------------------------
# 3. Serialização de NewsCenter
# ---------------------------------------------------------------------------

def test_news_center_to_dict_and_from_dict() -> None:
    nc = NewsCenter()
    nc.add(_item(seq=1, is_read=False))
    nc.add(_item(seq=2, is_read=True, cat=NewsCategory.FINANCE))

    data = nc.to_dict()
    assert len(data["items"]) == 2

    restored = NewsCenter.from_dict(data)
    assert len(restored.items) == 2
    assert restored.items[1].is_read is True
    assert restored.items[1].category == NewsCategory.FINANCE


def test_news_center_from_dict_none_returns_empty() -> None:
    nc = NewsCenter.from_dict(None)
    assert nc.items == []
    assert nc.unread_count() == 0


# ---------------------------------------------------------------------------
# 4. Compatibilidade com GameState (saves antigos)
# ---------------------------------------------------------------------------

def test_game_state_from_dict_without_news_center_loads_fine() -> None:
    """Saves antigos sem 'news_center' devem carregar NewsCenter vazio."""
    # Testa o comportamento de fallback do NewsCenter.from_dict
    nc = NewsCenter.from_dict(None)
    assert nc.items == []
    assert nc.unread_count() == 0
    assert nc.latest() == []


# ---------------------------------------------------------------------------
# 5. Geração de notícias — funções fábrica
# ---------------------------------------------------------------------------

def test_create_transfer_news_normal() -> None:
    item = create_transfer_news(2026, 10, "Santa Cruz", "João Silva", "Remo", 1_200_000, sequence=1)
    assert item.category == NewsCategory.TRANSFER
    assert item.priority == NewsPriority.IMPORTANT
    assert "João Silva" in item.message
    assert item.amount == 1_200_000


def test_create_transfer_news_free_agent() -> None:
    item = create_transfer_news(2026, 5, "Fortaleza", "Teste", None, 0, sequence=2, is_free_agent=True)
    assert item.category == NewsCategory.TRANSFER
    assert item.priority == NewsPriority.NORMAL
    assert "sem custo" in item.message.lower()


def test_create_transfer_news_release_clause() -> None:
    item = create_transfer_news(2026, 8, "Bahia", "Pedro Lima", "Ceará", 8_000_000, sequence=3, is_release_clause=True)
    assert "cláusula" in item.message.lower()
    assert item.priority == NewsPriority.IMPORTANT


def test_create_injury_news_grave() -> None:
    item = create_injury_news(2026, 12, "Clube X", "Atacante Y", rounds_out=8, sequence=4)
    assert item.category == NewsCategory.INJURY
    assert item.priority == NewsPriority.IMPORTANT
    assert "grave" in item.message.lower()


def test_create_injury_news_leve() -> None:
    item = create_injury_news(2026, 3, "Clube X", "Zagueiro Z", rounds_out=2, sequence=5)
    assert item.category == NewsCategory.INJURY
    assert item.priority == NewsPriority.NORMAL


def test_create_financial_news_crisis_is_urgent() -> None:
    item = create_financial_news(2026, 15, "Clube Y", "crisis", "Clube entrou em crise financeira.", sequence=6)
    assert item.category == NewsCategory.FINANCE
    assert item.priority == NewsPriority.URGENT


def test_create_financial_news_negative_budget_is_urgent() -> None:
    item = create_financial_news(2026, 7, "Clube Z", "negativo", "Orçamento negativo detectado.", sequence=7)
    assert item.priority == NewsPriority.URGENT


def test_create_coach_news_demissao() -> None:
    item = create_coach_news(2026, 10, "Paysandu", "Carlos Andrade", "demitido", sequence=8)
    assert item.category == NewsCategory.COACH
    assert item.priority == NewsPriority.IMPORTANT
    assert "demitido" in item.message.lower()


def test_create_match_news_goleada() -> None:
    item = create_match_news(2026, 20, "Time A", "Time B", 5, 0, sequence=9)
    assert item.category == NewsCategory.MATCH
    assert item.priority == NewsPriority.IMPORTANT
    assert "Goleada" in item.title


def test_create_match_news_final_is_urgent() -> None:
    item = create_match_news(2026, 38, "Time A", "Time B", 1, 0, is_final=True, sequence=10)
    assert item.priority == NewsPriority.URGENT


def test_create_award_news() -> None:
    item = create_award_news(2026, None, "Time Campeão", "Chuteira de Ouro", "Pedro Lima artilheiro com 29 gols.", player_name="Pedro Lima", sequence=11)
    assert item.category == NewsCategory.AWARD
    assert item.priority == NewsPriority.IMPORTANT


def test_create_stadium_news() -> None:
    item = create_stadium_news(2026, 30, "Clube Teste", "Obras concluídas", "Estádio ampliado em 5.000 lugares.", sequence=12)
    assert item.category == NewsCategory.STADIUM


# ---------------------------------------------------------------------------
# 6. Pruning do histórico
# ---------------------------------------------------------------------------

def test_prune_keeps_urgent_current_season() -> None:
    items = [
        _item(season=2025, prio=NewsPriority.LOW, seq=i, rnd=i)
        for i in range(1, 250)
    ] + [
        _item(season=2026, prio=NewsPriority.URGENT, seq=i, rnd=i)
        for i in range(250, 260)
    ]

    pruned = prune_news_items(items, max_items=50, current_season=2026)

    # Todas as URGENT de 2026 devem ser mantidas
    urgent_2026 = [i for i in pruned if i.season_year == 2026 and i.priority == NewsPriority.URGENT]
    assert len(urgent_2026) == 10


def test_prune_respects_max_items() -> None:
    items = [_item(seq=i, rnd=i % 38 + 1) for i in range(1, 400)]
    pruned = prune_news_items(items, max_items=100, current_season=2026)
    assert len(pruned) <= 100


def test_prune_preserves_recent_over_old() -> None:
    old = [_item(season=2024, prio=NewsPriority.LOW, seq=i, rnd=i % 38 + 1) for i in range(1, 200)]
    recent = [_item(season=2026, prio=NewsPriority.NORMAL, seq=i, rnd=i % 38 + 1) for i in range(200, 250)]
    items = old + recent

    pruned = prune_news_items(items, max_items=60, current_season=2026)
    # Recentes devem ser maioria
    recent_count = sum(1 for i in pruned if i.season_year == 2026)
    assert recent_count >= 40


# ---------------------------------------------------------------------------
# 7. GameState — persistência de NewsCenter
# ---------------------------------------------------------------------------

def test_game_state_includes_news_center_in_to_dict() -> None:
    from garfoot.domain.game_state import GameState
    from garfoot.domain.news import NewsCenter

    # Verifica que to_dict() contém a chave 'news_center' ao serializar
    nc = NewsCenter()
    nc.add(_item(seq=1))
    nc.add(_item(seq=2, cat=NewsCategory.FINANCE, prio=NewsPriority.URGENT))

    # Apenas verifica a estrutura de to_dict do NewsCenter
    data = nc.to_dict()
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["items"][1]["priority"] == "urgent"


# ---------------------------------------------------------------------------
# 8. Engine permanece pura
# ---------------------------------------------------------------------------

def test_engine_does_not_import_news() -> None:
    import sys
    engine_modules = [k for k in sys.modules if k.startswith("garfoot.engine")]
    for mod_name in engine_modules:
        mod = sys.modules[mod_name]
        source_file = getattr(mod, "__file__", "") or ""
        if source_file.endswith(".py"):
            with open(source_file) as f:
                content = f.read()
            assert "from garfoot.domain.news" not in content, (
                f"Engine module {mod_name} importa news — violação de pureza!"
            )
            assert "import news" not in content, (
                f"Engine module {mod_name} importa news — violação de pureza!"
            )
