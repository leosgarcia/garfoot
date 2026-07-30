# Plano de Migração da UI: Textual para PySide6

Status: aprovado. Bloco 1 — Esqueleto Qt mínimo concluído.

## 1. Objetivo

Migrar a interface atual do Garfoot de uma TUI em Textual para uma interface desktop em PySide6, com visual de programa Windows clássico: janela principal única, menus, tabelas, abas e caixas de diálogo. A migração deve ficar restrita à camada de interface; `garfoot/domain/`, `garfoot/engine/` e `garfoot/persistence/` não devem ser alterados por causa da UI.

## 2. Inventário da UI Textual Atual

### Arquivos-base

| Arquivo | Papel atual | Reaproveitamento na migração |
|---|---|---|
| `garfoot/ui/app.py` | Define `GarfootApp`, CSS global, bindings globais e registro de telas Textual. | Não reaproveitar diretamente; vira `garfoot/ui_qt/app.py` com `QApplication` e `QMainWindow`. |
| `garfoot/ui/data.py` | Carrega `data/brazil_2026_clubs.json`, converte clubes em `Team`, gera elencos temporários e orçamentos. | Reaproveitável por não depender de Textual. O filtro `load_teams_by_series` foi corrigido antes da migração e é coberto por teste. |
| `garfoot/ui/audio.py` | Mapeia eventos da engine para eventos sonoros e executa beep/terminal. | Reaproveitar a lógica de mapeamento; trocar o backend de reprodução para `QSoundEffect` ou `QMediaPlayer`. |
| `garfoot/ui/demo.py` | Cria times fictícios para partida demo. | Reaproveitável. |
| `garfoot/ui/widgets/dos.py` | Widgets Textual (`DosPanel`, `NumberedMenu`, `Spacer`). | Não reaproveitar diretamente; criar widgets Qt equivalentes ou estilo global QSS. |

### Telas existentes

