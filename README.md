# ⚽ Garfoot

**Garfoot** é um jogo de gerenciamento de futebol retrô desenvolvido em Python, inspirado nos clássicos dos anos 90 (estilo *Elifoot II*). O projeto combina nostalgia visual em modo texto (TUI) com um motor de simulação estatístico moderno, determinístico e extremamente detalhado.

---

## 🌟 Principais Funcionalidades

- **🖥️ Interface Retrô Terminal & GUI**:
  - Interface Terminal completa via [Textual](https://github.com/Textualize/textual) com suporte a atalhos rápidos (`F1`-`F7`), navegação por teclado e visual estilo MS-DOS.
  - Tela de abertura (Splash Screen) com arte ASCII, boot em cascata e efeitos clássicos.
  - Camada de interface gráfica moderna em desenvolvimento com **PySide6**.

- **⚽ Motor de Simulação Determinístico**:
  - Simulação minuto a minuto com eventos imutáveis (gols, cartões, lesões e substituições).
  - Cálculo de chance de gol baseado no alinhamento de formações, posições e atributos dos atletas.
  - Sementes de aleatoriedade determinísticas (SHA-256) garantindo reprodutibilidade sem dependência de `hash()` do sistema.

- **🏆 Ligas & Competições**:
  - Sistema de 4 divisões nacionais (Séries A, B, C e D) com promoção e rebaixamento.
  - **Copa do Brasil** com fase preliminar mata-mata e premiações por fase.
  - Supercopa ("Super Campeão").
  - Dataset completo com 80 clubes reais do futebol brasileiro.

- **💰 Economia & Gestão Financeira Avançada**:
  - Gerenciamento de bilheteria e apelo de público por partida (rivalidade, importância do jogo).
  - Folha salarial, despesas operacionais recorrentes e manutenção de estádio.
  - Patrocínio master e secundários com bônus por vitórias e metas.
  - Fair Play Financeiro, pontuação de saúde financeira e riscos de punição gradual em caso de crise.
  - Ampliação e melhorias no estádio do clube.

- **📜 Mercado de Transferências & Elenco**:
  - Mercado completo com compras diretas, propostas e rescisão via cláusula contratual.
  - Política determinística da CPU para movimentação de atletas no mercado com proteção ao jogador humano.
  - Mercado de agentes livres ao fim da temporada.
  - Gestão de elenco (18 a 30 atletas), categorias de base com promoção de jovens e aposentadoria por idade.

- **👔 Comissão Técnica & Imprensa**:
  - Demissão e contratação de treinadores com efeito de "chicotada psicológica" (*Coach Bounce Effect*).
  - Pressão da diretoria baseada em expectativas e resultados.
  - Centro de notícias dinâmico e estatísticas da temporada (artilharia, assistências, rankings).

---

## 🚀 Como Executar o Projeto

### Requisitos Prévios
- **Python 3.11** ou superior
- Gerenciador de pacotes `pip` ou `uv`

### 1. Clonar o repositório
```bash
git clone https://github.com/leosgarcia/garfoot.git
cd garfoot
```

### 2. Criar e ativar o ambiente virtual
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou no Windows: .venv\Scripts\activate
```

### 3. Instalar as dependências
```bash
pip install -e .
```

### 4. Iniciar o Jogo (Modo TUI / Terminal)
```bash
python -m garfoot.ui.app
```

---

## 🧪 Testes e Validação

O projeto possui uma suíte extensa de testes automatizados com `pytest` cobrindo determinismo, motor de jogo, regras de negócio e persistência de save.

Para executar os testes:
```bash
pytest
```

Para rodar os scripts de simulação longa/auditoria econômica (simula 5+ temporadas sem UI):
```bash
python scripts/audit_simulate_seasons.py
```

---

## 📁 Estrutura do Repositório

- `garfoot/domain/`: Regras puras de negócio, economia, ligas, contratos, finanças e atletas.
- `garfoot/engine/`: Motor de simulação de partidas, eventos, probabilidade e narração.
- `garfoot/persistence/`: Sistema de saves atômicos (`SaveManager`, `GameState`).
- `garfoot/ui/`: Interface TUI completa utilizando a biblioteca `textual`.
- `garfoot/ui_qt/`: Interface gráfica paralela usando `PySide6`.
- `data/`: Datasets de clubes e dados iniciais.
- `tests/`: Suíte de testes automatizados com `pytest`.

---

## 📄 Licença

Este projeto é desenvolvido para fins de estudos e entretenimento. Todos os direitos reservados.  
Autoria: **Leonardo Garcia**
