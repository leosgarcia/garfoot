# Decisões de Design (DESIGN_DECISIONS.md)

Este documento registra as decisões de design aprovadas, implementadas, pendentes ou em auditoria no Garfoot.

---

## Legenda de Status

- `[IMPLEMENTADO]`: Decidido e implementado no código base.
- `[PARCIAL]`: Funcionalidade com núcleo implementado, porém com expansões pendentes.
- `[PENDENTE]`: Especificação pendente ou aguardando bloco de desenvolvimento.
- `[PLANEJADO]`: Funcionalidade futura planejada no roadmap.
- `[AUDITORIA]`: Item identificado em auditoria técnica que requer saneamento/correção (AUD-FIX).
- `[HISTÓRICO]`: Registro histórico consolidado de decisões anteriores.

---

## DD-001: Overall de Jogadores, Evolução e Promoção da Base

- **Status**: `[IMPLEMENTADO]`
- **Regras Implementadas**:
  - **Fadiga (`fitness`)**: Perda de forma física pós-partida e recuperação em descanso (`apply_post_match_fatigue`).
  - **Moral (`morale`)**: Variação por vitórias, empates, derrotas e gols (`apply_post_match_morale`).
  - **Evolução e Declínio**: Evolução de jovens ($< 23$ anos) e declínio de veteranos ($> 31$ anos) (`apply_season_aging`).
  - **Promoção da Base**: Aposentadoria de veteranos (idade $> 38$ anos e `overall < 50`) promove jovem da base (17-19 anos) para manter o tamanho do elenco (`apply_season_team_progression`).

---

## DD-002: Mercado de Transferências e Listagem da CPU

- **Status**: `[IMPLEMENTADO]`
- **Regras Implementadas**:
  - **Listagem de Reservas**: Atletas reservas da CPU sem bloqueio contratual entram no mercado a 95%-110% do valor de mercado.
  - **Filtros Puramente Funcionais**: Filtros por posição, faixa de overall, preço máximo e idade em `filter_transfer_listings`.
  - **Execução de Compra**: Débito/crédito financeiro, troca de elenco e contrato de 3 anos (protegido no 1º ano).
  - **Interface TUI**: Tela `TransferMarketScreen` em Textual.

---

## DD-003: Valor de Mercado e Salário dos Jogadores

- **Status**: `[IMPLEMENTADO]`
- **Regras Implementadas**:
  - **Fórmula Não-Linear**: $\text{Valor Base} = 300.000 \times (overall / 50)^{5.0} \times \text{FatorIdade} \times \text{FatorPosicao} \times \text{IndexEconomico}$.
  - **Fator Idade**: Jovem $+8\%$/ano ($<23$), neutro ($23-29$), declínio $-12\%$/ano ($>29$).
  - **Fator Posição**: Atacante ($1.15$), Meio-campo ($1.05$), Defensor ($0.95$), Goleiro ($0.85$).
  - **Salário**: Fixo no contrato durante a vigência ($\approx 12\%$ do valor de mercado no momento da assinatura).

---

## DD-004: Modelo Contratual e Bloqueio de Transferências

- **Status**: `[IMPLEMENTADO]`
- **Regras Implementadas**:
  - Modelo `Contract` imutável em `garfoot/domain/contract.py`.
  - Atributos: `years_remaining`, `is_protected`, `protection_years`, `release_clause`.
  - Atletas protegidos ou sem contrato ativado não podem ser transferidos via compra direta comum (`can_be_transferred == False`).

---

## DD-005: Upgrade de Estádio e Empréstimos Bancários

- **Status**: `[IMPLEMENTADO]`
- **Regras Implementadas**:
  - **Upgrade de Estádio**: Custo progressivo $\text{Custo} = 300 \times \text{NovosAssentos} \times (1.0 + \frac{\text{capacidade}}{100.000}) \times \text{IndexEconomico}$. Obras duram 6 rodadas. Teto por divisão: D (25k), C (40k), B (60k), A (90k). Direitos adquiridos (*grandfathering*) garantidos para estádios do dataset maiores que o teto.
  - **Empréstimo Bancário**: Limite baseado na receita anual estimada por Série. Taxa de 15% em 10 parcelas por rodada. Multa de 5% e perda de moral em inadimplência.

---

## DD-006: Orçamento Inicial dos Clubes e Perfis Financeiros

- **Status**: `[IMPLEMENTADO]`
- **Consolidação**: Este item consolida a especificação de caixa inicial.
- **Regras Implementadas**:
  - Módulo `garfoot/domain/club_finance.py`.
  - Tabela base por Série: A (R$ 12M), B (R$ 5M), C (R$ 2M), D (R$ 800k).
  - Multiplicadores por perfil (`LARGE` 1.5x, `MEDIUM` 1.0x, `SMALL` 0.70x, `DEBT_PRESSURED` 0.45x, `DEVELOPING` 0.85x) e bônus por estádio (até +25%).
  - Atribuição idempotente (`initialize_team_budget`) que preserva orçamentos de saves existentes.

---

## DD-007: Limite de Elenco, Massa Salarial e Saúde Salarial

