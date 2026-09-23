---
name: garfoot-junit-domain-tests
description: "Use when writing or reviewing JUnit 5 tests for Garfoot core business rules, including simulation, finances, transfers, competitions, persistence boundaries, Mockito doubles, and coverage required by RNF-08."
argument-hint: "Descreva a regra de negócio e os cenários a testar"
---

# Garfoot JUnit Domain Tests

## Objetivo

Os testes do `core` devem validar comportamento de negócio sem JavaFX, banco, rede, relógio real ou aleatoriedade global. Consulte RNF-08 em [03-especificacao-de-requisitos.md](../../../docs/03-especificacao-de-requisitos.md).

## Procedimento

1. Escreva o cenário no formato Arrange, Act, Assert e dê ao teste um nome que descreva a regra observável.
2. Prefira objetos reais pequenos para entidades e value objects. Use Mockito apenas para dependências externas, portas, callbacks ou colaboradores cuja interação seja parte do contrato.
3. Injete seed, relógio, repositórios e políticas variáveis. Nunca dependa de `sleep`, ordem acidental de testes ou estado compartilhado.
4. Cubra caminho feliz, limites, entradas inválidas, transições de estado e idempotência quando aplicável.
5. Para probabilidades e simulação, teste propriedades estatísticas com uma amostra suficiente e tolerâncias explícitas. Use seeds reproduzíveis e não exija uma sequência específica de gols sem necessidade.
6. Verifique efeitos observáveis: saldo, classificação, contrato, eventos, estado da partida e chamadas relevantes às dependências.
7. Mantenha testes rápidos e isolados; testes de integração devem ficar identificados fora do conjunto unitário.

## Convenções

- JUnit 5 (`@Test`, `@ParameterizedTest`, `@Nested`, `@DisplayName` quando melhora a leitura).
- Mockito para mocks, stubs e verificações pontuais.
- Um comportamento principal por teste.
- Dados de teste nomeados e fábricas auxiliares pequenas, sem esconder a regra testada.
- Mensagens de asserção úteis quando o valor esperado não for óbvio.

## Checklist

- [ ] O teste pode rodar sem UI, banco ou rede.
- [ ] O teste é determinístico e independente.
- [ ] Casos de limite e falha estão cobertos.
- [ ] Mockito não substitui o objeto sob teste nem verifica detalhes irrelevantes.
- [ ] A asserção valida comportamento, não implementação privada.
- [ ] A suíte continua rápida e legível.
