"""Tela de Premiações Finais da Temporada em estilo DOS / Textual."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.domain.game_state import GameState
from garfoot.domain.prizes import SeasonAwardsResult
from garfoot.ui.widgets.dos import DosPanel


class SeasonAwardsScreen(Screen[None]):
    """Tela de encerramento da temporada com premiações e Chuteira de Ouro."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("enter", "back", "Confirmar"),
    ]

    def __init__(self, awards_result: SeasonAwardsResult | None = None) -> None:
        super().__init__()
        self.awards_result = awards_result

    def compose(self) -> ComposeResult:
        yield Static("ENCRRAMENTO DA TEMPORADA - PREMIAÇÕES FINAIS", id="title")
        with Horizontal(id="clubs-grid"):
            yield ListView(id="awards-list")
            with Vertical(id="club-side"):
                yield DosPanel("DESTAQUES DO ANO", "Carregando...", id="highlights-panel")
                yield DosPanel("TOTAL DE PREMIAÇÕES", "Carregando...", id="totals-panel")
        yield DosPanel("COMANDOS", "[ENTER / ESC] Continuar", id="commands-panel")

    def on_mount(self) -> None:
        self._refresh_ui()

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def action_back(self) -> None:
        self.app.pop_screen()

    def _refresh_ui(self) -> None:
        list_view = self.query_one("#awards-list", ListView)
        list_view.clear()
        list_view.border_title = " PREMIAÇÕES FINANCEIRAS DA TEMPORADA "

        if not self.awards_result or not self.awards_result.awards:
            list_view.append(ListItem(Static("As premiações serão calculadas ao final da temporada.")))
            self.query_one("#highlights-panel", DosPanel).update("Temporada em andamento.")
            self.query_one("#totals-panel", DosPanel).update("Nenhum prêmio distribuído ainda.")
            return

        totals_per_team: dict[str, int] = {}
        golden_boot_text = "Nenhum"

        for award in self.awards_result.awards:
            totals_per_team[award.team_name] = totals_per_team.get(award.team_name, 0) + award.amount

            if award.category == "chuteira_de_ouro":
                golden_boot_text = f"{award.player_name} ({award.team_name})"
                line = f"CHUTEIRA DE OURO: {award.player_name:<20} R$ {award.amount:>,}"
            else:
                comp = award.competition[:12]
                cat = "CAMPEÃO" if award.category == "campeao" else "VICE"
                line = f"{comp:<12} {cat:<8} {award.team_name:<20} +R$ {award.amount:>,}"

            list_view.append(ListItem(Static(line)))

        # 2. Atualiza Painel de Destaques
        self.query_one("#highlights-panel", DosPanel).update(
            f"CHUTEIRA DE OURO (Artilheiro do Ano):\n{golden_boot_text}\n\n"
            f"Status do Pagamento: {'APLICADO AO ORÇAMENTO' if self.awards_result.applied else 'PENDENTE'}"
        )

        # 3. Atualiza Totais pagos por Clube
        sorted_totals = sorted(totals_per_team.items(), key=lambda x: x[1], reverse=True)
        totals_lines = ["MAIORES FATURAMENTOS EM PREMIAÇÕES:", ""]
        for team_name, total_val in sorted_totals[:5]:
            totals_lines.append(f"{team_name:<20} +R$ {total_val:>,}")

        self.query_one("#totals-panel", DosPanel).update("\n".join(totals_lines))
