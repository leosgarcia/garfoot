"""Tela TUI do Centro de Notícias da Temporada."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from garfoot.domain.game_state import GameState
from garfoot.domain.news import NewsCategory, NewsCenter, NewsPriority
from garfoot.ui.widgets.dos import DosPanel

# Filtros disponíveis (tecla → (label, categoria | None))
_FILTERS: list[tuple[str, str, NewsCategory | None]] = [
    ("1", "Todas", None),
    ("2", "Meu Clube", None),        # Filtro especial: usa for_team()
    ("3", "Transferências", NewsCategory.TRANSFER),
    ("4", "Finanças", NewsCategory.FINANCE),
    ("5", "Técnicos", NewsCategory.COACH),
    ("6", "Lesões", NewsCategory.INJURY),
    ("7", "Premiações", NewsCategory.AWARD),
    ("8", "Estádio", NewsCategory.STADIUM),
    ("9", "Partidas", NewsCategory.MATCH),
]

_MAX_DISPLAY = 20


class NewsScreen(Screen[None]):
    """Tela dedicada ao Centro de Notícias e Eventos da Temporada."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("1", "filter_all", "Todas"),
        ("2", "filter_my_club", "Meu Clube"),
        ("3", "filter_transfer", "Transferências"),
        ("4", "filter_finance", "Finanças"),
        ("5", "filter_coach", "Técnicos"),
        ("6", "filter_injury", "Lesões"),
        ("7", "filter_award", "Premiações"),
        ("8", "filter_stadium", "Estádio"),
        ("9", "filter_match", "Partidas"),
        ("r", "mark_read", "Marcar lidas"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._active_filter: str = "1"   # chave do filtro ativo

    def compose(self) -> ComposeResult:
        yield Static("CENTRO DE NOTÍCIAS DA TEMPORADA", id="news-title")
        with Vertical(id="news-body"):
            yield DosPanel("FILTROS", self._filter_bar(), id="news-filters")
            yield DosPanel("NOTÍCIAS", "Carregando...", id="news-list")
        yield Static(
            "[ESC] Voltar  [R] Marcar lidas  [1-9] Filtros",
            id="news-commands",
        )

    def on_mount(self) -> None:
        self._refresh_news()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def _filter_bar(self) -> str:
        parts = []
        for key, label, _ in _FILTERS:
            marker = "►" if key == self._active_filter else " "
            parts.append(f"[{key}]{marker}{label}")
        return "   ".join(parts)

    def _get_items(self, news: NewsCenter, state: GameState) -> list:
        key = self._active_filter

        if key == "1":
            return news.latest(limit=_MAX_DISPLAY)
        elif key == "2":
            return news.for_team(state.player_team_name, limit=_MAX_DISPLAY)
        else:
            cat = next((c for k, _, c in _FILTERS if k == key and c is not None), None)
            if cat:
                return news.by_category(cat, limit=_MAX_DISPLAY)
            return news.latest(limit=_MAX_DISPLAY)

    def _format_items(self, items: list) -> str:
        if not items:
            return "(Nenhuma notícia nesta categoria.)"

        lines: list[str] = []
        for item in items:
            # Cabeçalho da notícia
            prio = item.priority_label
            unread_mark = "● " if not item.is_read else "  "
            header = f"{unread_mark}[{item.round_tag}][{item.category_label}]{prio} {item.title}"
            lines.append(header)
            lines.append(f"   {item.message}")
            lines.append("")

        return "\n".join(lines).rstrip()

    def _refresh_news(self) -> None:
        state = self._get_state()
        if not state:
            self.query_one("#news-list", DosPanel).update("Nenhum jogo ativo.")
            return

        news = state.news_center
        items = self._get_items(news, state)
        unread = news.unread_count()

        title_suffix = f"  [{unread} não lidas]" if unread else "  [Tudo lido]"
        panel = self.query_one("#news-list", DosPanel)
        panel.border_title = f" NOTÍCIAS{title_suffix} "
        panel.update(self._format_items(items))
        self.query_one("#news-filters", DosPanel).update(self._filter_bar())

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_mark_read(self) -> None:
        state = self._get_state()
        if state:
            state.news_center.mark_all_read()
            self._refresh_news()

    def _set_filter(self, key: str) -> None:
        self._active_filter = key
        self._refresh_news()

    def action_filter_all(self) -> None:
        self._set_filter("1")

    def action_filter_my_club(self) -> None:
        self._set_filter("2")

    def action_filter_transfer(self) -> None:
        self._set_filter("3")

    def action_filter_finance(self) -> None:
        self._set_filter("4")

    def action_filter_coach(self) -> None:
        self._set_filter("5")

    def action_filter_injury(self) -> None:
        self._set_filter("6")

    def action_filter_award(self) -> None:
        self._set_filter("7")

    def action_filter_stadium(self) -> None:
        self._set_filter("8")

    def action_filter_match(self) -> None:
        self._set_filter("9")
