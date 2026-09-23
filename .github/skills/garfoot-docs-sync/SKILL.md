---
name: garfoot-docs-sync
description: "Use when a Garfoot scope, architecture, language, platform, requirement, domain entity, module, or release decision changes. Keeps PRD, SRS, Modelo de Domínio, and development plan synchronized with implementation."
argument-hint: "Descreva a decisão ou mudança de escopo a documentar"
---

# Garfoot Documentation Sync

## Quando acionar

Acione esta skill sempre que uma decisão alterar escopo, linguagem, arquitetura, módulo, requisito, entidade, fluxo premium, plataforma ou fase de entrega. Código e documentação devem evoluir na mesma mudança.

## Procedimento

1. Registre a decisão concreta e identifique quais documentos são afetados.
2. Atualize a visão ou o PRD quando o objetivo, público, feature, limite free/premium ou fora de escopo mudar.
3. Atualize o SRS quando requisitos funcionais, não funcionais, restrições, segurança, desempenho ou contratos mudarem.
4. Atualize o Modelo de Domínio quando entidades, atributos, relacionamentos, pacotes ou camadas mudarem.
5. Atualize o Plano de Desenvolvimento quando a ordem de fases, marcos, riscos, stack ou estratégia de entrega mudar.
6. Atualize a Estrutura do Projeto quando módulos, diretórios, pacotes ou dependências mudarem.
7. Procure referências antigas com `rg` e substitua nomes, links e termos obsoletos.
8. Evite reescrever decisões não relacionadas. Se houver conflito entre documentos, resolva a decisão e deixe uma única formulação vigente.
9. Revise a documentação junto com o teste ou validação da mudança técnica.

## Mapa de documentos

- `01-visao-do-produto.md`: visão, objetivos e escopo macro.
- `02-requisitos-do-produto.md`: funcionalidades e prioridades de produto.
- `03-especificacao-de-requisitos.md`: RF, RNF e restrições verificáveis.
- `04-plano-de-desenvolvimento.md`: fases, marcos e riscos.
- `05-modelo-de-dominio.md`: entidades, relacionamentos e camadas.
- `06-estrutura-do-projeto.md`: módulos, pacotes e dependências.

## Checklist

- [ ] A decisão está refletida em todos os documentos relevantes.
- [ ] PRD, SRS e modelo de domínio não se contradizem.
- [ ] Referências cruzadas apontam para nomes atuais.
- [ ] Código, testes e documentação usam o mesmo vocabulário.
- [ ] Nenhuma mudança não relacionada foi incluída.
