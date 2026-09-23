# Execução Local

## Requisitos

- JDK 21;
- Maven Wrapper incluído no repositório.

## Preparar e abrir a aplicação

Na raiz do repositório, compile e instale os módulos no repositório Maven local:

```bash
./mvnw -q -pl ui -am install
```

Depois inicie o JavaFX a partir do módulo `ui`:

```bash
cd ui
../mvnw org.openjfx:javafx-maven-plugin:0.0.8:run
```

Na primeira execução, o Garfoot cria uma temporada demonstrativa. O save local fica em `~/.garfoot/garfoot.mv.db` e é atualizado ao avançar uma rodada e ao fechar a janela.

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
