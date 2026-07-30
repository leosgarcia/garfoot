# STATUS.md

> **Nota**: Para decisões de regras de negócio de funcionalidades implementadas e especificações para o futuro, consulte o arquivo [DESIGN_DECISIONS.md](file:///home/leonardo/projects/garfoot/DESIGN_DECISIONS.md).

## 1. Visão Geral

Garfoot é um jogo de gerenciamento de futebol em Python, com inspiração retrô/DOS (estilo Elifoot II) e foco em simulação de campeonatos, elencos e partidas por texto.

Estado atual do projeto:
- **Save/Load**: Implementado (`SaveManager`, `GameState`, persistência atômica e nome personalizado no Novo Jogo).
- **Tela de Abertura / Splash Screen**: Implementada (`SplashOpeningScreen` estilo retrô DOS, banner ASCII "GARFOOT" simétrico, autoria de Leonardo Garcia, grupos de recursos, efeito de boot em cascata e prompt piscando).
- **Carreira Jogável em Textual**: Implementada (Hub da Temporada com 3 colunas, tabela de classificação com 20 times alinhados, ordenação estrita de elenco por Goleiro/Defesa/Meio/Atacante com divisórias, atalhos F1-F7, atalhos numéricos e de letras, simulação com cores e ritmos de partida ajustados).
- **Audit Fixes Concluídos (AUD-FIX-01 a AUD-FIX-05)**:
  - `AUD-FIX-01`: Documentação saneada (`STATUS.md` e `DESIGN_DECISIONS.md`).
  - `AUD-FIX-02`: Seeds determinísticas SHA-256 sem `hash()`.
  - `AUD-FIX-03`: Ledger de idempotência financeira e histórica (`IdempotencyLedger`).
  - `AUD-FIX-04`: Validação transacional de transferências sem estados parciais (`TransferFailureReason`).
  - `AUD-FIX-05`: Simulação longa econômica sem UI por 5+ temporadas e gerador de relatório (`scripts/audit_simulate_seasons.py`).
- **Temporada Base e Orquestração**: Implementadas (`SeasonOrchestrator`, pontos corridos em 4 divisões, Copa do Brasil com fase preliminar e Super Campeão).
- **Dataset Real de Clubes**: Existente (`data/brazil_2026_clubs.json` com 80 clubes das Séries A, B, C e D).
- **Domínio Avançado**: Economia avançada, contratos e rescisão, mercado de transferências, política de transferência da CPU, saúde financeira e Fair Play, patrocínios, despesas operacionais, comissão técnica/chicotada psicológica, lesões, substituições, estatísticas/rankings, premiações e centro de notícias implementados.
- **Migração PySide6**: Iniciada em `garfoot/ui_qt/` como camada paralela à TUI Textual, com esqueleto mínimo de `QApplication` + `QMainWindow` + `QStackedWidget` validado em modo offscreen.

## 2. Arquitetura Implementada

### Núcleo Inicial de Domínio

| Arquivo | Principais classes/funções | Responsabilidade | Dependências internas |
|---|---|---|---|
| `garfoot/domain/enums.py` | `PlayerPosition`, `MatchStatus` | Enums compartilhados para posição de jogador e estado de partida. | Nenhuma |
| `garfoot/domain/player.py` | `Player`, `MIN_ATTRIBUTE`, `MAX_ATTRIBUTE` | Modelo de jogador, validação básica, cálculo de `overall`, ajustes de moral/forma e serialização. | `garfoot.domain.enums.PlayerPosition` |
| `garfoot/domain/stadium.py` | `Stadium` | Modelo de estádio e estimativa de ocupação/renda de bilheteria. | Nenhuma |
| `garfoot/domain/team.py` | `Formation`, `Team` | Modelo de time, elenco, orçamento, compra/venda, escalação, moral média, renda de mando e serialização. | `garfoot.domain.player.Player`, `garfoot.domain.stadium.Stadium` |
| `garfoot/domain/league.py` | `MatchFixture`, `LeagueStanding`, `Championship` | Liga isolada de pontos corridos, fixtures, resultados e tabela ordenada. | `garfoot.domain.enums.MatchStatus`, `garfoot.domain.team.Team` |
| `garfoot/domain/season.py` | `LeagueTier`, `NextSeasonComposition`, `apply_promotion_relegation` | Regra pura de fim de temporada para acesso/rebaixamento entre Séries A, B, C e D (4 séries). | `garfoot.domain.league.LeagueStanding` |
| `garfoot/domain/player_progression.py` | `MatchOutcome`, `apply_post_match_fatigue`, `apply_post_match_morale`, `apply_season_aging` | Regras puras de fadiga, moral, envelhecimento e aposentadoria de jogadores. | `garfoot.domain.player.Player` |
| `garfoot/domain/season_progression.py` | `apply_season_team_progression` | Aplica o envelhecimento ao elenco do time ao fim da temporada e promove jovens da base em caso de aposentadoria. | `garfoot.domain.player_progression`, `garfoot.domain.team.Team` |
| `garfoot/domain/round_robin.py` | `generate_round_robin_schedule` | Algoritmo puro de geração de calendários de pontos corridos (Berger/Circle Method) para turno e returno. | `garfoot.domain.league.MatchFixture` |
| `garfoot/domain/prizes.py` | `CompetitionType`, `PrizeCategory`, `CompetitionPrize`, `PrizeStructure` | Estrutura de premiação por competição, categoria e prêmios de final de temporada. | Nenhuma |

### Módulos Atuais do Domínio

| Arquivo | Principais classes/funções | Responsabilidade | Status |
|---|---|---|---|
| `contract.py` | `Contract` | Modelo imutável de contrato do atleta com vigência, proteção e cláusula de rescisão (`release_clause`). | Implementado |
| `economy.py` | `calculate_player_market_value`, `calculate_release_clause` | Fórmulas puras não-lineares de valor de mercado e cláusula de rescisão. | Implementado |
| `economic_context.py` | `EconomicContext` | Contexto econômico global, inflação acumulada e reajuste por índice. | Implementado |
| `finance.py` | `StadiumUpgradeProject`, `BankLoan`, `calculate_upgrade_cost` | Finanças do clube, ampliação de estádio e empréstimos bancários. | Implementado |
| `club_finance.py` | `ClubFinancialProfile`, `initialize_team_budget` | Orçamentos iniciais balanceados por série e perfil financeiro. | Implementado |
| `squad_rules.py` | `SquadLimitConfig`, `validate_squad_limits`, `WageHealth` | Limites de elenco (18 a 30 atletas), diagnóstico por posição e folha salarial. | Implementado |
| `transfer_market.py` | `TransferListing`, `execute_player_purchase`, `execute_release_clause_purchase` | Mercado de transferências, compras comuns e compras por rescisão. | Implementado |
| `cpu_transfer_policy.py` | `ClubTransferProfile`, `execute_cpu_transfer_window` | Política determinística da CPU para compra/venda de atletas com proteção ao humano. | Implementado |
| `contract_lifecycle.py` | `FreeAgentPool`, `process_end_of_season_contracts` | Expiração contratual, renovações da CPU e pool de agentes livres. | Implementado |
| `match_appeal.py` | `MatchAppealContext`, `calculate_match_appeal_factor` | Apelo do adversário, nível de rivalidade e importância na ocupação do estádio. | Implementado |
| `sponsorship.py` | `SponsorshipContract`, `ClubSponsorshipPortfolio` | Contratos de patrocínio, receita por rodada e bônus por vitória. | Implementado |
| `operating_expenses.py` | `OperatingExpense`, `process_round_operating_expenses` | Despesas operacionais recorrentes, manutenção de estádio e burn rate. | Implementado |
| `financial_health.py` | `FinancialHealthStatus`, `ClubFinancialState`, `calculate_financial_health_report` | Score de saúde financeira, crise, punições graduais e Fair Play Financeiro. | Implementado |
| `news.py` | `NewsItem`, `NewsCenter`, `create_transfer_news` | Centro de notícias da temporada, prioridades, categorias e pruning. | Implementado |
| `statistics.py` | `SeasonStatisticsManager`, `build_top_scorers_ranking` | Estatísticas acumuladas de jogadores/técnicos e rankings ordenados. | Implementado |
| `coach.py` | `Coach`, `CoachBounceEffect`, `calculate_coach_pressure` | Treinadores, pressão da diretoria, demissões e "chicotada psicológica". | Implementado |
| `game_settings.py` | `GameSettings`, `MatchSpeed`, `SoundMode` | Opções de velocidade de partida e configurações de áudio. | Implementado |
| `game_state.py` | `GameState` | Estado global consolidado do jogo serializável em JSON. | Implementado |

### Engine de Simulação

| Arquivo | Principais classes/funções | Responsabilidade | Dependências internas |
|---|---|---|---|
| `garfoot/engine/events.py` | `MatchEventType`, `GoalEvent`, `CardEvent`, `InjuryEvent`, `SubstitutionEvent` | Tipos imutáveis de eventos gerados pela simulação. | Nenhuma |
| `garfoot/engine/probability.py` | `TeamMatchProfile`, `build_team_profile`, `calculate_possession`, `calculate_goal_chance` | Funções puras de rating, posse e chance de gol. | `PlayerPosition`, `Player`, `Formation`, `Team` |
| `garfoot/engine/match_engine.py` | `MatchResult`, `simulate_match` | Simulação minuto a minuto de uma partida, determinística por seed. | `PlayerPosition`, `Player`, `Team`, eventos, `probability.py` |
| `garfoot/engine/match_progression.py` | `apply_post_match_progression` | Aplica fadiga, lesões, descanso e moral pós-partida. | `garfoot.domain.player_progression`, `MatchResult` |
| `garfoot/engine/commentary.py` | `narrate_event`, `narrate_match`, `narrate_summary` | Converte eventos e resultados em texto narrativo. | `events.py`, `match_engine.py` |

### Interface (UI)

| Arquivo | Principais classes/funções | Responsabilidade | Dependências internas |
|---|---|---|---|
| `garfoot/ui/app.py` | `GarfootApp`, `main` | Aplicação Textual com paleta retrô DOS. | telas de `garfoot.ui.screens` |
| `garfoot/ui/audio.py` | `SoundEvent`, `play_ui_sound` | Efeitos de som em UI com fallback silencioso absoluto. | `game_settings.py` |
| `garfoot/ui/screens/season_hub.py` | `SeasonHubScreen` | Hub principal de temporada estilo Elifoot II (3 colunas). | widgets e telas da UI |
| `garfoot/ui/screens/market.py` | `TransferMarketScreen` | Tela de mercado de transferências. | `transfer_market.py` |
| `garfoot/ui/screens/news.py` | `NewsScreen` | Tela do Centro de Notícias, registrada em `GarfootApp.SCREENS`. | `news.py` |
| `garfoot/ui/screens/rankings.py` | `RankingsScreen` | Tela de rankings de artilheiros e treinadores, registrada em `GarfootApp.SCREENS`. | `statistics.py` |
| `garfoot/ui/screens/contracts.py` | `ContractsScreen` | Tela de contratos e agentes livres, registrada em `GarfootApp.SCREENS`. | `contract_lifecycle.py`, `squad_rules.py` |
| `garfoot/ui/screens/board_inbox.py` | `BoardInboxScreen` | Tela interativa da Caixa de Entrada da Diretoria. | `board_inbox.py` |
| `garfoot/ui_qt/app.py` | `build_app`, `main` | Ponto de entrada PySide6 paralelo: `QApplication` e janela principal. | `garfoot.ui_qt.main_window`, `theme` |
| `garfoot/ui_qt/main_window.py` | `GarfootMainWindow` | Esqueleto de janela Windows clássica com menu bar, status bar e `QStackedWidget`. | PySide6 |
| `garfoot/ui_qt/theme.py` | `classic_windows_qss` | Tema QSS cinza/azul inspirado em aplicativos Windows 95/98. | Nenhuma |

## 3. Regras de Negócio Implementadas

Para o detalhamento completo e histórico consolidado das regras de negócio de cada módulo (Overall, Partidas, Premiações, Economia, Finanças, Lesões, Substituições, Treinadores, Estatísticas, Patrocínios, Saúde Financeira, Notícias e Caixa de Entrada da Diretoria), consulte [DESIGN_DECISIONS.md](file:///home/leonardo/projects/garfoot/DESIGN_DECISIONS.md).

## 4. Dataset de Dados Reais

Arquivo atual: `data/brazil_2026_clubs.json`.
- Total de clubes no JSON: `80` (Série A: 20, Série B: 20, Série C: 20, Série D: 20).
- Dados estruturais preenchidos nos 80 clubes.

## 5. Testes e Validação

Comandos de validação executados e aprovados:

```bash
python3 -m compileall garfoot scripts
.venv/bin/pytest -m "not slow" --tb=short -q
```

**Resultado de Validação mais recente**:
- `285 passed, 2 deselected` em 3.26s com `QT_QPA_PLATFORM=offscreen`.
- `compileall` concluído sem erros de sintaxe ou importação.
- Novos testes: `tests/test_ui_data.py`, `tests/test_ui_screens.py` e `tests/test_ui_qt_app.py`.

Navegação pela TUI:
```bash
.venv/bin/python -m garfoot.ui.app
```

Smoke test da UI Qt sem display gráfico:
```bash
QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_ui_qt_app.py -q
```

Entrada manual da UI Qt, quando houver ambiente gráfico:
```bash
.venv/bin/python -m garfoot.ui_qt.app
```

## 6. Histórico de Blocos Implementados

| Bloco / Tarefa | Módulo / Funcionalidade | Descrição |
|---|---|---|
| Bloco 01 - 04 | Core Domain & Engine | Jogadores, Times, Estádios, Ligas e Simulação minuto a minuto por seed. |
| Bloco 05 - 07 | Temporada & TUI | Acesso/Rebaixamento 4 divisões, TUI Textual inicial, Sorteio e Tabela. |
| Bloco 08 - 10 | Save/Load & Economia | `SaveManager`, Mercado v1, Valor de Mercado não-linear e Contratos. |
| Bloco 11 - 12 | Finanças & Lesões | Upgrade de estádio, Empréstimos, Ajustes de velocidade TUI e Lesões R3. |
| Bloco 13 - 14 | Substituições & Técnicos | 5 substituições por jogo, Treinadores, Pressão e Chicotada Psicológica. |
| Bloco 15 - 16 | Rankings & Premiações | Estatísticas acumuladas, Artilharia, Premiações idempotentes e Chuteira de Ouro. |
| Bloco 17 - 18 | Rescisão & Inflação | Cláusulas de Rescisão (1.5x-8.0x), Compra forçada e Contexto Econômico Global. |
| Bloco 19 - 20 | CPU Policy & Finanças | Transferências da CPU com perfis, Saúde Financeira, Notícias e Hub 3 colunas. |
| AUD-FIX 01-05 | Auditorias Técnicas | Determinismo SHA-256, IdempotencyLedger, Validação Transacional e Simulação 5+ temp. |
| Bloco 21 | Caixa de Entrada Diretoria | Módulo `board_inbox.py`, 5 tipos de comunicado, decisões interativas e TUI. |
| Pré-Migração Qt | Correções da TUI | `load_teams_by_series` filtrando corretamente, `ContractsScreen.__init__` corrigido, telas `contracts`/`news`/`rankings` registradas e telas parametrizadas documentadas. |
| Migração Qt Bloco 1 | Esqueleto PySide6 | Nova camada paralela `garfoot/ui_qt/` com `QApplication`, `QMainWindow`, `QStackedWidget`, tema clássico e teste offscreen. |

## 7. Pendências Reais e Próximos Blocos

### Próximos Blocos Planejados (Funcionalidades)

- **Migração PySide6 Bloco 2 — Splash + Menu Principal**: Próxima etapa da camada `garfoot/ui_qt/`, ainda sem tocar domínio/engine/persistência.
- **Telas auxiliares parametrizadas**: `SeasonAwardsScreen` e `RoundResultsScreen` existem, mas não são rotas simples em `GarfootApp.SCREENS` porque exigem dados no construtor; devem ser abertas como instâncias quando o fluxo correspondente estiver ativo.
- **Bloco 22 — Metas da Temporada e Avaliação da Diretoria**: Expectativas de desempenho por Série e risco de demissão do treinador humano.
- **Sistemas Futuros**:
  - Reputação do clube e do técnico;
  - Moral individual de vestiário e insatisfação de reservas;
  - Evolução focada e treinos específicos;
  - Categorias de base avançadas e Scouting/Olheiros;
  - Histórico de carreiras e Hall da Fama.

## 8. Diretrizes de Arquitetura

- A camada de domínio permanece 100% pura (sem I/O, sem Textual, sem dependência do motor).
- A engine de partida permanece 100% pura e determinística por seed.
- A migração PySide6 convive em paralelo com a TUI Textual: `garfoot/ui/` continua existindo, e `garfoot/ui_qt/` deve avançar tela por tela.
- As regras financeiras, salariais e de fair play não travam o jogo em saldo devedor, aplicando punições desportivas e administrativas progressivas.
- Dados de clubes brasileiros servem ao desenvolvimento interno/privado do projeto Garfoot.
