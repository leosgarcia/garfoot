---
name: garfoot-licensing-integration
description: "Use when implementing the NestJS licensing API integration, license tokens, premium feature flags, authentication, revalidation, offline mode, or RF-10/RNF-05 behavior in Garfoot."
argument-hint: "Descreva o fluxo de licença ou feature flag a implementar"
---

# Garfoot Licensing Integration

## Fonte de verdade

Consulte RF-10 e RNF-05 em [03-especificacao-de-requisitos.md](../../../docs/03-especificacao-de-requisitos.md), além da seção de licenciamento em [05-modelo-de-dominio.md](../../../docs/05-modelo-de-dominio.md). O cliente Java não deve espalhar detalhes HTTP ou JWT pelo domínio e pela UI.

## Procedimento

1. Defina o contrato da API: endpoint, método, payload, resposta, códigos de erro, expiração e versão.
2. Mantenha o cliente HTTP e DTOs no módulo `licensing-client`; converta a resposta para um modelo de licença usado pelo restante da aplicação.
3. Valide assinatura, emissor, audiência, expiração e demais claims obrigatórias do token antes de aceitar premium. Nunca confie apenas em uma flag local.
4. Armazene o token localmente de forma protegida e evite registrar token, senha ou dados sensíveis em logs, exceções e telemetria.
5. Modele explicitamente `FREE`, `PREMIUM`, expirado, inválido e indisponível. Feature flags devem ser derivadas do estado validado da licença.
6. Em modo offline, permita somente capacidades previstas no contrato e aplique a política de expiração/revalidação definida. Não transforme falha de rede em premium implícito.
7. Use timeouts, tratamento de erro e reintento limitado. A UI deve receber um resultado de estado, não uma exceção HTTP crua.
8. Teste sucesso, token inválido, expirado, resposta malformada, API indisponível e funcionamento offline.

## Checklist de segurança

- [ ] Toda comunicação usa HTTPS/TLS.
- [ ] Token e credenciais não aparecem em logs.
- [ ] Assinatura e claims são validadas localmente conforme contrato.
- [ ] Falha de rede não concede acesso premium.
- [ ] Feature flags não são decididas pela UI.
- [ ] O domínio permanece independente de HTTP e framework web.
