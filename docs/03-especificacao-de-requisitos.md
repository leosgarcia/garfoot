# SRS — Software Requirements Specification
## Garfoot — Jogo de Gerenciamento de Futebol

### 1. Introdução

#### 1.1 Propósito
Especificar de forma precisa os requisitos funcionais e não funcionais do sistema, servindo de base para implementação e testes.

#### 1.2 Escopo
Aplicação desktop em Java (núcleo do jogo) + serviço web de licenciamento (Node/NestJS + PostgreSQL) consumido via HTTP.

#### 1.3 Definições
- **RF**: Requisito Funcional.
- **RNF**: Requisito Não Funcional.
- **Core**: motor de simulação e regras de domínio, independente de UI.

### 2. Requisitos Funcionais

#### RF-01 — Gestão de Elenco
- RF-01.1 O sistema deve armazenar jogadores com atributos: técnica, físico, mental, posição, idade, moral, condição física.
- RF-01.2 O sistema deve permitir escalar um time (formação tática + 11 titulares + reservas).
- RF-01.3 O sistema deve aplicar evolução/regressão de atributos por temporada, em função de idade e minutos jogados.
- RF-01.4 O sistema deve gerar lesões e suspensões que impeçam escalação temporária do jogador.

#### RF-02 — Motor de Simulação de Partidas
- RF-02.1 O sistema deve calcular o resultado de uma partida a partir da força ofensiva/defensiva de ambos os times, tática e fator aleatório ponderado.
- RF-02.2 O sistema deve gerar eventos de partida (gols, cartões, lesões, substituições) distribuídos ao longo de 90 minutos simulados.
- RF-02.3 O sistema deve produzir uma narração textual dos eventos principais da partida.
- RF-02.4 O sistema deve ser determinístico dado um seed fixo (para fins de teste/replay), e não determinístico em jogo normal.

#### RF-03 — Campeonatos
- RF-03.1 O sistema deve gerar automaticamente a tabela de jogos (rodadas) de uma liga de pontos corridos, turno e returno.
- RF-03.2 O sistema deve suportar competições em formato mata-mata (eliminatória simples ou ida-e-volta).
- RF-03.3 O sistema deve aplicar acesso/rebaixamento entre divisões ao fim da temporada (feature premium).
- RF-03.4 O sistema deve manter classificação atualizada (pontos, vitórias, saldo de gols, critérios de desempate).

Para RF-03.1, o gerador atual garante cada par de clubes uma vez por turno e inverte o mando no returno; com número ímpar de participantes, cada equipe folga em uma rodada. Para RF-03.4, a ordenação determinística inicial é pontos, saldo de gols, gols pró, vitórias, nome e ID do clube.

#### RF-04 — Transferências
- RF-04.1 O sistema deve permitir propor a compra de um jogador de outro clube, com valor e condições.
- RF-04.2 O sistema deve simular resposta da IA do clube vendedor (aceite, recusa, contraproposta) considerando valor de mercado e necessidade do clube.
- RF-04.3 O sistema deve suportar empréstimo de jogadores com prazo definido.
- RF-04.4 O sistema deve restringir negociações a janelas de transferência configuráveis.

#### RF-05 — Finanças
- RF-05.1 O sistema deve calcular receita de bilheteria por partida em função de público e preço de ingresso.
- RF-05.2 O sistema deve calcular folha salarial mensal com base nos contratos ativos.
- RF-05.3 O sistema deve gerar balanço financeiro por temporada (receitas - despesas).
- RF-05.4 O sistema deve impedir gastos que resultem em saldo negativo além de um limite configurável (risco de intervenção da diretoria).

#### RF-06 — Categoria de Base (premium)
- RF-06.1 O sistema deve gerar periodicamente novos jogadores jovens com atributos e potencial variáveis.
- RF-06.2 O sistema deve permitir promoção de jogador da base para o elenco principal.

#### RF-07 — Infraestrutura do Clube
- RF-07.1 O sistema deve permitir upgrade de capacidade do estádio, com custo e efeito em receita de bilheteria.
- RF-07.2 O sistema deve permitir contratação de comissão técnica (preparador físico, olheiro), com efeito em atributos/eventos do time.

#### RF-08 — Imprensa e Eventos Narrativos
- RF-08.1 O sistema deve gerar eventos narrativos periódicos (notícias, entrevistas, incidentes) com efeito leve sobre moral do elenco.

#### RF-09 — Persistência
- RF-09.1 O sistema deve salvar o estado completo do jogo (times, jogadores, calendário, finanças, histórico) em um arquivo/banco local.
- RF-09.2 O sistema deve permitir carregar um save existente e retomar o jogo no estado exato salvo.
- RF-09.3 Usuários free devem ser limitados a 1 save; usuários premium, a saves ilimitados (conforme PRD F9).

#### RF-10 — Registro e Licenciamento
- RF-10.1 O sistema deve permitir criar conta (e-mail + senha) via API de licenciamento.
- RF-10.2 O sistema deve autenticar o usuário e obter um token de licença assinado.
- RF-10.3 O sistema deve armazenar o token localmente de forma criptografada, permitindo uso offline.
- RF-10.4 O sistema deve revalidar a licença periodicamente quando houver conexão disponível.
- RF-10.5 O sistema deve bloquear/liberar funcionalidades (feature flags) conforme o status premium retornado pela API.

### 3. Requisitos Não Funcionais

- **RNF-01 (Plataforma)**: o núcleo Java deve rodar em Windows 10+, principais distribuições Linux e macOS recente, via JRE empacotada com `jpackage` (usuário final não instala JVM manualmente).
- **RNF-02 (Desempenho)**: a simulação de uma partida completa deve concluir em até 2 segundos em hardware de referência modesto (ex: 4 núcleos, 8GB RAM).
- **RNF-03 (Disponibilidade offline)**: o jogo deve ser 100% jogável offline após a ativação inicial da licença, exceto para checar/atualizar status premium.
- **RNF-04 (Persistência local)**: os dados de save devem sobreviver a fechamento inesperado do aplicativo (auto-save periódico).
- **RNF-05 (Segurança)**: o token de licença armazenado localmente deve ser criptografado; comunicação com a API de licenciamento deve usar HTTPS/TLS.
- **RNF-06 (Extensibilidade)**: o motor de simulação deve ser desacoplado da camada de UI (JavaFX), permitindo testes automatizados sem interface gráfica.
- **RNF-07 (Internacionalização)**: strings de UI centralizadas para permitir tradução futura (mínimo: pt-BR nativo, estrutura pronta para outros idiomas).
- **RNF-08 (Testabilidade)**: regras de domínio (simulação, finanças, transferências) devem ter cobertura de testes unitários (JUnit) desde o início, dado o volume de regras de negócio.

### 4. Restrições

- Linguagem: Java (núcleo do jogo).
- Serviço de licenciamento: stack web já utilizada (NestJS/PostgreSQL).
- Sem dependência de conexão constante à internet para jogar.

### 5. Modelo de dados
Ver `05-modelo-de-dominio.md` para o detalhamento completo de entidades e relacionamentos.