- **Status**: `[IMPLEMENTADO]`
- **Consolidação**: Este item consolida o teto de atletas por time.
- **Regras Implementadas**:
  - Módulo `garfoot/domain/squad_rules.py`.
  - Mínimo operacional: 18 atletas. Faixa ideal: 22 a 26. Teto máximo: 30 atletas.
  - Mínimos por posição: Goleiros (2), Defensores (6), Meio-Campistas (6), Atacantes (4).
  - Classificação da folha salarial (`HEALTHY`, `ATTENTION`, `PRESSURED`, `CRITICAL`). Compras bloqueadas ao atingir 30 atletas ou em situação salarial `CRITICAL`.

---

## DD-008: Rivalidade, Apelo do Adversário e Lotação do Estádio

- **Status**: `[IMPLEMENTADO]`
- **Consolidação**: Este item consolida o apelo em partidas.
- **Regras Implementadas**:
  - Módulo `garfoot/domain/match_appeal.py`.
  - Bônus por rivalidade (`REGIONAL`, `STATE_CLASSIC`, `CITY_CLASSIC`, `HISTORIC`), apelo do rival e importância da partida.
  - Integração em `Stadium.estimate_attendance_rate_with_appeal` respeitando limites de ocupação (piso 20%, teto 95%).

---

## DD-009: Início do Jogador Humano na Série D

- **Status**: `[IMPLEMENTADO]`
- **Regra de Negócio**:
  - O jogador humano começa obrigatoriamente na **Série D**.
  - Garantia de isonomia: Orçamento, elenco e regras do time humano seguem exatamente os mesmos padrões dos demais clubes da Série D.

---

## DD-010: Formato da Série D em Pontos Corridos

- **Status**: `[IMPLEMENTADO]`
- **Decisão**: 20 times em turno e returno (38 rodadas), idêntico às Séries A, B e C, visando coerência da engine.

---

## DD-011: Copa do Brasil com Fase Preliminar (80 Times)

- **Status**: `[IMPLEMENTADO]`
- **Decisão**: 32 piores ranqueados jogam a Fase Preliminar em partida única; 16 vencedores juntam-se aos 48 melhores na Fase Principal (64 times, 6 rodadas mata-mata).

---

## DD-012: Velocidade de Simulação das Partidas

- **Status**: `[IMPLEMENTADO]`
- **Decisão**: Configuração 100% de UI (`MatchSpeed` em `game_settings.py`), sem afetar a engine determinística.

---

## DD-013: Sons de Eventos de Partida em UI

- **Status**: `[IMPLEMENTADO]`
- **Decisão**: Camada pura de UI (`garfoot/ui/audio.py`) com fallback silencioso absoluto em ambientes sem áudio/headless.

---

## DD-014: Sistema de Lesões de Jogadores

- **Status**: `[IMPLEMENTADO]`
- **Regras**: Severidades `MINOR`, `MODERATE` e `SEVERE` em `garfoot/domain/injury.py`. Afastamento em rodadas, bloqueio de escalação e perda temporária de atributos técnicos/fitness.

---

## DD-015: Substituições de Jogadores

- **Status**: `[IMPLEMENTADO]`
- **Regras**: Limite de 5 substituições por partida (`garfoot/domain/substitution.py`), impedimento de reentrada, bloqueio de lesionados e sugestões automáticas para a CPU.

---

## DD-016: Treinadores e "Chicotadas Psicológicas"

- **Status**: `[IMPLEMENTADO]`
- **Regras**: Pressão do cargo, demissão/contratação da CPU e bônus temporário de moral/rating por 3-5 rodadas pós-troca (`garfoot/domain/coach.py`).

---

## DD-017: Rankings Estatísticos de Artilheiros e Treinadores

- **Status**: `[IMPLEMENTADO]`
- **Regras**: Módulo `garfoot/domain/statistics.py` acumulando gols, partidas e desempenho de técnicos por divisão e geral com desempate puro.

---

## DD-018: Premiações Finais da Temporada e Chuteira de Ouro

- **Status**: `[IMPLEMENTADO]`
- **Consolidação**: Consolidado com a estrutura atual de `PrizeStructure.default_brazil_2026`.
- **Regras**: Tabela de prêmios por divisão e prêmio de Artilheiro do Ano. Pagamento estritamente **idempotente** (`applied = True`) para evitar créditos duplicados ao recarregar saves.

---

## DD-019: Cláusula de Rescisão Contratual e Compra Forçada

- **Status**: `[IMPLEMENTADO]`
- **Regras**: Campo `release_clause` em `Contract`. Cálculo de 1.5x a 8.0x do valor de mercado. Permite compra forçada de atletas protegidos mediante pagamento integral da rescisão (`execute_release_clause_purchase`).

---

## DD-020: Inflação e Contexto Econômico Global

- **Status**: `[IMPLEMENTADO]`
- **Regras**: `EconomicContext` com inflação de 5%/ano. Reajusta novos contratos, obras e premiações futuras sem afetar contratos vigentes ou saldos passados.

---

## DD-021: Política de Transferências da CPU

