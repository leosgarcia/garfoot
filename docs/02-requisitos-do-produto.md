# PRD — Product Requirements Document
## Garfoot — Jogo de Gerenciamento de Futebol

### 1. Visão geral do produto

Jogo desktop de gerenciamento de futebol em Java (JavaFX), com sistema de registro que libera funções premium. Referência de gênero: Elifoot. Ver `01-visao-do-produto.md` para contexto de negócio.

### 2. Público-alvo e personas

**Persona 1 — "Nostálgico"**: 30-45 anos, jogou Elifoot/similares na infância/adolescência, busca resgatar a experiência com qualidade de vida atual (save em nuvem opcional, UI mais limpa).

**Persona 2 — "Gestor competitivo"**: gosta de otimizar números, planilhas mentais de escalação, quer profundidade em finanças/transferências/tática.

**Persona 3 — "Casual"**: quer partidas rápidas, campeonato simples, sem se aprofundar em todos os sistemas — deve conseguir jogar bem só com as funções free/essenciais.

### 3. Funcionalidades (Features) — Free vs Premium

| # | Funcionalidade | Free | Premium |
|---|---|---|---|
| F1 | Criar/gerenciar 1 time | ✅ | ✅ |
| F2 | Simular partidas (motor completo) | ✅ | ✅ |
| F3 | 1 campeonato (liga nacional única) | ✅ | ✅ |
| F4 | Múltiplas divisões com acesso/rebaixamento | ❌ | ✅ |
| F5 | Copas mata-mata e copas continentais | ❌ | ✅ |
| F6 | Seleção nacional | ❌ | ✅ |
| F7 | Mercado de transferências completo (negociação avançada, empréstimos) | Limitado (só compra simples) | ✅ Completo |
| F8 | Categoria de base / escolinha | ❌ | ✅ |
| F9 | Múltiplos saves simultâneos | 1 save | Ilimitado |
| F10 | Infraestrutura do clube (estádio, CT) | Visualização apenas | Gestão completa |
| F11 | Imprensa/eventos narrativos avançados | Eventos básicos | Eventos completos |
| F12 | Estatísticas históricas/recordes de longo prazo | ❌ | ✅ |

### 4. Fluxos principais de usuário (user flows)

**4.1 Primeiro acesso**
1. Usuário instala o jogo → abre pela primeira vez.
2. Tela de boas-vindas oferece: "Jogar sem cadastro (free)" ou "Registrar-se".
3. Se registrar: formulário (e-mail/senha) → chamada à API de licenciamento → token salvo localmente.
4. Segue para criação de save (escolher/criar time).

**4.2 Ciclo de jogo (loop principal)**
1. Tela de clube (visão geral: elenco, finanças, próximos jogos).
2. Usuário ajusta escalação/tática.
3. Usuário avança para a próxima partida ou rodada.
4. Motor simula → resultado exibido (narração + placar + estatísticas).
5. Classificação e calendário atualizados.
6. Eventos aleatórios (imprensa, lesões, propostas de transferência) podem interromper o loop pedindo decisão do usuário.
7. Repete até fim de temporada → tela de resumo de temporada → nova temporada.

**4.3 Upgrade para premium**
1. Usuário tenta acessar função bloqueada (ex: 2ª divisão).
2. Tela explica o que é premium, com botão "Ativar premium".
3. Fluxo de pagamento/ativação (fora do escopo técnico deste documento — ver `03-especificacao-de-requisitos.md` para requisito de integração).
4. API valida e libera feature flags no app.

### 5. Requisitos funcionais por sistema (resumo — detalhamento técnico em `03-especificacao-de-requisitos.md`)

- **Simulação de partida**: motor calcula eventos (gols, cartões, lesões) a partir de atributos dos jogadores, tática e fatores aleatórios; gera narração textual minuto a minuto.
- **Elenco**: CRUD de jogadores com atributos, evolução por idade/desempenho, lesões e suspensões.
- **Campeonatos**: geração de tabela (rodadas), motor de pontos corridos e mata-mata, acesso/rebaixamento.
- **Transferências**: proposta, contraproposta, aceite/recusa por IA, janelas de transferência.
- **Finanças**: receitas (bilheteria, patrocínio, TV), despesas (salários, manutenção), saldo por temporada.
- **Base**: geração periódica de novos jogadores jovens com potencial variável.
- **Infraestrutura**: upgrade de estádio/CT com efeito em receita/desempenho.
- **Imprensa**: geração de eventos narrativos com impacto leve em moral.
- **Persistência**: salvar/carregar estado completo do jogo (múltiplos saves conforme plano).
- **Registro/licenciamento**: cadastro, login, validação online/offline, feature flags.

### 6. Requisitos não funcionais (resumo — ver `03-especificacao-de-requisitos.md`)

- Rodar em Windows/Linux/macOS via JVM empacotada (jpackage).
- Simulação de uma partida deve levar no máximo poucos segundos em hardware modesto.
- Funcionar offline após ativação inicial (exceto ações que exigem sincronização, ex: upgrade premium).

### 7. Métricas de sucesso do produto

- Taxa de conclusão de pelo menos 1 temporada completa entre novos usuários.
- Taxa de conversão free → premium.
- Tempo médio de sessão.
- Taxa de erro/crash por sessão (estabilidade).

### 8. Fora de escopo (nesta versão)

Multiplayer, mobile, gráficos 3D de partida, integração com redes sociais.