# Calibração com partidas reais

Fonte: dataset Transfermarkt local (`data/external/transfermarkt/transfermarkt-datasets.zip`), competição `BRA1`, temporadas `2024`.
Os resultados são usados somente neste relatório; o jogo continua offline e não incorpora CSVs externos ao motor.

| Métrica | Jogos reais | Motor (auditoria 10.000 partidas) | Diferença |
|---|---:|---:|---:|
| Partidas | 380 | 10000 | 9620 |
| Gols por partida | 2.524 | 2.299 | -0.225 |
| Vitória mandante | 0.503 | 0.395 | -0.108 |
| Empate | 0.261 | 0.281 | 0.020 |
| Vitória visitante | 0.237 | 0.324 | 0.087 |
| 0 × 0 | 0.071 | 0.099 | 0.028 |
| 8+ gols | 0.003 | 0.000 | -0.003 |

## Observações

A base oferece 380 jogos completos de 2024 na Série A; 2025 está incompleto no snapshot e foi excluído.
Após o primeiro ajuste de gols-base, a média e a frequência de empates/placares sem gols se aproximaram da amostra histórica.
A taxa de vitória mandante segue abaixo da referência; calibrar o mando em seguida, sem sacrificar a relação entre força e resultado.
A amostra histórica contém regras, elencos e contextos de várias épocas; a comparação é indicativa, não uma validação preditiva.
