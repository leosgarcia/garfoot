# Decisões Técnicas Iniciais

## Status

Aceita em 2026-09-23 para iniciar o desenvolvimento do Garfoot.

## Java

O projeto usa **Java 21 LTS**. Essa versão está instalada no ambiente de desenvolvimento e oferece estabilidade de longo prazo para o core, JavaFX, persistência e empacotamento com `jpackage`.

O pacote raiz oficial é `br.com.garfoot`.

## Build

O projeto usa **Maven multi-módulo** com Maven 3.9.x. O repositório inclui `mvnw` para que o build não dependa de Maven instalado globalmente.

Módulos iniciais:

- `core`: domínio e regras de negócio, sem framework;
- `persistence`: mapeamento e acesso a dados;
- `licensing-client`: cliente da API de licenciamento;
- `ui`: JavaFX e recursos de apresentação.

## Persistência

- **H2** será usado em testes e como banco local embarcado padrão (`~/.garfoot/garfoot.mv.db`).
- **PostgreSQL** é o alvo para persistência compatível com produção e evolução do projeto.
- O core não conhece JPA, Hibernate, H2 ou PostgreSQL.
- O módulo `persistence` é responsável por mapeamento, repositórios e configuração de banco.
- `FabricaPersistencia` usa H2 local por padrão; `GARFOOT_DB_URL`, `GARFOOT_DB_USER` e `GARFOOT_DB_PASSWORD` permitem configurar PostgreSQL sem credenciais no código.
- A primeira implementação persiste um snapshot JSON versão 1 de temporada por entidade JPA, mantendo o agregado e suas regras sem anotações. Jackson é usado exclusivamente no módulo `persistence`; a evolução para tabelas normalizadas não altera o core.

## Interface

A UI usa **JavaFX 21**. FXML, controllers e CSS ficam no módulo `ui`. Controllers coordenam casos de uso e navegação, mas não carregam regras de domínio.

## Testes

- JUnit 5 para regras e comportamento;
- Mockito 5 para portas e colaboradores externos;
- testes do core independentes de UI, banco e rede;
- seeds, relógio e dependências variáveis devem ser injetáveis quando afetarem resultados.

## Licenciamento

O cliente usa `java.net.http.HttpClient` inicialmente, mantendo HTTP e token fora do core. A integração deve seguir RF-10 e RNF-05 do SRS: HTTPS/TLS, validação de token, feature flags derivadas do estado validado e modo offline sem concessão implícita de premium.

## Consequências

- O ambiente precisa de JDK 21 ou compatível.
- A primeira compilação baixa dependências Maven e JavaFX.
- A persistência pode começar com testes H2 sem exigir PostgreSQL local.
- O snapshot por temporada facilita gravação atômica; mudanças de formato precisarão de versão e migração antes da distribuição de saves de usuários.
- Mudanças de versão de Java, JavaFX, banco ou build devem atualizar este documento e a Estrutura do Projeto.
