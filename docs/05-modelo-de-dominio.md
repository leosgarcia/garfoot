# Modelo de Domínio
## Garfoot — Jogo de Gerenciamento de Futebol

### 1. Visão geral das entidades

```
Usuario 1---1 Licenca
Clube 1---N Jogador
Clube 1---N Contrato
Jogador 1---N Contrato
Clube N---N Campeonato (via Inscricao)
Campeonato 1---N Rodada
Rodada 1---N Partida
Partida N---1 Clube (mandante)
Partida N---1 Clube (visitante)
Partida 1---N EventoPartida
Clube 1---1 Financas
Clube 1---1 Estadio
Clube 1---N Funcionario (comissao tecnica)
Clube 1---N JogadorBase (categoria de base)
Negociacao N---1 Jogador
Negociacao N---1 Clube (comprador)
Negociacao N---1 Clube (vendedor)
```

### 2. Entidades principais (classes Java — esqueleto)

#### 2.1 Jogador
```java
public class Jogador {
    private UUID id;
    private String nome;
    private LocalDate dataNascimento;
    private Posicao posicao; // enum: GOL, ZAG, LAT, VOL, MEI, ATA...
    private AtributosJogador atributos;
    private int moral; // 0-100
    private int condicaoFisica; // 0-100
    private StatusJogador status; // DISPONIVEL, LESIONADO, SUSPENSO
    private Clube clube; // null se sem clube
    private Contrato contratoAtivo;
}

public class AtributosJogador {
    private int tecnica;
    private int fisico;
    private int mental;
    private int velocidade;
    private int finalizacao;
    private int passe;
    private int marcacao;
    private int potencial; // teto de evolução (relevante p/ base)
}
```

#### 2.2 Clube
```java
public class Clube {
    private UUID id;
    private String nome;
    private String sigla;
    private List<Jogador> elenco;
    private List<JogadorBase> categoriaBase;
    private Financas financas;
    private Estadio estadio;
    private List<Funcionario> comissaoTecnica;
    private Tatica taticaAtual;
    private boolean controladoPeloUsuario;
}

public class Tatica {
    private Formacao formacao; // enum: 4-4-2, 4-3-3, 3-5-2...
    private Map<Posicao, Jogador> escalacao;
    private EstiloJogo estilo; // enum: OFENSIVO, EQUILIBRADO, DEFENSIVO
}
```

#### 2.3 Partida e simulação
```java
public class Partida {
    private UUID id;
    private Clube mandante;
    private Clube visitante;
    private LocalDateTime dataHora;
    private int golsMandante;
    private int golsVisitante;
    private List<EventoPartida> eventos;
    private StatusPartida status; // AGENDADA, EM_ANDAMENTO, ENCERRADA
}

public class EventoPartida {
    private int minuto;
    private TipoEvento tipo; // GOL, CARTAO_AMARELO, CARTAO_VERMELHO, LESAO, SUBSTITUICAO
    private Jogador jogadorEnvolvido;
    private String descricaoNarrativa;
}
```

No contrato Java, `EventoPartida` também registra explicitamente `jogadorQueSai` e
`jogadorQueEntra` em substituições. Para compatibilidade, `jogadorEnvolvido` identifica
quem sai, e o construtor anterior de quatro argumentos continua disponível. O resultado
de `MotorSimulacaoPartida` é aplicado à entidade por `ResultadoSimulacao.aplicarA(partida)`;
essa operação transiciona a partida agendada por `EM_ANDAMENTO` até `ENCERRADA` e copia
placar e eventos como um único efeito de domínio.

#### 2.4 Campeonato
```java
public class Campeonato {
    private UUID id;
    private String nome;
    private TipoCompeticao tipo; // LIGA, MATA_MATA, MISTO
    private List<Clube> participantes;
    private List<Rodada> rodadas;
    private List<ClassificacaoItem> classificacao; // apenas p/ formato liga
}

public class Rodada {
    private int numero;
    private List<Partida> partidas;
}

public class ClassificacaoItem {
    private Clube clube;
    private int pontos;
    private int vitorias, empates, derrotas;
    private int golsPro, golsContra;
}
```

#### 2.5 Transferências
```java
public class Negociacao {
    private UUID id;
    private Jogador jogadorAlvo;
    private Clube clubeComprador;
    private Clube clubeVendedor;
    private BigDecimal valorProposto;
    private TipoNegociacao tipo; // COMPRA, EMPRESTIMO
    private StatusNegociacao status; // PROPOSTA, CONTRAPROPOSTA, ACEITA, RECUSADA
}
```

