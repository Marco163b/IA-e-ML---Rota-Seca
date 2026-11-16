# Avaliação temporal de janeiro a setembro de 2026

Os quatro cruzamentos RS01–RS04 conservam a identificação do estudo de 2023–2025. Os registros de 2026 foram separados para avaliar modelos e limiares definidos com os dados anteriores. A previsão continua sendo o início de um registro do CGE no intervalo após a emissão até uma hora adiante.

## Fontes desta edição

- Os [boletins do CGE](https://www.cgesp.org/v3/alagamentos.jsp) cobrem **273 dias consecutivos**, de 01/01/2026 a 30/09/2026. O [extrator](../cge/extrair_cge.py) conferiu a data de cada página e a soma das quatro categorias, e exigiu confirmação explícita nos dias vazios. [Cobertura por dia](cobertura.csv) · [Registros correspondentes aos quatro locais](eventos.csv)
- O [arquivo anual do INMET](https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip) contém o membro `INMET_SE_SP_A701_SAO PAULO - MIRANTE_01-01-2026_A_31-10-2026.CSV` nesta edição, com SHA-256 `cd32ce32979616192fda9c29f838c734cedde393ec1660f7eb6474b4eda371d5`. Para a avaliação, extraímos **6.493 medições válidas em 6.552 horas** de janeiro a setembro. O CSV em horário civil de São Paulo (UTC−3) tem SHA-256 `1f6688437d511db686e04ad608311873475b4928ffd982f490a5ffad287f667e`. [Chuva horária da A701](chuva_a701.csv)
- O [cadastro dos cruzamentos](../cge/trechos.csv) e os [atributos geográficos](../geografia/atributos_trechos.csv) são os mesmos da versão de referência. As camadas geográficas descrevem uma aproximação estática do terreno.

## Formação do painel de referência

O [painel de 2026](painel_trecho_hora.csv.gz) tem as mesmas colunas do [painel histórico](../README.md). O preparo reutiliza o histórico de ocorrências desde 2023 até o fim da véspera de cada previsão e a chuva até a hora de emissão, incluindo as leituras de dezembro de 2025 para as primeiras janelas de janeiro. Uma previsão exige 24 horas consecutivas de chuva válida da A701. A última emissão elegível é 30/09/2026 às 22h, para que o desfecho observado esteja dentro dos dias conferidos.

Das 26.204 combinações de cruzamento e hora possíveis, **23.328** têm janela completa da A701. Outra implementação conferiu cada rótulo com o horário dos inícios registrados, o histórico até a véspera, as três janelas de chuva e as características geográficas. Na comparação entre modelos, a disponibilidade simultânea das estações pode reduzir esse total. O SHA-256 do painel completo da A701 é `c460b189e69ff279e05bc23eb6714a459e3f446d8c87c713e38010c5f291082b`.

## Como reproduzir

O repositório inclui os CSVs necessários para reconstituir o painel. Na raiz do repositório, com o ambiente de `ml/requirements.txt` já instalado:

```powershell
& .\.venv\Scripts\python.exe ml/dados/avaliacao_2026/preparar_avaliacao.py --saida "$env:TEMP\rota-seca-2026.csv.gz"
Get-FileHash ml/dados/avaliacao_2026/painel_trecho_hora.csv.gz,"$env:TEMP\rota-seca-2026.csv.gz" -Algorithm SHA256
```

Para refazer os CSVs a partir das fontes públicas, use `$zipsInmet` como a pasta que contém o `2026.zip` e uma pasta local para o cache HTML. O extrator do CGE também requer `beautifulsoup4`, conforme a [documentação de coleta](../cge/README.md). Ele reaproveita os boletins existentes e consulta em série os dias ausentes. A Prefeitura e o INMET podem revisar os arquivos públicos.

```powershell
$conf2026 = Join-Path $env:TEMP 'rota-seca-fontes-2026'
py -3 ml/dados/cge/extrair_cge.py --inicio 2026-01-01 --fim 2026-09-30 --cache "$conf2026/boletins" --saida $conf2026 --baixar
py -3 ml/dados/chuva/extrair_chuva.py --zips $zipsInmet --inicio 2026-01-01 --fim-exclusivo 2026-10-01 --saida "$conf2026/chuva_a701.csv"
& .\.venv\Scripts\python.exe ml/dados/avaliacao_2026/preparar_avaliacao.py --fontes $conf2026 --saida "$conf2026/painel_trecho_hora.csv.gz"
```
