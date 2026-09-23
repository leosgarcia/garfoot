---
name: garfoot-jpackage-release
description: "Use when preparing or troubleshooting native Garfoot installers with jpackage for Windows, Linux, or macOS from the ui module. Covers runtime images, packaging, validation, and platform constraints."
argument-hint: "Descreva a plataforma e o artefato de release a gerar"
---

# Garfoot jpackage Release

## Fonte de verdade

Consulte a Fase 8 em [04-plano-de-desenvolvimento.md](../../../docs/04-plano-de-desenvolvimento.md), além da estrutura do módulo `ui` em [06-estrutura-do-projeto.md](../../../docs/06-estrutura-do-projeto.md).

## Procedimento

1. Confirme a versão de Java, Maven e JavaFX suportadas pelo projeto e gere um build limpo do módulo `ui` e suas dependências.
2. Produza um artefato executável ou uma imagem de aplicação com classpath, módulos JavaFX, recursos FXML, CSS e ícones incluídos.
3. Monte o `jpackage` com nome, versão, identificador, classe principal, imagem de entrada, diretório de saída e tipo de instalador explícitos.
4. Gere o instalador no sistema operacional alvo. `jpackage` não cria um instalador Windows a partir do Linux nem um instalador macOS a partir de outro sistema sem uma cadeia de build apropriada.
5. Use opções específicas de plataforma somente quando disponíveis e documente requisitos de assinatura, certificados, ícones e formatos (`deb`/`rpm`, `msi`/`exe`, `pkg`/`dmg`).
6. Teste instalação limpa, inicialização, navegação de telas, carregamento de FXML/CSS, persistência local e desinstalação em cada plataforma alvo.
7. Verifique que a JVM empacotada inicia sem Java instalado pelo usuário e que o artefato não depende de caminhos absolutos da máquina de build.
8. Registre versão, commit, plataforma, comando efetivo e resultado dos testes no artefato ou relatório de release.

## Checklist por release

- [ ] Build limpo e testes aprovados.
- [ ] Dependências e recursos do `ui` estão no artefato.
- [ ] Versão do instalador é válida e reproduzível.
- [ ] O instalador foi gerado no sistema operacional correspondente.
- [ ] Instalação limpa e desinstalação foram verificadas.
- [ ] Aplicação inicia e carrega FXML/CSS sem erro.
- [ ] Licenciamento e modo offline seguem o contrato.
- [ ] Artefatos e comandos de cada plataforma foram registrados.
