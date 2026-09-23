---
name: garfoot-domain-model
description: "Use when creating or modifying Java domain classes, entities, value objects, enums, or domain services in Garfoot. Enforces subdomain packages, framework-free core, naming conventions, and alignment with the Modelo de Domínio."
argument-hint: "Descreva a classe ou regra de domínio a criar ou alterar"
---

# Garfoot Domain Model

## Fonte de verdade

Antes de editar, consulte [05-modelo-de-dominio.md](../../../docs/05-modelo-de-dominio.md) e [03-especificacao-de-requisitos.md](../../../docs/03-especificacao-de-requisitos.md). Se a implementação e a documentação divergirem, trate a divergência como uma decisão explícita a resolver, não como licença para inventar um terceiro padrão.

## Procedimento

1. Identifique o subdomínio da mudança: `jogador`, `clube`, `partida`, `campeonato`, `transferencia`, `financas`, `base`, `infraestrutura` ou `usuario`.
2. Coloque a classe no pacote correspondente dentro do módulo `core`, seguindo o pacote raiz definido no documento de estrutura do projeto.
3. Use nomes de classes em `PascalCase`, métodos e atributos em `camelCase`, constantes em `UPPER_SNAKE_CASE` e enums com nomes de domínio claros.
4. Mantenha o core em Java puro. Não adicione anotações JPA, Hibernate, Spring, JavaFX ou qualquer outra anotação de framework às classes de domínio.
5. Prefira invariantes no próprio agregado ou value object, tipos explícitos e coleções protegidas contra mutação externa.
6. Separe persistência, transporte HTTP e apresentação em seus respectivos módulos. Use mapeadores quando a representação externa diferir do domínio.
7. Adicione ou atualize testes de unidade para invariantes e regras introduzidas.
8. Atualize o Modelo de Domínio quando uma entidade, relacionamento ou camada for alterado por decisão de escopo.

## Checklist

- [ ] O pacote representa o subdomínio correto.
- [ ] A classe não depende de framework no `core`.
- [ ] Os nomes seguem as convenções Java e o vocabulário dos documentos.
- [ ] Invariantes inválidas não podem ser criadas silenciosamente.
- [ ] A regra possui teste de domínio independente de banco e UI.
- [ ] A documentação foi sincronizada quando o modelo mudou.
