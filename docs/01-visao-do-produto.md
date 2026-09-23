# Documento de Visão
## Garfoot — Jogo de Gerenciamento de Futebol

### 1. Propósito

Este documento descreve, em alto nível, o problema que o produto resolve, o público-alvo, o escopo geral e os objetivos de negócio. Serve como referência para alinhar todas as decisões técnicas e de produto tomadas ao longo do projeto.

### 2. Problema

Jogos de gerenciamento de futebol nacionais (como o Elifoot original) praticamente desapareceram do mercado. Os sucessores diretos internacionais (Football Manager e similares) são complexos, pagos por temporada, exigem hardware relativamente robusto e não têm identidade com o futebol brasileiro/regional. Existe uma lacuna para um jogo de gestão de futebol:

- Leve, 100% desktop, sem depender de conexão constante;
- Com identidade e progressão simples de entender (no espírito do Elifoot);
- Com um modelo de negócio sustentável via registro/premium, sem ser pago por assinatura obrigatória.

### 3. Visão do produto

Um jogo de gerenciamento de futebol para desktop (Windows/Linux/macOS), em Java, onde o jogador assume o comando de um clube e conduz sua trajetória através de temporadas — escalando time, negociando jogadores, administrando finanças, base e infraestrutura, disputando campeonatos regionais, nacionais, copas e seleção. O core de simulação de partidas é o coração do produto: precisa ser crível, variado e não repetitivo. Uma camada de registro libera funcionalidades premium para quem se cadastra, sustentando o desenvolvimento contínuo.

### 4. Público-alvo

- Jogadores nostálgicos de Elifoot/Winning Eleven-management dos anos 1990-2000;
- Fãs de jogos de gestão esportiva que buscam alternativa leve aos concorrentes internacionais pagos;
- Público brasileiro/lusófono, com interesse em competições e times nacionais/regionais.

### 5. Escopo geral (visão macro, não exaustivo — ver `02-requisitos-do-produto.md` e `03-especificacao-de-requisitos.md` para detalhe)

Incluso:
- Simulação de partidas (motor próprio);
- Gestão de elenco, escalação e tática;
- Campeonatos (liga, copa mata-mata, acesso/rebaixamento, copas continentais, seleção);
- Mercado de transferências com negociação;
- Finanças de clube;
- Categoria de base;
- Infraestrutura do clube (estádio, CT, comissão técnica);
- Imprensa e eventos narrativos aleatórios;
- Persistência de save/load de longo prazo (múltiplas temporadas);
- Sistema de registro de usuário com liberação de funções premium.

Fora do escopo inicial (não descartado para o futuro):
- Multiplayer online;
- Versão mobile;
- Gráficos 3D de partida (o jogo é orientado a texto/dados, como o Elifoot original).

### 6. Objetivos de negócio

1. Lançar uma versão jogável e estável cobrindo todos os sistemas descritos no escopo geral.
2. Estabelecer um modelo de registro gratuito + funções premium que gere receita recorrente ou pontual sem depender de assinatura obrigatória para jogar.
3. Construir uma base de jogadores fiel através de identidade nostálgica e qualidade da simulação.
4. Manter a arquitetura desacoplada o suficiente (núcleo do jogo em Java vs. serviço de licenciamento web) para permitir evolução futura (ex: expansão para multiplayer ou mobile) sem reescrever o core.

### 7. Stakeholders

| Papel | Responsabilidade |
|---|---|
| Product Owner / Idealizador | Define regras de negócio do jogo, prioriza funcionalidades |
| Desenvolvedor(es) | Implementação do núcleo Java, UI JavaFX, serviço de licenciamento |
| Jogadores/usuários finais | Público consumidor, fonte de feedback |

### 8. Critérios de sucesso da visão

- O motor de simulação produz resultados variados e plausíveis ao longo de múltiplas temporadas simuladas em teste.
- Um usuário consegue: criar conta → jogar uma temporada completa → salvar e carregar o jogo → sem erros críticos.
- O fluxo de registro/premium funciona ponta a ponta (cadastro, ativação, revalidação, bloqueio de features free).