| Tela Textual | Função atual | Dados consumidos | Equivalente Qt proposto |
|---|---|---|---|
| `SplashOpeningScreen` (`splash.py`) | Abertura com banner, créditos, recursos e prompt animado. | Não consome domínio; apenas textos estáticos e timers. | `QSplashScreen` ou `QWidget` inicial no `QStackedWidget`, com `QTimer`, banner em fonte monoespaçada e botão/atalho para avançar. |
| `MainMenuScreen` (`main_menu.py`) | Menu principal: novo jogo, carregar, continuar, clubes, tabela, demo e sair. | Lê `current_game_state` do app. | Página inicial no `QStackedWidget` ou tela inicial da `QMainWindow`, com botões grandes, menu bar e atalhos. |
| `NewGameScreen` (`new_game.py`) | Escolha obrigatória de clube da Série D, nome do save, criação de `GameState`, `SeasonOrchestrator`, `Championship`, `KnockoutCup` e save inicial. | `load_clubs`, `load_teams`, `GameState`, `Championship`, `LeagueTier`, `SeasonOrchestrator`, `KnockoutCup`, `SaveManager`. | Página/diálogo de novo jogo com `QListWidget` ou `QTableView`, painel de detalhe e `QLineEdit` para nome do save. |
| `LoadGameScreen` (`load_game.py`) | Lista saves, mostra metadados, carrega save e abre hub. | `SaveManager`, `SaveMetadata`. | `QDialog` ou página de carregar jogo com `QTableWidget/QTableView` e painel de detalhes. |
| `SeasonHubScreen` (`season_hub.py`) | Hub da carreira: status, clube, próxima rodada, classificação, notícias e ações centrais. | `GameState`, `LeagueTier`, `MatchStatus`, `MatchFixture`, `SaveManager`, notícias do estado. | Página principal pós-save em `QMainWindow`, com `QDockWidget` ou painéis fixos: resumo, rodada, tabela, notícias e toolbar/menu. |
| `ClubsScreen` (`clubs.py`) | Lista clubes por série e mostra detalhes do dataset. | `load_clubs`. | Janela/página de clubes com `QListWidget` à esquerda, filtros por série em `QComboBox`/abas e `QTabWidget` de detalhes. |
| `StandingsScreen` (`standings.py`) | Mostra tabelas de duas divisões por tela: A/B ou C/D. | `GameState`, `LeagueTier`, `Championship.standings()`. | Página de classificação com `QTabWidget` por série ou duas `QTableView` lado a lado, preservando alternância A/B e C/D. |
| `MatchPrepScreen` (`match_prep.py`) | Escalação e tática antes da rodada; escolhe titulares e formação. | `GameState`, `LeagueTier`, `Team`, `Formation`, `Player`, `PlayerPosition`. | Página de preparação com `QTableView` de elenco, botões/radio para formações, painel de clube, confronto e finanças. |
| `LiveMatchScreen` (`live_match.py`) | Simula a rodada ao vivo em ticks; mostra placares por série, toca sons, grava estado e aplica progressão. | `GameState`, `LeagueTier`, `MatchStatus`, `MatchFixture`, `simulate_match`, `MatchResult`, `GoalEvent`, `apply_post_match_progression`, estatísticas, `SaveManager`, `audio.py`. | Página de rodada ao vivo com `QTimer`, duas tabelas de placares, painel de tempo e botões A/B, C/D, acelerar e avançar. |
| `MatchScreen` (`match.py`) | Partida demo entre clubes do dataset ou times fictícios; mostra narração e estatísticas. | `load_teams`, `make_demo_team`, `simulate_match`, `narrate_match`, `narrate_summary`. | Página de partida demo com `QTextEdit`/`QPlainTextEdit` para narração e painel lateral de placar. |
| `TransferMarketScreen` (`market.py`) | Lista jogadores no mercado, filtra por posição e compra jogador. | `GameState`, `PlayerPosition`, `TransferListing`, `get_available_transfer_market`, `filter_transfer_listings`, `execute_player_purchase`, `SaveManager`. | Página de mercado com `QTableView`, filtros por posição em toolbar/combobox, painel de detalhes e ação Comprar. |
| `ContractsScreen` (`contracts.py`) | Renova contratos e contrata agentes livres. | `GameState`, `Player`, `renew_player_contract`, `sign_free_agent`, `SaveManager`, regras de folha salarial. | Página com `QTabWidget`: Elenco/Contratos e Agentes Livres; detalhes à direita; botões Renovar/Contratar. Observação: tela registrada em `GarfootApp.SCREENS` após correção pré-migração. |
| `OptionsScreen` (`options.py`) | Configura velocidade da partida e liga/desliga som. | `GameState`, `MatchSpeed`, `SaveManager`. | `QDialog` de opções com `QComboBox` de velocidade, `QCheckBox` de som e botões Aplicar/Cancelar. |
| `BoardInboxScreen` (`board_inbox.py`) | Caixa de mensagens da diretoria; permite decisões em opções pendentes. | `GameState`, `BoardMessage`, `BoardMessageOption`, `BoardMessageStatus`, `BoardMessageType`, `process_board_decision`. | Página/diálogo com lista de mensagens, painel de conteúdo e botões para opções de decisão. |
| `NewsScreen` (`news.py`) | Centro de notícias com filtros e marcação como lida. | `GameState`, `NewsCenter`, `NewsCategory`, `NewsPriority`. | Página de notícias com `QListWidget/QTableView`, filtros por categoria e painel de leitura. Observação: registrada em `GarfootApp.SCREENS` após correção pré-migração. |
| `RankingsScreen` (`rankings.py`) | Rankings/estatísticas de artilheiros e treinadores. | `GameState`, estatísticas persistidas no estado. | Página com `QTabWidget` para artilheiros, treinadores e outras visões estatísticas. Observação: registrada em `GarfootApp.SCREENS` após correção pré-migração. |
| `SeasonAwardsScreen` (`season_awards.py`) | Premiações finais da temporada. | `GameState`, `SeasonAwardsResult`. | Diálogo/página de fim de temporada com tabela de prêmios, destaques e totais por clube. Observação: não está registrada em `GarfootApp.SCREENS` hoje. |
| `RoundResultsScreen` (`round_results.py`) | Mostra resultados de uma rodada e detalhes de uma partida selecionada. | `MatchFixture`, `MatchResult`, `narrate_summary`. | Página/diálogo pós-rodada com tabela de partidas e painel de súmula. Observação: não está registrada em `GarfootApp.SCREENS` hoje. |

## 3. Navegação Atual e Estratégia Qt

A navegação Textual atual usa `App.SCREENS` com nomes de rota (`splash`, `main`, `new_game`, `load_game`, `clubs`, `standings`, `match`, `match_prep`, `season_hub`, `live_match`, `market`, `options`, `board_inbox`) e também alguns `push_screen()` com instâncias criadas diretamente (`RankingsScreen`, `NewsScreen`, `LiveMatchScreen`). O estado ativo é guardado dinamicamente em `self.app.current_game_state`.

