"""Hub central e painel completo da temporada ativa (Carreira)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static

from garfoot.domain.enums import MatchStatus
from garfoot.domain.game_state import GameState
from garfoot.domain.league import MatchFixture
from garfoot.domain.season import LeagueTier
from garfoot.engine.match_engine import MatchResult, simulate_match
from garfoot.engine.match_progression import apply_post_match_progression
from garfoot.persistence.save_manager import SaveManager
from garfoot.ui.widgets.dos import DosPanel


class SeasonHubScreen(Screen[None]):
    """Hub central do jogo quando um save está ativo."""

    BINDINGS = [
        ("escape", "back_to_menu", "Menu Principal"),
        ("space", "play_next_round", "Escalar & Jogar"),
        ("1", "play_next_round", "Escalar & Jogar"),
        ("j", "play_next_round", "Escalar & Jogar"),
        ("f1", "play_next_round", "Escalar & Jogar"),
        ("2", "show_standings", "Classificação"),
        ("c", "show_standings", "Classificação"),
        ("f2", "show_standings", "Classificação"),
        ("3", "save_game", "Salvar Jogo"),
        ("s", "save_game", "Salvar Jogo"),
        ("f3", "save_game", "Salvar Jogo"),
        ("4", "open_market", "Mercado"),
        ("m", "open_market", "Mercado"),
        ("f4", "open_market", "Mercado"),
        ("5", "open_options", "Opções"),
        ("o", "open_options", "Opções"),
        ("f5", "open_options", "Opções"),
        ("6", "show_rankings", "Rankings"),
        ("r", "show_rankings", "Rankings"),
        ("f6", "show_rankings", "Rankings"),
        ("7", "open_news", "Notícias"),
        ("n", "open_news", "Notícias"),
        ("f7", "open_news", "Notícias"),
        ("8", "open_board", "Diretoria"),
        ("i", "open_board", "Diretoria"),
        ("f8", "open_board", "Diretoria"),
        ("9", "open_contracts", "Contratos"),
        ("t", "open_contracts", "Contratos"),
        ("f9", "open_contracts", "Contratos"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("GARFOOT 2026 - HUBS DA TEMPORADA", id="title")
        with Horizontal(id="hub-grid"):
            # Coluna 1: Status do Clube + Detalhes Táticos
            with Vertical(id="hub-left"):
                yield DosPanel("STATUS DA CARREIRA", "Carregando...", id="status-panel")
                yield DosPanel("DESTAQUES DO SEU CLUBE", "Carregando...", id="club-summary-panel")

            # Coluna 2: Jogos da Rodada Atual
            with Vertical(id="hub-middle"):
                yield DosPanel("CONFRONTOS DA RODADA", "Carregando...", id="next-match-panel")

            # Coluna 3: Tabela em Tempo Real (Top 10 / G4 e Z4)
            with Vertical(id="hub-right"):
                yield DosPanel("CLASSIFICAÇÃO SÉRIE D", "Carregando...", id="hub-standings-panel")

        yield DosPanel(
            "AÇÕES",
            "[F1/1] Jogar   [F2/2] Classificação   [F3/3] Salvar   [F4/4] Mercado   [F5/5] Opções   [F6/6] Rankings   [F7/7] Notícias   [F8/8] Diretoria   [F9/9] Contratos",
            id="commands-panel",
        )
        yield DosPanel("ÚLTIMAS NOTÍCIAS", "(sem notícias)", id="hub-news-panel")

    def on_mount(self) -> None:
        self._refresh_ui()

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def action_back_to_menu(self) -> None:
        self.app.pop_screen()

    def action_show_standings(self) -> None:
        self.app.push_screen("standings")

    def action_open_market(self) -> None:
        self.app.push_screen("market")

    def action_open_options(self) -> None:
        self.app.push_screen("options")

    def action_show_rankings(self) -> None:
        self.app.push_screen("rankings")

    def action_open_news(self) -> None:
        self.app.push_screen("news")

    def action_save_game(self) -> None:
        state = self._get_state()
        if not state:
            return
        manager = SaveManager()
        filepath = manager.save_game(state)
        self.app.notify(f"Jogo salvo em {filepath.name}!", title="Salvo com Sucesso")

    def action_play_next_round(self) -> None:
        state = self._get_state()
        if not state:
            return

        if state.current_round > 38:
            self.app.notify("A temporada de pontos corridos foi concluída (38/38 rodadas)!", title="Fim de Temporada")
            return

        # Abre a tela de escalação e tática antes de simular
        self.app.push_screen("match_prep", self._on_match_prep_confirmed)

    def _on_match_prep_confirmed(self, confirmed: bool | None) -> None:
        if not confirmed:
            return

        state = self._get_state()
        if not state:
            return

        user_team = next(
            (c for c in state.season_orchestrator.championships[LeagueTier.SERIE_D].teams if c.name == state.player_team_name),
            None,
        )
        user_series = "D"

        from garfoot.ui.screens.live_match import LiveMatchScreen

        def _on_live_finished() -> None:
            self._refresh_ui()
            # Chama a Etapa 3 (Classificação Pós-Partida de 2 séries por tela)
            self.app.push_screen("standings")

        self.app.push_screen(
            LiveMatchScreen(
                current_round=state.current_round,
                user_series=user_series,
                callback_on_finish=_on_live_finished,
            )
        )

    def _refresh_ui(self) -> None:
        state = self._get_state()
        if not state:
            return

        orchestrator = state.season_orchestrator
        serie_d = orchestrator.championships.get(LeagueTier.SERIE_D)

        # 1. Status da Carreira
        status_text = (
            f"Save: {state.save_name}\n"
            f"Clube: {state.player_team_name}\n"
            f"Temporada: {state.current_season}\n"
            f"Rodada Atual: {min(state.current_round, 38)} / 38\n"
            f"Divisão: Série D"
        )
        self.query_one("#status-panel", DosPanel).update(status_text)

        # 2. Destaques do Clube do Jogador
        user_team = None
        if serie_d:
            user_team = next((t for t in serie_d.teams if t.name == state.player_team_name), None)

        if user_team:
            best_player = max(user_team.players, key=lambda p: p.overall) if user_team.players else None
            stadium_name = user_team.stadium.name if user_team.stadium else "Estádio Próprio"
            stadium_cap = f"{user_team.stadium.capacity:,}" if user_team.stadium else "---"

            summary_text = (
                f"Tática Atual: {user_team.formation.label}\n"
                f"Força do 11 Titular: {user_team.squad_strength}\n"
                f"Moral Média: {user_team.average_morale():.1f}\n"
                f"Destaque: {best_player.name if best_player else '---'} (OVR {best_player.overall if best_player else 0})\n"
                f"Estádio: {stadium_name}\n"
                f"Capacidade: {stadium_cap} lugares"
            )
        else:
            summary_text = "Dados do clube indisponíveis."

        self.query_one("#club-summary-panel", DosPanel).update(summary_text)

        # 3. Rodada Completa (Todos os jogos da rodada na Série D)
        if serie_d and state.current_round <= 38:
            round_fixtures = [f for f in serie_d.fixtures if f.round_number == state.current_round]
            lines = [f"RODADA {state.current_round} / 38:"]
            for f in round_fixtures:
                prefix = ">" if (f.home_team == state.player_team_name or f.away_team == state.player_team_name) else " "
                lines.append(f"{prefix} {f.home_team[:15]:<15} x {f.away_team[:15]:<15}")
            self.query_one("#next-match-panel", DosPanel).update("\n".join(lines))
        else:
            self.query_one("#next-match-panel", DosPanel).update("Temporada Concluída!")

        # 4. Tabela Série D em tempo real (20 times completos)
        if serie_d:
            standings = serie_d.standings()
            lines = ["POS CLUBE                    J  V  E  D GP:GC PTS"]
            for idx, st in enumerate(standings[:20], start=1):
                prefix = ">" if st.team_name == state.player_team_name else " "
                name_abbr = st.team_name[:22]
                lines.append(
                    f"{prefix}{idx:>2} {name_abbr:<22} {st.played:>2} {st.wins:>2} {st.draws:>2} {st.losses:>2} {st.goals_for:>2}:{st.goals_against:<2} {st.points:>3}"
                )
            self.query_one("#hub-standings-panel", DosPanel).update("\n".join(lines))

        # 5. Painel de Últimas Notícias (5 mais recentes)
        news = state.news_center
        latest = news.latest(limit=5)
        unread = news.unread_count()
        if latest:
            news_lines: list[str] = []
            for item in latest:
                mark = "●" if not item.is_read else " "
                news_lines.append(f"{mark} [{item.round_tag}][{item.category_label}] {item.title}")
            if unread:
                news_lines.append(f"\n[7] Ver todas  ({unread} não lidas)")
            else:
                news_lines.append("\n[7] Ver todas")
            news_text = "\n".join(news_lines)
        else:
            news_text = "(nenhuma notícia ainda)\n\n[7] Centro de Notícias"
        self.query_one("#hub-news-panel", DosPanel).update(news_text)

    def action_open_board(self) -> None:
        self.app.push_screen("board_inbox")

    def action_open_contracts(self) -> None:
        self.app.push_screen("contracts")

