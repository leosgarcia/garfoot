# Pirâmide brasileira inicial — temporada 2026

## Decisão de produto

Cada país tem campeonatos e classificações próprios. A escolha de mais de um país representa destinos possíveis para a carreira do técnico; não mistura clubes de nacionalidades diferentes numa tabela. O primeiro início jogável é o Brasil: Série B, com 20 clubes, por ser a última divisão jogável do modo Free. A Série A também está catalogada com seus 20 clubes para viabilizar a progressão futura.

## Dados implementados

O recurso versionado [`ligas-brasil-2026.json`](../ui/src/main/resources/data/ligas-brasil-2026.json) contém:

- 20 participantes da Série A e 20 participantes da Série B;
- metadados do regulamento de 2026 (38 rodadas, 4 acessos e 4 rebaixamentos; na Série B real o acesso de 2026 tem playoffs entre posições 3–6);
- elencos Transfermarkt do snapshot local de 2026-07-06 quando houve correspondência;
- elencos sintéticos claramente identificados para os clubes sem correspondência;
- oito clubes fictícios como reserva distrital, sem calendário próprio.

Os vinte participantes da Série A têm correspondência de clube e elenco no snapshot. Na Série B, quatro clubes têm elenco correspondente: Ceará, Fortaleza, Juventude e Sport; os outros dezesseis têm elenco sintético. O snapshot não deve ser lido como uma fotografia exata do plantel no primeiro dia de 2026. Alguns elencos correspondidos também recebem atletas sintéticos para completar posições mínimas da formação, marcando o elenco como completado.

O snapshot Transfermarkt foi obtido e preparado conforme a licença e o hash registrados em [`data/external/transfermarkt/README.md`](../data/external/transfermarkt/README.md). A lista de participantes foi conferida nas fontes abaixo:

- [CBF — Série A 2026](https://www.cbf.com.br/futebol-brasileiro/times/campeonato-brasileiro/serie-a/2026)
- [CBF — formato da Série B 2026](https://www.cbf.com.br/futebol-brasileiro/noticias/jogos-inesqueciveis/campeonato-de-selecoes-estaduais-30-edicoes/brasileirao-serie-b-comeca-com-novo-formato)
- [ge — lista dos 20 clubes da Série B](https://ge.globo.com/pe/futebol/brasileirao-serie-b/noticia/2025/12/07/serie-b-de-2026-tem-todos-os-seus-20-clubes-participantes-definidos-veja-lista.ghtml)

## Distrital e progressão

A distrital é um reservatório agregado no modelo: não cria calendário nem partidas para centenas de clubes. Nesta primeira temporada ele demonstra a estrutura de reserva. A promoção/rebaixamento entre Série A e B e a reposição da B a partir do distrito ainda precisam de regras de fim de temporada e serão bons alvos para a validação manual e o próximo incremento.

## Escopo de países

O modelo persiste país, divisão, países escolhidos para a carreira e clubes distritais por país. Nesta entrega, somente Brasil possui dados e pode ser selecionado. Inglaterra, Espanha, Itália, Alemanha e França seguem como candidatos para uma próxima carga, preservando o formato real de cada liga em vez de forçar quatro divisões de vinte clubes.

## Limitações para validação manual

- O calendário da temporada de jogo é gerado pelo motor da aplicação; não é uma importação do calendário oficial da CBF.
- A temporada inicial é rotulada 2026, mas os elencos são uma base aproximada do snapshot de 6 de julho, com as lacunas acima.
- O acesso da Série B 2026 usa playoffs na competição real. A regra completa de playoffs e a transição entre temporadas não estão simuladas ainda.
- O catálogo da Série A está disponível como dado, mas o início Free configurado leva à Série B.