Para PySide6, a recomendação é usar uma `QMainWindow` única com `QStackedWidget` como área central. Isso preserva a sensação de programa único clássico, como WinRAR/Elifoot 98, em vez de várias janelas soltas. Telas auxiliares pontuais, como opções, confirmação de compra, confirmação de save e erro de carregamento, podem ser `QDialog` modais.

Estrutura sugerida:

```text
garfoot/ui_qt/
├── __init__.py
├── app.py              # QApplication + main()
├── main_window.py      # QMainWindow, menu bar, toolbar, status bar, QStackedWidget
├── app_state.py        # estado da UI: current_game_state, seleção atual, helpers de navegação
├── data.py             # reexporta ou adapta garfoot.ui.data sem dependência Qt
├── audio.py            # backend Qt para sons, reaproveitando o mapeamento de eventos
├── theme.py            # QSS Windows clássico / Win98 / Garfoot
├── widgets/
│   ├── __init__.py
│   ├── classic_panel.py
│   ├── money_label.py
│   └── table_models.py
└── screens/
    ├── splash.py
    ├── main_menu.py
    ├── new_game.py
    ├── load_game.py
    ├── season_hub.py
    ├── clubs.py
    ├── standings.py
    ├── match_prep.py
    ├── live_match.py
    ├── match_demo.py
    ├── market.py
    ├── contracts.py
    ├── options.py
    ├── board_inbox.py
    ├── news.py
    ├── rankings.py
    ├── season_awards.py
    └── round_results.py
```

Durante a transição, manter `garfoot/ui/` intacto e criar `garfoot/ui_qt/` em paralelo. Só depois de a UI Qt cobrir os fluxos principais e ser aprovada visualmente, decidir se a TUI Textual vira legado, fallback ou é removida. Essa convivência reduz risco e permite comparar o sabor DOS vs Windows clássico.

## 4. Dados, Áudio e Persistência

### Dados

`garfoot/ui/data.py` não importa Textual. Ele usa JSON, `Path`, `Random`, `typing` e modelos/funções de domínio (`Player`, `Team`, `Stadium`, `PlayerPosition`, `stable_random`, `initialize_team_budget`). Pode ser reaproveitado pela UI Qt como camada de acesso/conversão de dados.

Atualização pré-migração: `load_teams_by_series(series)` agora filtra os dicionários crus do JSON antes de convertê-los para `Team`, mantendo a série fora do domínio. O helper `_get_team_series` consulta o JSON por nome do clube e não retorna mais `True` indiscriminadamente.

### Áudio

`garfoot/ui/audio.py` separa bem duas coisas:

- mapeamento puro de evento da engine para `SoundEvent` (`map_engine_event_to_sound_event`);
- reprodução concreta (`play_ui_sound`), hoje via `app.bell()` ou `sys.stdout.write("\a")`.

Na UI Qt, o mapeamento pode ser reaproveitado. O mecanismo de reprodução deve virar um backend Qt usando `QSoundEffect` para efeitos curtos ou `QMediaPlayer` para arquivos maiores. A regra de “quando tocar cada som” deve continuar nas telas de simulação ao vivo, não na engine.

### Settings e save/load

`garfoot/domain/game_settings.py` é puro: dataclasses/enums, `to_dict`/`from_dict`, sem Textual.

`garfoot/persistence/save_manager.py` também não depende de Textual. Ele faz I/O de JSON local, escrita atômica, listagem e carregamento de `GameState`. Pode ser usado sem alteração na UI Qt. A nova UI deve apenas trocar `app.notify` por `QMessageBox`, barra de status ou diálogo próprio.

## 5. Ordem Incremental de Migração

1. Esqueleto Qt mínimo — concluído
   - Criados `ui_qt/app.py`, `main_window.py`, `theme.py`, `screens/__init__.py` e `widgets/__init__.py`.
   - A janela inicial usa `QApplication`, `QMainWindow`, menu bar, status bar e `QStackedWidget` central.
   - Validado em modo sem display com `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_ui_qt_app.py -q`.

2. Splash + Menu Principal — concluído
   - Migrados `SplashOpeningScreen` e `MainMenuScreen` para `garfoot/ui_qt/screens/`.
   - A splash mantém logo ASCII monoespaçado, créditos e prompt piscando via `QTimer`.
   - O menu principal usa botões verticais grandes em estilo instalador Windows clássico.
   - Destinos ainda não migrados abrem placeholders distintos e testáveis.
   - Menu bar superior inclui `Arquivo > Sair` e `Ajuda > Sobre`.
   - Validado em modo offscreen por `tests/test_ui_qt_app.py`.

