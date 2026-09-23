# Plano de Desenvolvimento de Software
## Garfoot — Jogo de Gerenciamento de Futebol

### 1. Estratégia geral

Desenvolvimento incremental por sistema (não por MVP restrito, conforme decisão de escopo completo), mas com **ordem de implementação** que respeita dependências técnicas: primeiro o núcleo de domínio e simulação (testável sem UI), depois persistência, depois UI, depois sistemas periféricos (transferências, finanças, base, imprensa), depois licenciamento.

### 2. Fases

**Fase 0 — Setup (curta)**
- Estrutura do projeto (Maven, módulos).
- Configuração de banco local (PostgreSQL ou H2 embarcado para desenvolvimento).
- Pipeline básico de build/testes (JUnit).

**Fase 1 — Núcleo de domínio e simulação**
- Modelagem das entidades centrais (Time, Jogador, Partida).
- Motor de simulação de partida (sem UI — testado via JUnit).
- Motor de campeonato (geração de tabela, atualização de classificação).
- Escalação por formação, com titulares, reservas e validação de disponibilidade/posição.
- Simulação de temporada com seed reproduzível.

**Fase 2 — Persistência**
- Mapeamento JPA/Hibernate das entidades.
- Save/load funcional via linha de comando ou testes automatizados (antes da UI existir).

**Fase 3 — Interface JavaFX**
- Tela de clube, elenco, escalação, partida (resultado/narração), classificação.
- Ligação da UI ao núcleo já testado nas fases 1-2.

**Fase 4 — Sistemas de gestão**
- Mercado de transferências (negociação com IA).
- Finanças do clube.
- Categoria de base.
- Infraestrutura do clube.

**Fase 5 — Competições avançadas**
- Múltiplas divisões, acesso/rebaixamento.
- Copas mata-mata e continentais.
- Seleção nacional.

**Fase 6 — Imprensa e eventos narrativos**

**Fase 7 — Registro e licenciamento**
- API de licenciamento (NestJS/PostgreSQL).
- Integração do cliente Java com a API (cadastro, ativação, revalidação).
- Feature flags ligando funcionalidades premium (F4-F12 de `02-requisitos-do-produto.md`) ao status de licença.

**Fase 8 — Empacotamento e distribuição**
- Geração de instaladores nativos via `jpackage` (Windows/Linux/macOS).
- Testes de instalação limpa em cada plataforma-alvo.

**Fase 9 — Testes finais e polimento**
- Testes de ponta a ponta (criar conta → jogar temporada → salvar/carregar).
- Balanceamento do motor de simulação (ajuste fino de probabilidades).

### 3. Organização (equipe enxuta / solo)

Dado que o projeto parte de um desenvolvedor principal, o plano assume desenvolvimento solo com possibilidade de expansão futura da equipe. Papéis lógicos (podem ser acumulados pela mesma pessoa):

| Papel | Responsabilidade |
|---|---|
| Dev núcleo/domínio | Modelo de dados, motor de simulação, regras de negócio |
| Dev UI | Telas JavaFX, experiência de usuário |
| Dev backend licenciamento | API NestJS, autenticação, feature flags |
| QA/Testes | Testes unitários e de integração, balanceamento |

### 4. Marcos (milestones) sugeridos

1. **M1** — Motor de simulação produz resultado de partida via teste automatizado (sem UI).
2. **M2** — Campeonato completo simulável ponta a ponta via testes (temporada inteira, sem UI).
3. **M3** — Save/load funcional.
4. **M4** — Primeira versão jogável com UI (loop completo: escalar → simular → ver resultado → avançar rodada).
5. **M5** — Sistemas de gestão (transferências, finanças, base, infraestrutura) integrados à UI.
6. **M6** — Competições avançadas e imprensa integradas.
7. **M7** — Registro/licenciamento funcionando ponta a ponta com feature flags.
8. **M8** — Instaladores nativos gerados e testados nas 3 plataformas.

### 5. Gestão de risco (pontos de atenção técnica)

| Risco | Mitigação |
|---|---|
| Motor de simulação "sem graça" ou repetitivo | Prototipar e balancear isoladamente antes de acoplar à UI; testes de "sanidade" rodando centenas de partidas simuladas e observando distribuição de placares |
| Rating agregado esconder desequilíbrio por posição ou calendário | Executar auditoria com escalações e temporadas representativas antes de calibrar fórmulas; a validação atual só mede forças agregadas |
| Complexidade de domínio virar acoplamento excessivo | Manter núcleo de domínio isolado de JavaFX e de Hibernate (camadas separadas: domínio puro → persistência → UI) |
| Sistema de licenciamento vulnerável a bypass | Validação assinada (JWT ou similar), revalidação periódica, não confiar apenas em flag local não assinada |
| Escopo grande gerar perda de foco | Seguir a ordem de fases: núcleo antes de periféricos; cada fase só avança com a anterior testada |

### 6. Prazos

Não estimados neste documento — dependem de disponibilidade real de horas de desenvolvimento. Recomenda-se estimar esforço por fase (em pontos ou horas) após a Fase 0, quando a complexidade real do motor de simulação estiver mais clara.
