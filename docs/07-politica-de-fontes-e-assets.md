# Política de Fontes de Dados e Assets

## Decisão

O Garfoot usará o snapshot do `dcaribou/transfermarkt-datasets` como fonte canônica inicial para dados de clubes, jogadores, partidas, eventos, escalações, transferências, valores de mercado, competições, países e seleções.

O snapshot é adequado para a proposta do projeto porque contém dados posteriores a `01/01/2026`: a fonte informa cobertura até `06/07/2026`. A atualização do pipeline está pausada, portanto essa data deve ser tratada como limite conhecido, não como atualização em tempo real.

## Fontes avaliadas

| Fonte | Decisão | Uso |
|---|---|---|
| `dcaribou/transfermarkt-datasets` | Canônica | Dados relacionais principais do jogo |
| `openfootball/clubs` | Complementar | Clubes, estádios, nomes alternativos e validação |
| `openfootball/*` | Complementar | Calendários e resultados de competições específicas |
| `salimt/football-datasets` | Opcional | Enriquecimento de jogadores, lesões e desempenho, após auditoria |
| `football-data-webscraping` | Auxiliar | Coletas pontuais de lacunas, não fonte persistente automática |
| `worldfootballR` | Não usar | Repositório arquivado em setembro de 2025 |
| Kaggle `player-scores` | Não duplicar | Distribuição alternativa do dataset do dcaribou |

O `dcaribou/transfermarkt-datasets` e o `openfootball` informam CC0/domínio público. O toolkit `football-data-webscraping` informa licença MIT para o código, mas isso não concede automaticamente direitos sobre os dados raspados. A licença do dataset `salimt/football-datasets` não foi confirmada e ele não deve ser incorporado como fonte distribuída até essa verificação.

O fato de o Garfoot ser um projeto pessoal não elimina a necessidade de respeitar licenças, termos de uso, `robots.txt` e políticas das fontes.

## Catálogo de fontes por entidade

