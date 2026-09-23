---
name: garfoot-match-engine
description: "Use when implementing or changing MotorSimulacaoPartida, formulas de força ofensiva/defensiva, probabilidades, eventos de partida, placares, narração ou testes estatísticos do motor."
argument-hint: "Descreva a regra, fórmula ou tipo de evento da partida"
---

# Garfoot Match Engine

## Fonte de verdade

Consulte [03-especificacao-de-requisitos.md](../../../docs/03-especificacao-de-requisitos.md), especialmente RF-02, e [05-modelo-de-dominio.md](../../../docs/05-modelo-de-dominio.md). O motor deve ser independente da UI e determinístico quando recebe um seed fixo.

## Procedimento para regras e fórmulas

1. Identifique as entradas da regra: força do elenco, ataque, defesa, tática, condição, moral, mando e aleatoriedade.
2. Normalize atributos e pesos antes de combiná-los. Evite que um único atributo domine a fórmula sem justificativa documentada.
3. Mantenha a aleatoriedade injetável ou controlada por seed. Não use `Object.hashCode`, hash de coleção ou qualquer fonte não determinística para decidir o resultado.
4. Faça a mudança em uma etapa pequena: fórmula, distribuição de eventos e narração devem poder ser validadas separadamente.
5. Não fixe placares para fazer um teste passar. Valide propriedades da distribuição em muitas partidas com seed controlado: variação de resultados, média plausível, frequência de 0-0 e limites de placares extremos.
6. Use limites de sanidade para detectar gols absurdos, sem transformar um valor de teste estatístico em uma regra artificial do jogo. Valores e tolerâncias devem ser justificados pelo domínio.

## Novos eventos de partida

1. Adicione o tipo ao enum ou contrato de eventos no pacote de partida.
2. Defina os dados mínimos do evento e preserve compatibilidade com consumidores existentes.
3. Atualize o narrador textual com um caso explícito e uma mensagem segura para dados incompletos.
4. Garanta que serialização, persistência e apresentação não dependam de um `switch` esquecido.
5. Teste a criação do evento, sua ordenação por minuto e a saída textual do narrador.

## Checklist de validação

- [ ] Seed fixo produz exatamente o mesmo resultado.
- [ ] Seeds diferentes podem produzir resultados diferentes.
- [ ] A distribuição não fica concentrada em um único placar.
- [ ] Placares extremos são raros e não há gols impossíveis para a regra.
- [ ] Eventos permanecem ordenados e narráveis.
- [ ] O motor não importa UI, persistência ou rede.
- [ ] Testes unitários cobrem a regra nova e regressões próximas.
