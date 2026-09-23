# Convenções de Nomenclatura da Documentação

## Regra para arquivos

Os arquivos desta pasta devem seguir o formato:

```text
NN-nome-descritivo.md
```

Onde:

- `NN` é um número sequencial com dois dígitos;
- `nome-descritivo` usa letras minúsculas;
- palavras são separadas por hífens (`kebab-case`);
- nomes usam ASCII, sem acentos, espaços, pontos intermediários ou abreviações ambíguas;
- a extensão deve ser sempre `.md`.

## Organização

- `00` é reservado para convenções, índices e documentos de orientação;
- documentos de visão e requisitos vêm antes dos documentos de arquitetura e planejamento;
- novos documentos recebem o próximo número disponível;
- ao renomear um documento, referências internas devem ser atualizadas na mesma alteração.

## Nomes atuais

| Arquivo | Finalidade |
|---|---|
| `01-visao-do-produto.md` | Visão, objetivos e escopo do produto |
| `02-requisitos-do-produto.md` | Requisitos de produto e funcionalidades |
| `03-especificacao-de-requisitos.md` | Requisitos funcionais e não funcionais detalhados |
| `04-plano-de-desenvolvimento.md` | Fases, marcos e riscos de desenvolvimento |
| `05-modelo-de-dominio.md` | Entidades e camadas do domínio |
| `06-estrutura-do-projeto.md` | Organização técnica do projeto |
| `07-politica-de-fontes-e-assets.md` | Fontes, licenças, mídia e rastreabilidade de dados |
| `08-decisoes-tecnicas-iniciais.md` | Baseline de Java, Maven, persistência, UI e testes |
| `09-formulas-de-rating.md` | Fórmulas e calibração dos atributos de jogadores |