3. Clubes
   - Migrar `ClubsScreen` usando `garfoot.ui.data.load_clubs`.
   - Meta: primeira tela com dados reais e lista/detalhe; ótimo ponto de feedback visual.
   - Risco baixo, sem save nem mutação de estado.

4. Carregar Jogo e Novo Jogo
   - Migrar `LoadGameScreen` e `NewGameScreen`.
   - Meta: criar/carregar `GameState` e entrar no hub.
   - Risco médio, usa `SaveManager`, `SeasonOrchestrator`, `Championship`, `KnockoutCup`.

5. Hub da Temporada
   - Migrar `SeasonHubScreen`.
   - Meta: ter a tela central da carreira em Qt.
   - Dependência: save ativo funcionando.

6. Classificação
   - Migrar `StandingsScreen` com tabelas reais em `QTableView`.
   - Meta: substituir texto monoespaçado por tabela Windows clássica, sem perder densidade.

7. Preparação de Partida
   - Migrar `MatchPrepScreen`.
   - Meta: escalação, seleção de titulares e formações em UI de tabela/botões.
   - Risco médio, altera `Team.formation` e `starting_player_names` no estado.

8. Partida Demo e Rodada Ao Vivo
   - Migrar `MatchScreen` e `LiveMatchScreen`.
   - Meta: validar `QTimer`, narração, placares simultâneos, sons e progressão de rodada.
   - Risco maior por envolver simulação, progressão, estatísticas, save e áudio.

9. Mercado, Contratos e Financeiro do Elenco
   - Migrar `TransferMarketScreen` e `ContractsScreen`.
   - Meta: operações mutáveis de compra, renovação e contratação livre com confirmações.
   - Risco médio/alto por mexer em orçamento, elenco e persistência.

10. Notícias, Diretoria, Rankings, Premiações e Resultados
    - Migrar `NewsScreen`, `BoardInboxScreen`, `RankingsScreen`, `SeasonAwardsScreen` e `RoundResultsScreen`.
    - Meta: completar telas auxiliares e encerramento de rodada/temporada.

11. Polimento final
    - Atalhos globais, menus clássicos, ícones simples se desejado, QSS final, testes manuais de fluxo completo e empacotamento experimental.

## 6. Estilo Visual Qt

Direção visual recomendada:

- `QMainWindow` com menu bar: Jogo, Temporada, Clube, Competição, Mercado, Opções, Ajuda.
- Toolbar com botões pequenos e texto curto, estilo Windows 95/98.
- `QStatusBar` com temporada, rodada, clube e caixa disponível.
- `QTableView`/`QTableWidget` para elenco, classificação, mercado, saves e rankings.
- `QTabWidget` para detalhes de clube, contratos e rankings.
- Fonte monoespaçada opcional em áreas de narração e placares, para manter nostalgia.
- QSS com cinza clássico, azul escuro em seleção, bordas simples e pouco gradiente.

## 7. Empacotamento Windows

PySide6 aumenta bastante o tamanho do build em comparação com Textual. Com PyInstaller, a complexidade é média:

- adicionar `PySide6` como dependência opcional ou principal da UI Qt;
- incluir `data/brazil_2026_clubs.json` como arquivo de dados;
- incluir assets de som quando existirem;
- ajustar paths com helper compatível com `_MEIPASS` do PyInstaller;
- testar `--onedir` primeiro, depois avaliar `--onefile`;
- esperar um executável/pasta final significativamente maior, possivelmente dezenas a centenas de MB, por causa das DLLs/plugins Qt.

Isso não deve ser feito antes de a UI Qt estar funcional. A primeira meta de distribuição deve ser `onedir`, mais fácil de depurar.

## 8. Decisões Importantes

- Não substituir `garfoot/ui/` imediatamente. Criar `garfoot/ui_qt/` em paralelo.
- Não tocar em `garfoot/domain/` nem `garfoot/engine/` por causa da UI.
- Reaproveitar `SaveManager`, `GameSettings`, `GameState` e a maior parte de `garfoot/ui/data.py`.
- Trocar apenas adaptadores de apresentação: Textual widgets/screens por PySide6 widgets/pages/dialogs.
- Usar `QStackedWidget` dentro de uma `QMainWindow` única como navegação principal.
- Usar `QDialog` somente para fluxos pontuais e modais.
- Tratar `audio.py` como duas camadas: mapeamento reaproveitável e player Qt novo.
- `load_teams_by_series` já foi corrigido e testado antes do início da camada Qt.
