---
name: garfoot-javafx-screens
description: "Use when creating or modifying JavaFX screens, FXML files, controllers, CSS, navigation, or bindings between the UI and the Garfoot core."
argument-hint: "Descreva a tela, fluxo ou estado visual a implementar"
---

# Garfoot JavaFX Screens

## Fonte de verdade

Consulte [06-estrutura-do-projeto.md](../../../docs/06-estrutura-do-projeto.md) para módulos e pacotes. A UI usa JavaFX; o domínio continua independente de JavaFX.

## Estrutura padrão

Para cada tela, mantenha os artefatos separados:

- FXML em `ui/src/main/resources/fxml/`;
- Controller em `ui/src/main/java/.../controller/`;
- CSS em `ui/src/main/resources/css/`;
- testes de controller ou de apresentação no módulo `ui`, sem mover regras de negócio para a UI.

Use nomes como `ClubOverview.fxml`, `ClubOverviewController` e uma folha CSS com nome correspondente em `kebab-case`, conforme o padrão Java/CSS já adotado no projeto.

## Procedimento

1. Descreva o estado de entrada, as ações disponíveis e os estados de carregamento, erro e vazio.
2. Identifique um caso de uso ou serviço do core para cada ação. O Controller coordena eventos, estado de tela e navegação; não calcula finanças, escalações, transferências ou resultados.
3. Injete dependências no Controller ou em uma camada de apresentação. Evite instanciar serviços de domínio diretamente em handlers.
4. Mantenha bindings e `fx:id` explícitos e valide o carregamento do FXML.
5. Centralize estilos no CSS da tela ou em um tema compartilhado. Não espalhe estilos inline sem necessidade.
6. Trate atualização de tela, falhas e tarefas demoradas sem bloquear a thread do JavaFX.
7. Teste o Controller com dependências falsas e teste o caso de uso separadamente no `core`.

## Checklist

- [ ] FXML, Controller e CSS estão nos módulos e diretórios corretos.
- [ ] O Controller não contém regra de domínio.
- [ ] A tela trata carregando, sucesso, vazio e erro.
- [ ] Navegação e dependências são testáveis.
- [ ] O core não importa JavaFX.
- [ ] Textos e estilos seguem a convenção existente e ficam prontos para internacionalização.