| Entidade ou informação | Fonte canônica | Onde baixar ou consultar | Fonte complementar | Situação |
|---|---|---|---|---|
| Clubes | `dcaribou/transfermarkt-datasets` | [ZIP do snapshot](https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/transfermarkt-datasets.zip), tabela `clubs.csv` | [openfootball/clubs](https://github.com/openfootball/clubs) | Baixado e extraído |
| Dados de estádio | `dcaribou/transfermarkt-datasets` | `clubs.csv`, campos `stadium_name` e `stadium_seats` | `openfootball/clubs` | Disponível, sujeito a lacunas |
| Jogadores | `dcaribou/transfermarkt-datasets` | Tabela `players.csv` | [salimt/football-datasets](https://github.com/salimt/football-datasets) | Baixado e extraído |
| Desempenho de jogadores | `dcaribou/transfermarkt-datasets` | `appearances.csv`, `game_lineups.csv` e `player_valuations.csv` | `salimt/football-datasets` | Disponível no snapshot |
| Transferências | `dcaribou/transfermarkt-datasets` | Tabela `transfers.csv` | `salimt/football-datasets` | Baixado e extraído |
| Partidas | `dcaribou/transfermarkt-datasets` | `games.csv` e `club_games.csv` | [openfootball](https://github.com/openfootball) por competição | Disponível até 2026-07-06 |
| Eventos de partida | `dcaribou/transfermarkt-datasets` | Tabela `game_events.csv` | Scraping pontual, se necessário | Disponível no snapshot |
| Competições | `dcaribou/transfermarkt-datasets` | Tabela `competitions.csv` | `openfootball/*` | Disponível |
| Países e confederações | `dcaribou/transfermarkt-datasets` | Tabela `countries.csv` | `openfootball` | Disponível |
| Seleções nacionais | `dcaribou/transfermarkt-datasets` | Tabela `national_teams.csv` | `openfootball/worldcup` e competições internacionais | Disponível |
| Técnicos de clubes | `dcaribou/transfermarkt-datasets` | Campo `clubs.coach_name` | Scraping pontual autorizado e documentado | Parcial: 403/796 |
| Técnicos de seleções | Nenhuma fonte integrada | Campo `national_teams.coach_name` | Scraping pontual ou fonte específica | Ausente: 0/124 |
| Comissão técnica | Nenhuma fonte integrada | Não existe tabela no snapshot | `football-data-webscraping` como ferramenta, não dataset | Não disponível |
| Escudos de clubes | CDN referenciada pela Transfermarkt | `https://img.a.transfermarkt.technology/wappen/homepage/{club_id}.png` | Fonte de assets a avaliar | 796 baixados |
| Escudos de seleções | URL `team_image_url` do dataset | Campo `national_teams.team_image_url` | Fonte de assets a avaliar | 124 baixados |
| Fotos de jogadores | URL `image_url` do dataset | Campo `players.image_url` | Não necessária inicialmente | Script pronto, download sob demanda |
| Bandeiras | FlagCDN | [Catálogo de códigos](https://flagcdn.com/en/codes.json) e `https://flagcdn.com/w320/{iso2}.png` | Fonte de assets a avaliar | 121 baixadas |

O ZIP principal também está disponível no [repositório dcaribou](https://github.com/dcaribou/transfermarkt-datasets), que documenta o esquema, o snapshot e a licença. O arquivo local e seu hash estão registrados em [data/external/transfermarkt/README.md](../data/external/transfermarkt/README.md).

### Fontes que podem ser incorporadas depois

- [openfootball/clubs](https://github.com/openfootball/clubs): lista pública de clubes e estádios, útil para nomes alternativos e validação; não fornece perfis completos de jogadores.
- [openfootball/football.json](https://github.com/openfootball/football.json): calendários e resultados em JSON para competições cobertas.
- [salimt/football-datasets](https://github.com/salimt/football-datasets): conjunto mais amplo de jogadores, lesões e desempenho; requer confirmação da licença antes de distribuição.
- [football-data-webscraping](https://github.com/sahil-gidwani/football-data-webscraping): código MIT para coletas pontuais; requer respeito às políticas dos sites e não deve ser executado como raspagem indiscriminada.

## Regra de integração

Uma entidade deve ter uma fonte canônica. Fontes complementares não substituem silenciosamente o registro canônico. Quando for necessário cruzar fontes, manter uma correspondência explícita:

```text
source_entity_links
- source
- source_entity_id
- garfoot_entity_id
- match_method
- confidence
- verified_at
```

O cruzamento deve preferir IDs da fonte. Nomes são apenas fallback e precisam ser normalizados e revisados, pois podem variar por idioma, acentos, abreviações, patrocinadores e categorias de base.

## Cobertura de técnicos

A auditoria do snapshot foi feita com parser CSV, para não quebrar nomes que contêm vírgulas.

- `clubs.csv`: possui `coach_name` preenchido em 403 de 796 clubes.
- `national_teams.csv`: possui a coluna `coach_name`, mas nenhum dos 124 registros tem valor preenchido.
- Não existe tabela separada para auxiliares, preparadores, diretores ou comissão técnica.
- Os registros de clubes fornecem somente o nome do técnico, sem ID estável ou perfil detalhado.

A importação deve tratar técnico como dado opcional. Não criar técnicos fictícios para completar registros ausentes.

## Assets de mídia

O dataset principal não fornece diretamente escudos de clubes nem bandeiras de países.

| Asset | Fonte | Identificador local |
|---|---|---|
| Escudo de clube | URL derivada do `club_id` na CDN da Transfermarkt | `club-badges/{club_id}.png` |
| Escudo de seleção | `national_teams.team_image_url` | `national-badges/{national_team_id}.png` |
| Foto de jogador | `players.image_url` | `player-photos/{player_id}.jpg` |
| Bandeira | FlagCDN, usando código ISO resolvido por nome | `flags/{iso2}.png` |

A carga inicial já validou e baixou 796 escudos de clubes, 124 escudos de seleções e 121 bandeiras únicas. As fotos dos jogadores ficam preparadas para download, mas não são baixadas automaticamente pela carga inicial devido ao volume de aproximadamente 50 mil arquivos.

Os assets ficam em `data/assets/transfermarkt/`, são derivados e ignorados pelo Git. Cada download usa cache, atraso entre requisições, arquivo temporário e relatório em `download-failures.txt`.

## Comandos de assets

Carga inicial de escudos e bandeiras:

```bash
python3 scripts/download_transfermarkt_assets.py \
  --assets clubs,flags,national-teams
```

Carga explícita das fotos dos jogadores:

```bash
python3 scripts/download_transfermarkt_assets.py \
  --assets players
```

Teste limitado:

```bash
python3 scripts/download_transfermarkt_assets.py \
  --assets clubs,flags,national-teams,players \
  --limit 10
```

Use `--force` apenas para renovar arquivos existentes. Falhas não devem ser ignoradas: o relatório deve ser revisado antes de considerar uma carga completa.

## Atualização e rastreabilidade

Toda atualização de dados deve registrar:

- URL de origem;
- data de download;
- data final de cobertura;
- licença informada;
- SHA-256 do arquivo bruto;
- alterações de esquema;
- quantidade de registros e assets;
- falhas de download;
- decisão sobre compatibilidade com o modelo do Garfoot.

Dados externos servem para povoar o mundo inicial e fixtures de desenvolvimento. Testes de domínio devem usar fixtures pequenas, determinísticas e versionáveis, sem depender da rede ou do snapshot completo.