#### 2.6 Finanças
```java
public class Financas {
    private Clube clube;
    private BigDecimal saldoCaixa;
    private BigDecimal receitaBilheteriaTemporada;
    private BigDecimal receitaPatrocinio;
    private BigDecimal folhaSalarialMensal;
    private List<LancamentoFinanceiro> historico;
}
```

#### 2.7 Registro/Licenciamento (integração com API externa)
```java
public class Usuario {
    private UUID id;
    private String email;
    private String senhaHash; // apenas se autenticação local; normalmente delegada à API
}

public class Licenca {
    private UUID usuarioId;
    private StatusLicenca status; // FREE, PREMIUM
    private LocalDateTime validaAte;
    private String tokenAssinado; // JWT ou similar, cacheado localmente
}
```

### 3. Camadas do domínio (organização lógica)

- **domain** — classes acima, sem dependência de framework (Java puro). Onde vive a regra de negócio testável isoladamente.
- **domain.service** — serviços de domínio: `MotorSimulacaoPartida`, `MotorCampeonato`, `ServicoTransferencia`, `ServicoFinancas`.
- **engine** — simulação pura da partida: `ForcaEquipe`, `MotorSimulacaoPartida` e `ResultadoSimulacao`.
- **persistence** — entidades JPA (podem espelhar as classes de domínio ou ser mapeadas separadamente, conforme preferência por DDD estrito vs. pragmático).
- **licensing** — cliente HTTP para a API de licenciamento e cache local do token.

### 4. Observação de design

Vale manter as classes de `domain` livres de anotações JPA/Hibernate diretamente, usando um mapeamento separado (ou MapStruct) se o projeto crescer — isso facilita testar o motor de simulação com JUnit puro, sem precisar subir banco de dados, conforme RNF-06 e RNF-08 de `03-especificacao-de-requisitos.md`.

### 5. Primeiro contrato implementado

O scaffold inicial implementa em `core/src/main/java/br/com/garfoot/core/model/`:

- `jogador`: `Jogador`, `AtributosJogador`, `Posicao` e `StatusJogador`;
- `clube`: `Clube` e `Tecnico`;
- `partida`: `Partida`, `EventoPartida`, `TipoEvento` e `StatusPartida`;
- `campeonato`: `Campeonato`, `Rodada` e `TipoCompeticao`.

Essas classes cobrem o contrato mínimo de identidade, elenco, técnico, partida, eventos e competição. Elas validam texto obrigatório, faixas de atributos, clubes distintos em uma partida, participantes únicos e transições básicas de partida. O modelo ainda não implementa tática, classificação, contratos, finanças ou o motor de simulação.

O motor possui uma sobrecarga de simulação que recebe as listas de jogadores de cada lado. Nessa forma, gols, cartões, lesões e substituições podem referenciar um `Jogador`; sem escalações, os eventos permanecem genéricos para compatibilidade. `ResultadoSimulacao.narracao()` transforma os eventos ordenados em texto linha a linha.

O subdomínio `tatica` contém `Formacao`, `Escalacao`, `Tatica` e `EstiloJogo`. A formação define os onze slots por posição e a escalação recebe os titulares nessa ordem, além de reservas. Titulares e reservas não podem repetir IDs, e todos devem estar disponíveis; a posição de cada titular deve corresponder ao slot.

`MotorCampeonato` gera turno e returno para liga de pontos corridos, invertendo o mando no returno. A temporada aplica cada `ResultadoSimulacao` à `Partida` e atualiza `ClassificacaoItem` com pontos, vitórias, empates, derrotas, gols pró/contra e saldo. Os desempates são pontos, saldo, gols pró, vitórias, nome e ID do clube, nessa ordem. Clubes sem elenco usam força neutra 50/50 até que exista escalação como entrada obrigatória do motor.

Para atribuir o autor do gol, o motor pondera finalização (80%) e técnica (20%) por prioridade posicional (`GOL` 0,10; `ZAG` 0,65; `LAT` 0,85; `VOL` 0,90; `MEI` 1,15; `ATA` 1,35). São priors iniciais ajustáveis; não alteram a expectativa de gols do confronto.

O script `scripts/import_transfermarkt_data.py` normaliza o snapshot externo para JSON em `data/processed/transfermarkt/`. Essa camada de importação mantém `source_id` e não é dependência do core.
