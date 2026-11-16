# Chuva horária de São Paulo · estação A701

O [CSV de chuva](chuva_a701.csv) contém a precipitação da estação automática **São Paulo – Mirante de Santana (A701)** do Instituto Nacional de Meteorologia. A série cobre todas as horas locais entre 1º de janeiro de 2022 e 31 de dezembro de 2025. A latitude e a longitude informadas em 2025 são −23,49629 e −46,62007, a 785,64 m de altitude. Uma estação representa a chuva medida junto ao instrumento. Pancadas localizadas podem atingir um trecho da cidade com intensidade diferente. [Séries anuais do INMET](https://portal.inmet.gov.br/dadoshistoricos)

## Como ler

- `hora_local` é o horário de São Paulo (UTC−3 em todo o período). A marca de 14h contém a precipitação medida durante a hora que terminou às 14h. Para calcular o alerta das 14h, essa leitura só pode entrar se já tiver chegado ao sistema. [Definição de precipitação horária do INMET](https://portal.inmet.gov.br/glossario/glossario)
- `chuva_mm` é o total de precipitação da última hora em milímetros. O valor 0 indica leitura de zero, e uma célula vazia indica hora sem medição válida. A intensidade média em mm/h tem o mesmo valor numérico neste intervalo de uma hora.
- O extrator lê o campo `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)`, converte vírgula decimal e deixa vazios os campos ausentes ou negativos, incluindo o marcador −9999. Depois completa a grade de horas. Para um acumulado de 24 h, são necessárias 24 leituras válidas consecutivas. O INMET disponibiliza as observações automáticas como dados brutos. [Orientações do INMET](https://portal.inmet.gov.br/noticias/saiba-como-acessar-os-dados-meteorol%C3%B3gicos-dispon%C3%ADveis-no-site-do-inmet)

## Cobertura do pluviômetro

| Ano local | Horas no período | Com leitura | Ausentes | Com chuva acima de zero |
|---|---:|---:|---:|---:|
| 2022 | 8.760 | 8.759 | 1 | 762 |
| 2023 | 8.760 | 8.115 | 645 | 625 |
| 2024 | 8.784 | 8.764 | 20 | 689 |
| 2025 | 8.760 | 8.713 | 47 | 565 |
| **Total** | **35.064** | **34.351** | **713** | **2.641** |

A maior sequência de leituras ausentes foi de 219 horas. Uma lacuna na estação pode inviabilizar várias estimativas seguidas, já que os acumulados também dependem das horas anteriores.

## Reconstrução

O CSV versionado já permite executar o estudo. Para conferi-lo contra a fonte, baixe os ZIPs anuais das estações automáticas de [2022](https://portal.inmet.gov.br/uploads/dadoshistoricos/2022.zip), [2023](https://portal.inmet.gov.br/uploads/dadoshistoricos/2023.zip), [2024](https://portal.inmet.gov.br/uploads/dadoshistoricos/2024.zip), [2025](https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip) e [2026](https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip) para uma pasta fora do repositório, mantendo os nomes originais. Os ZIPs nacionais abrangem centenas de estações. O extrator usa apenas o CSV cujo nome contém `_A701_`. As últimas três horas locais de 31/12/2025 correspondem às 00h, 01h e 02h UTC de 01/01/2026, por isso a reconstrução lê também o ZIP de 2026.

Em PowerShell, na raiz do repositório, ajuste o caminho da pasta de downloads. A saída de conferência vai para a pasta temporária do Windows.

```powershell
$zipsInmet = 'C:\dados\inmet'
$conferencia = Join-Path $env:TEMP 'chuva_a701_conferencia.csv'
py -3 .\ml\dados\chuva\extrair_chuva.py --zips $zipsInmet --saida $conferencia
Get-FileHash -Algorithm SHA256 $conferencia
```

O SHA-256 do CSV utilizado é `54142d5aed430514650d9abb0da124326aa18a51037800e4b5d66dc1e284bf1c`. A tabela registra os hashes dos arquivos CSV de origem da A701 descompactados, obtidos em 09/11/2026. O ZIP de 2026 pode ganhar novas linhas conforme o INMET atualiza a série.

| Arquivo de origem por ano UTC | SHA-256 do CSV completo da estação |
|---|---|
| 2022 | `ceb3a4cde159602228959b96c32eb46134f37b9b3b84c90126d8cbf169d8d088` |
| 2023 | `ae52e888aa15f03e64c04cc0400896091d32da1ad4a303fdcb830cead9f78c44` |
| 2024 | `c5f365c069258734ba108f4e85e71ddb00a8a9d4c936b4a7ec76afd9c00fd276` |
| 2025 | `1eac048271dd0339613149e4638b293f5b627c847980a2b0853c725217e0a314` |
| 2026 (jan–out) | `cd32ce32979616192fda9c29f838c734cedde393ec1660f7eb6474b4eda371d5` |