- **Status**: `[IMPLEMENTADO]`
- **Regras**: Perfis estratégicos em `garfoot/domain/cpu_transfer_policy.py`. Avaliação de carências, ofertas e preços pedidos determinísticos via `seed`, mantendo o time do humano 100% protegido.

---

## DD-022: Patrocínios e Receitas Comerciais

- **Status**: `[IMPLEMENTADO]`
- **Regras**: Contratos `MASTER`, `KIT_SUPPLIER`, `STADIUM_PARTNER` e `PERFORMANCE_BONUS` em `garfoot/domain/sponsorship.py`. Receita creditada por rodada e bônus por vitória.

---

## DD-023: Despesas Operacionais do Clube

- **Status**: `[IMPLEMENTADO]`
- **Regras**: Custos de manutenção de estádio, logística, comissão e base por rodada em `garfoot/domain/operating_expenses.py`.

---

## DD-024: Saúde Financeira, Crise e Fair Play Financeiro

- **Status**: `[IMPLEMENTADO]`
- **Regras**: Score de saúde (0-100), crise e penalidades graduais em `garfoot/domain/financial_health.py`. Travamento de mercado/expansão e perda de pontos em insolvência prolongada. Saldo devedor não interrompe a execução do jogo.

---

## DD-025: Centro de Notícias e Eventos da Temporada

- **Status**: `[IMPLEMENTADO]`
- **Regras**: `NewsCenter` em `garfoot/domain/news.py` com 11 categorias, prioridades, IDs determinísticos e pruning automático (máximo 300 notícias).

---

## Auditoria Pós-Bloco 20 — Achados e Correções Concluídas

- **Status**: `[IMPLEMENTADO]`

Os achados da auditoria pós-Bloco 20 foram integralmente sanados pelas frentes AUD-FIX:

1. **Documentação Saneada (AUD-FIX-01)**: Saneamento de contradições e atualização dos documentos `STATUS.md` e `DESIGN_DECISIONS.md`. `[CONCLUÍDO]`
2. **Seeds e Determinismo (AUD-FIX-02)**: Uso de `hash()` Python em simulação e seletores substituído por hash estável baseado em SHA-256 (`stable_random.py`). `[CONCLUÍDO]`
3. **Idempotência Financeira e Histórica via Ledger (AUD-FIX-03)**: Transações financeiras (patrocínios, despesas, premiações) e viradas contratuais encapsuladas com `IdempotencyLedger` para impedir cobrança ou crédito duplicado. `[CONCLUÍDO]`
4. **Validação Transacional de Transferências (AUD-FIX-04)**: Rotinas de compra/venda operam com pré-validação atômica (`validate_transfer_preconditions`), eliminando estados parciais e corrupções. `[CONCLUÍDO]`
5. **Simulação Econômica de Longo Prazo (AUD-FIX-05)**: Criado script de auditoria (`scripts/audit_simulate_seasons.py`) e suíte automatizada validando estabilidade em 5+ temporadas. `[CONCLUÍDO]`

---

## Liberação da Trava do Bloco 21

> [!NOTE]
> A trava formal do **Bloco 21 (Caixa de Entrada da Diretoria)** foi **LEVANTADA em 2026-07-29** após a conclusão e homologação com sucesso de todas as auditorias técnicas `AUD-FIX-01` a `AUD-FIX-05`. O projeto está totalmente liberado para a implementação da Caixa de Entrada da Diretoria e tomada de decisões.

---

## DD-026: Caixa de Entrada da Diretoria (Board Inbox) e Tomada de Decisão

- **Status**: `[IMPLEMENTADO]`
- **Regras Implementadas**:
  - **Módulo Dedicado**: Criado `garfoot/domain/board_inbox.py` para gestão de comunicados interativos com tomada de decisão. O `NewsCenter` permanece exclusivo para o feed unidirecional de notícias informativas.
  - **5 Categorias de Comunicados (`BoardMessageType`)**: `RESULTS_WARNING` (desempenho), `FINANCIAL_ALERT` (estresse de caixa), `INVESTMENT_RESPONSE` (respostas a estádio/obras), `SEASON_CONGRATULATIONS` (reconhecimento/prêmios) e `BOARD_ULTIMATUM` (ultimatos com prazo).
  - **Expirabilidade e Timeout Caso a Caso**: Comunicados urgentes contêm `expires_at_round`. Caso o gestor avance rodadas sem responder, a opção padrão (`default_option_id_on_timeout`) é aplicada automaticamente e o status transiciona para `EXPIRED`.
  - **Garantia de Idempotência**: Toda tomada de decisão aplica a marcação atômica via `IdempotencyLedger` em `GameState` com a chave `board-decision:{message_id}:{option_id}`. Re-execuções por causa de re-load de save não duplicam débitos, ajustes de capacidade ou variações de moral.
  - **Interface TUI Retrô**: Implementada a tela `BoardInboxScreen` em `garfoot/ui/screens/board_inbox.py` com lista de comunicados pendentes, painel de contexto do comunicado e seleção navegável de opções via teclado (`1/2` / `A/B` / `ENTER`). Atalho registrado no Hub da Temporada (`8 / I / F8`).
