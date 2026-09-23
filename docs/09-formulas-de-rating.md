# Fórmulas de Rating do Jogador

## Status

Protótipo experimental definido em 2026-09-23. As fórmulas ainda precisam de calibração de jogo e validação no motor de partidas.

## Fontes

A entrada canônica vem do snapshot `dcaribou/transfermarkt-datasets`, usando identidade, posição, data de nascimento, altura, valor de mercado, aparições, minutos, gols, assistências e internacionalizações.

A distribuição do [EAFC26 DataHub](https://github.com/ismailoksuz/EAFC26-DataHub) é usada somente como referência de calibração. O CSV local tem 18.405 linhas, foi baixado em 2026-09-23 e possui SHA-256 `cb46c2a57eff44f3c7e098a8a7e807113d0524fee3c1737c39262dcfd4e9824d`. Ele não é fonte canônica do Garfoot.

## Escala

Todos os atributos ficam entre 20 e 100. O piso 20 evita jogadores sem dados com atributos zerados; a ausência de dados deve reduzir a confiança, não apagar o jogador.

A função `limitar(x)` aplica:

$$
\operatorname{limitar}(x) = \max(20, \min(100, x))
$$

## Componentes comuns

`mercado` usa o valor de mercado em euros de forma logarítmica para evitar que os jogadores mais caros dominem toda a escala:

$$
mercado = limitar(25 + 18 \log_{10}(1 + valorMercadoEur / 100000))
$$

`experiencia` combina minutos, aparições e internacionalizações, todos com teto para evitar que longevidade substitua qualidade:

$$
experiencia = limitar(25 + \min(40, minutos/500) + \min(15, aparicoes/20) + \min(20, internacionalCaps \cdot 0.8))
$$

`contribuicao` usa gols e assistências por 90 minutos. Sem minutos, usa o piso 35:

$$
contribuicao = limitar(35 + 22 \cdot \min(1.2, gols/90) + 16 \cdot \min(1.0, assistencias/90))
$$

`maturidade` favorece o pico de 28 anos; `fisicoBase` combina curva etária e altura. Prioridades por posição impedem que uma métrica ofensiva transforme um zagueiro em atacante ou vice-versa.

Para análise, o protótipo também separa o jogador por valor de mercado:

- `elite`: a partir de €20 milhões;
- `alto`: de €5 milhões até menos de €20 milhões;
- `profissional`: de €500 mil até menos de €5 milhões;
- `desenvolvimento`: abaixo de €500 mil ou sem valor informado.

## Atributos

As fórmulas implementadas em `GeradorRatingJogador` são:

- `tecnica = 0.55 mercado + 0.25 contribuicao + 0.20 experiencia`;
- `fisico = 0.65 fisicoBase + 0.20 mercado + 0.15 prioridadePosicao`;
- `mental = 0.45 experiencia + 0.30 mercado + 0.25 maturidade`;
- `velocidade = 0.55 fisicoBase + 0.25 prioridadePosicao + 0.10 maturidade + 0.10 mercado`;
- `finalizacao = 0.55 contribuicao + 0.25 tecnica + 0.20 prioridadeFinalizacao`;
- `passe = 0.45 tecnica + 0.20 contribuicao + 0.20 experiencia + 0.15 prioridadePasse`;
- `marcacao = 0.25 mercado + 0.25 mental + 0.20 fisico + 0.30 prioridadeMarcacao`;
- `potencial = 0.45 mercado + 0.40 potencialPorIdade + 0.15 maturidade`.

As prioridades de posição são heurísticas iniciais, não atributos observados. Elas devem ser revisadas quando houver dados reais de desempenho defensivo, criação de chances e velocidade.

Após comparar os quantis por nível, o gerador aplica um offset de calibração aos atributos na ordem `tecnica`, `fisico`, `mental`, `velocidade`, `finalizacao`, `passe`, `marcacao`, `potencial`:

| Nível | Offsets |
|---|---|
| `elite` | `+18, +6, +15, +8, +23, +15, +9, +12` |
| `alto` | `+23, +5, +20, +6, +20, +18, +11, +13` |
| `profissional` | `+24, +2, +18, +5, +15, +15, +9, +16` |
| `desenvolvimento` | `+24, +0, +15, +3, +8, +12, +8, +16` |

Esses offsets são parâmetros de calibração derivados da mediana do snapshot EAFC26, não dados individuais de jogadores. Devem ser revisados quando a população inicial do Garfoot e os resultados do motor de partidas estiverem disponíveis.

## Comparação inicial

O protótipo em `scripts/prototype_player_ratings.py` agrega as aparições do Transfermarkt e gera `data/processed/ratings-prototype/`. O relatório compara P10, P50 e P90 com os campos equivalentes do EAFC26.

A primeira execução mostrou que:

- físico e velocidade ficaram próximos da referência;
- técnica, mental, passe e potencial ficaram abaixo da referência;
- finalização e marcação refletem fortemente a posição e a baixa cobertura de estatísticas avançadas;
- as populações não são equivalentes: Transfermarkt tem cerca de 50 mil jogadores e EAFC26 cerca de 18 mil.

A comparação por nível reforçou a diferença: antes dos offsets, no grupo `elite`, a técnica mediana gerada foi 62 contra 80 no EAFC26; no grupo `profissional`, 41 contra 65. O nível de mercado está separando corretamente a população, e os offsets corrigem parte da escala sem substituir os dados de origem.

Portanto, a fórmula é adequada como baseline técnico, mas não deve ser considerada balanceada até ser testada no motor de partidas. O motor inicial usa `ForcaEquipe` para combinar os ratings em ataque e defesa. A expectativa de gols fica limitada a `0.15..3.50` por equipe, com mando de campo de `0.15`, e os gols são amostrados por minuto com um gerador determinístico quando recebe um seed.

Com escalações, o motor também amostra cartões amarelos, cartões vermelhos, lesões e até três substituições por equipe. Cada evento mantém seu `TipoEvento`, minuto, jogador opcional e descrição narrativa. A narração é derivada desses mesmos eventos, evitando uma segunda representação que possa divergir do placar.

## Auditoria inicial do motor (2026-09-23)

Uma amostra de 10.000 jogos neutros entre equipes de força 60/60, após o ajuste da expectativa-base de gols de 0,55 para 0,72, mediu média de **2,299 gols**, **39,5%** de vitórias do mandante, **28,1%** de empates, **9,9%** de placares 0-0 e nenhum caso em que uma equipe marcou oito ou mais gols. A calibração contra os 380 jogos completos da Série A 2024 está em [`11-calibracao-partidas-reais.md`](11-calibracao-partidas-reais.md).

Em 2.000 seeds por confronto, equipes com força crescente contra adversários espelhados tiveram taxas de vitória de **22,45%** (35 contra 65), **35,8%** (50 contra 50), **52,05%** (65 contra 35) e **73,5%** (85 contra 15). O teste confirma correlação monotônica entre força e vitória, sem placares extremos frequentes. Esses resultados sustentam o baseline atual; não justificam alterar parâmetros nesta etapa.

Uma segunda auditoria simulou **100 temporadas completas** de quatro clubes neutros (1.200 partidas). A média foi **1,772 gols por partida**, com **16,1%** de 0-0 e nenhum caso de oito ou mais gols por equipe. A amostra reproduzível não substitui uma população de elencos realistas, mas confirma que a agregação por temporada não introduziu placares extremos.

### Auditoria posicional 4-4-2

O sorteio original escolhia qualquer jogador com a mesma chance de marcar. Em 10.000 partidas com elencos 4-4-2 posicionais, goleiros representaram 5,6% dos autores de gol, acima do esperado. O motor passou a ponderar finalização e técnica por um multiplicador de posição: GOL `0,10`, ZAG `0,65`, LAT `0,85`, VOL `0,90`, MEI `1,15`, ATA `1,35`. A expectativa e a quantidade de gols da partida não mudaram.

Na amostra atualizada de 10.000 partidas, os autores foram ATA 8.867, MEI 5.844, LAT 2.819, VOL 2.079, ZAG 2.099 e GOL 119. Em 50 temporadas completas com quatro clubes posicionais (600 jogos), ocorreram 2,228 gols por jogo e 10,3% de 0-0; não houve placares com oito ou mais gols. Pontos acumulados por nível foram 283 (`40`), 351 (`55`), 463 (`70`) e 527 (`85`); os atacantes marcaram 522 gols e os goleiros seis.

Em 4.000 confrontos entre elencos posicionais de níveis espelhados, as taxas de vitória do mandante de força crescente foram 16,1%, 26,3%, 43,7% e 59,9%. A priorização posicional é uma heurística de gameplay, ainda sem calibração contra dados de uma liga real; deve ser revista quando o motor considerar escalações táticas reais e amostras de partidas observadas.

Limitações: os elencos posicionais são fixtures sintéticas, não uma população importada do Transfermarkt; `ForcaEquipe` usa médias de elenco e não tática, condição, moral ou mando na seleção dos onze. O próximo risco é comparar a regra com escalações e resultados reais antes de tratar o balanceamento como concluído.

## Execução

```bash
python3 scripts/prototype_player_ratings.py
./mvnw -q -pl core test
```
