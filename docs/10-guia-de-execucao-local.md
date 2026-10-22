# Execução Local

## Requisitos

- JDK 21;
- Maven Wrapper incluído no repositório.

## Preparar e abrir a aplicação

Na raiz do repositório, compile e instale os módulos no repositório Maven local:

```bash
./mvnw -q clean install
```

Depois inicie o JavaFX a partir do módulo `ui`:

```bash
./mvnw -pl ui javafx:run
```

No menu principal, use **Novo Jogo** para iniciar no Brasileirão Série B 2026. Escolha o clube, informe o nome do técnico e confirme a criação do save para abrir o hub do clube. O save local fica em `~/.garfoot/garfoot.mv.db`.

O modo Free oferece Brasil nesta versão. Os vinte clubes de cada série estão catalogados; elencos correspondidos vêm do snapshot Transfermarkt de 2026-07-06, e os elencos sintéticos são identificados na escolha do clube. Veja [a investigação da pirâmide 2026](12-investigacao-piramide-2026.md) para cobertura e limitações dos dados.

## PostgreSQL

Para conectar a um PostgreSQL local ou remoto, configure as variáveis antes de iniciar:

```bash
export GARFOOT_DB_URL='jdbc:postgresql://localhost:5432/garfoot'
export GARFOOT_DB_USER='garfoot'
export GARFOOT_DB_PASSWORD='senha-do-usuario'
```

O driver PostgreSQL já está no módulo de persistência. Hibernate atualiza o schema ao iniciar. Não coloque a senha em arquivos versionados.

## Testes

```bash
./mvnw -q clean test
```

O teste de integração PostgreSQL é opt-in. Defina `GARFOOT_TEST_POSTGRES_URL`, `GARFOOT_TEST_POSTGRES_USER` e `GARFOOT_TEST_POSTGRES_PASSWORD` para executá-lo com `./mvnw -pl persistence -am -Dtest=PostgresPersistenceIntegrationTest -Dsurefire.failIfNoSpecifiedTests=false test`.
