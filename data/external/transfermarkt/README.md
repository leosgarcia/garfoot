# Dataset Transfermarkt

Fonte externa usada como base de dados inicial do Garfoot.

O catálogo completo, por entidade e por tipo de asset, está em [`docs/07-politica-de-fontes-e-assets.md`](../../../docs/07-politica-de-fontes-e-assets.md).

## Origem

- Repositório: https://github.com/dcaribou/transfermarkt-datasets
- Download: https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/transfermarkt-datasets.zip
- Licença informada pela fonte: CC0-1.0
- Snapshot informado pela fonte: dados até 2026-07-06
- Data do download local: 2026-09-23
- SHA-256 do ZIP local: `ae2270f7820e09329c423a12562f4494e237d0dc1a4624cff21df050e79d5a18`

A fonte informa que as atualizações estão pausadas. O snapshot não cobre necessariamente elencos da temporada 2026/27 e não deve ser tratado como uma fonte online em tempo real.

## Organização local

```text
transfermarkt/
├── README.md
├── transfermarkt-datasets.zip       # download bruto, ignorado pelo Git
└── raw/                              # tabelas CSV e CSV.GZ, ignoradas pelo Git
```

As tabelas estão disponíveis em `*.csv` para inspeção e importação direta, enquanto os arquivos `*.csv.gz` originais são preservados para rastreabilidade. O código do Garfoot deve importar os dados por uma etapa explícita, sem acoplar o domínio ao esquema externo.

## Tabelas relevantes

| Tabela | Uso inicial no Garfoot |
|---|---|
| `clubs` | cadastro de clubes, estádio, técnico e valores agregados |
| `players` | cadastro, posição, idade, nacionalidade e valores de mercado |
| `games` | histórico e calendário de partidas |
| `game_events` | gols, cartões, substituições e eventos históricos |
| `game_lineups` | titulares, banco e posições em partidas históricas |
| `transfers` | histórico de transferências e valores |
| `player_valuations` | histórico de valor de mercado |
| `competitions` | competições e países associados |
| `countries` | países e confederações |
| `national_teams` | seleções nacionais |
| `appearances` | minutos, gols, assistências e cartões por jogador |
| `club_games` | visão por clube do resultado de cada partida |

### Técnicos

- `clubs.csv` possui `coach_name` preenchido em 403 de 796 clubes.
- `national_teams.csv` possui `coach_name`, mas os 124 registros estão vazios.
- Não há tabela separada para comissão técnica, auxiliares, preparadores ou diretores.
- O nome do técnico não possui ID estável ou perfil detalhado no snapshot.

## Regenerar localmente

```bash
mkdir -p data/external/transfermarkt/raw
curl -L --fail --show-error --retry 3 \
  --output data/external/transfermarkt/transfermarkt-datasets.zip \
  https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/transfermarkt-datasets.zip
unzip -oq data/external/transfermarkt/transfermarkt-datasets.zip \
  -d data/external/transfermarkt/raw
for file in data/external/transfermarkt/raw/*.csv.gz; do
  gzip -dkf "$file"
done
```

Antes de atualizar o snapshot, confira a licença, a data de referência, o hash do arquivo e as mudanças de esquema. Os dados externos não substituem fixtures pequenas e determinísticas dos testes.

## Assets de mídia

O downloader em [`scripts/download_transfermarkt_assets.py`](../../../scripts/download_transfermarkt_assets.py) cria assets locais por identificador:

```bash
python3 scripts/download_transfermarkt_assets.py \
  --assets clubs,flags,national-teams
```

Para baixar também as fotos dos 50 mil jogadores, use a opção explícita:

```bash
python3 scripts/download_transfermarkt_assets.py \
  --assets clubs,flags,national-teams,players
```

Os assets derivados ficam em `data/assets/transfermarkt/` e não são versionados. O script usa cache, limite opcional, atraso entre requisições e relatório de falhas. As bandeiras são obtidas da FlagCDN; escudos e fotos usam URLs referenciadas pela Transfermarkt.

Para a política completa de fontes, licenças, correspondência entre entidades, técnicos e rastreabilidade, consulte [`07-politica-de-fontes-e-assets.md`](../../../docs/07-politica-de-fontes-e-assets.md).
