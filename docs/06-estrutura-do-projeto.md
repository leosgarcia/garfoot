# Estrutura do Projeto
## Garfoot — Jogo de Gerenciamento de Futebol

### 1. Organização geral (multi-módulo Maven)

Separar em módulos permite testar o núcleo de domínio sem depender de UI, e reaproveitar o `core` em outra UI no futuro se necessário.

```
garfoot/
├── pom.xml                        (parent POM, gerencia versões e módulos)
│
├── core/                          (módulo: domínio + regras de negócio, Java puro)
│   ├── pom.xml
│   └── src/
│       ├── main/java/br/com/garfoot/core/
│       │   ├── model/             (Jogador, Clube, Partida, Campeonato...)
│       │   ├── model/tatica/      (Formacao, Escalacao, Tatica, EstiloJogo)
│       │   ├── application/       (casos de uso e portas externas)
│       │   ├── engine/            (MotorSimulacaoPartida, MotorCampeonato...)
│       │   └── util/
│       └── test/java/br/com/garfoot/core/
│           └── service/           (testes JUnit do motor de simulação, etc.)
│
├── persistence/                   (módulo: JPA/Hibernate + PostgreSQL)
│   ├── pom.xml
│   └── src/main/java/br/com/garfoot/persistence/
│       ├── entity/                (entidades JPA)
│       ├── repository/            (DAOs/repositories)
│       └── mapper/                (domain <-> snapshot de storage)
│
├── licensing-client/               (módulo: cliente HTTP da API de licenciamento)
│   ├── pom.xml
│   └── src/main/java/br/com/garfoot/licensing/
│       ├── LicensingClient.java
│       ├── TokenCache.java
│       └── dto/
│
├── ui/                             (módulo: JavaFX)
│   ├── pom.xml
│   └── src/main/
│       ├── java/br/com/garfoot/ui/
│       │   ├── MainApp.java
│       │   ├── controller/        (um controller por tela)
│       └── resources/
│           ├── fxml/               (telas JavaFX)
│           └── css/
│
└── docs/                           (documentação numerada conforme `00-convencoes-de-nomenclatura.md`)
```

Scripts de dados ficam em `scripts/`. O importador `import_transfermarkt_data.py` lê `data/external/transfermarkt/raw/` e gera artefatos normalizados ignorados pelo Git em `data/processed/transfermarkt/`.

### 2. Módulo `core` — pacotes internos sugeridos

```
core/
└── model/
    ├── jogador/        Jogador, AtributosJogador, Posicao
    ├── clube/          Clube, Tecnico
    ├── tatica/         Formacao, Escalacao, Tatica, EstiloJogo
    ├── partida/        Partida, EventoPartida, TipoEvento, StatusPartida
    ├── campeonato/     Campeonato, Rodada, ClassificacaoItem, TipoCompeticao
    ├── transferencia/  Negociacao, StatusNegociacao, TipoNegociacao
    ├── financas/       Financas, LancamentoFinanceiro
    ├── base/           JogadorBase
    ├── infraestrutura/ Estadio, Funcionario
    └── usuario/        Usuario, Licenca, StatusLicenca
```

### 3. Backend de licenciamento (serviço separado, fora deste repositório Java)

```
licensing-api/                     (NestJS, repositório/projeto separado)
├── src/
│   ├── auth/           (cadastro, login, JWT)
│   ├── license/        (geração/validação de licença, status premium)
│   └── users/
├── prisma/
│   └── schema.prisma
└── ...
```

### 4. Dependências principais por módulo

- **core**: Java puro (nenhuma dependência externa obrigatória, exceto JUnit em `test`). Opcionalmente Lombok para reduzir boilerplate.
- **persistence**: Hibernate/JPA, H2 local/testes e driver PostgreSQL configurável.
- **licensing-client**: `java.net.http.HttpClient` (nativo, sem dependência extra) ou um client HTTP leve; biblioteca JWT para validar assinatura do token localmente.
- **ui**: JavaFX (controls, fxml), CSS para estilização.

Versões e decisões aprovadas para o primeiro scaffold estão registradas em `08-decisoes-tecnicas-iniciais.md`.

O primeiro adapter de persistência armazena uma temporada como snapshot JSON em uma entidade JPA isolada. H2 valida save/load e é o banco local padrão; PostgreSQL foi validado por integração no ambiente local. Jackson converte o snapshot somente no módulo `persistence`.

### 5. Convenções sugeridas

- Pacote raiz oficial: `br.com.garfoot`.
- Build: Maven multi-módulo (`mvn -pl core,persistence,licensing-client,ui -am install`).
- Testes: JUnit 5 + Mockito para o `core`, isolando o motor de simulação de qualquer I/O.
- Empacotamento final: `jpackage` a partir do módulo `ui` (empacota o app + dependências + JVM em instalador nativo).
