# Chuva horária em São Paulo – Interlagos (A771)

O [CSV](chuva_a771.csv) traz a precipitação medida na estação automática A771 do INMET a cada hora local, de 01/01/2022 00h até 30/09/2026 23h. A série permite testar se uma segunda estação, ao sul da cidade, acrescenta informação às leituras do Mirante de Santana (A701). O recorte temporal e o cálculo das distâncias utilizam apenas medições e geografia. [Catálogo de dados históricos do INMET](https://portal.inmet.gov.br/dadoshistoricos)

## Leituras e distâncias

O campo oficial `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)` informa o volume acumulado na hora encerrada na marca de tempo. Os CSVs do INMET usam UTC e o extrator converte para a hora de São Paulo (UTC−3 durante todo o estudo). Por exemplo, uma leitura às 18h locais equivale à linha das 21h UTC. Em `chuva_mm`, zero representa medição de 0 mm e uma célula vazia representa valor ausente, negativo ou hora sem linha. Os acumulados de três e de 24 horas exigem três e 24 leituras horárias consecutivas observadas, respectivamente.

| Ano local | Horas da grade | Medições válidas | Horas com 24 leituras consecutivas |
|---|---:|---:|---:|
| 2022 | 8.760 | 8.277 | 8.162 |
| 2023 | 8.760 | 8.588 | 8.086 |
| 2024 | 8.784 | 8.775 | 8.597 |
| 2025 | 8.760 | 8.731 | 8.303 |
| 2026 (jan–set) | 6.552 | 6.551 | 6.528 |

Os cabeçalhos do INMET identificam a A771 como São Paulo – Interlagos, altitude 771 m. Nos arquivos de 2024 a 2026, a posição é −23,72444443°, −46,67749999°. Em 2022–2023 aparece como −23,724501°, −46,677501°, diferença de cerca de seis metros. Para a comparação abaixo, calculamos a distância geodésica no elipsoide WGS84 entre a posição informada desde 2024 e o ponto representativo de cada cruzamento. A proximidade ajuda a selecionar a estação, mas ainda pode haver chuva localizada entre o pluviômetro e a rua. [Coordenadas dos cruzamentos](../geografia/atributos_trechos.csv)

| Local | Interlagos A771 | Mirante A701 | Mais próxima entre as duas |
|---|---:|---:|---|
| RS01 | 15,15 km | 12,47 km | Mirante |
| RS02 | 5,03 km | 21,86 km | Interlagos |
| RS03 | 11,02 km | 16,10 km | Interlagos |
| RS04 | 10,93 km | 15,95 km | Interlagos |

## Reprodução

Baixe os ZIPs anuais para uma pasta local, preservando os nomes `2022.zip` a `2026.zip`. O [extrator](extrair_interlagos.py) usa a biblioteca padrão do Python 3.11 ou mais recente e lê apenas o CSV da A771 em cada arquivo. Na edição consultada em 10/11/2026, o arquivo de 2026 ia até 31 de outubro. O código descarta medições posteriores ao recorte em hora local. [2022](https://portal.inmet.gov.br/uploads/dadoshistoricos/2022.zip) · [2023](https://portal.inmet.gov.br/uploads/dadoshistoricos/2023.zip) · [2024](https://portal.inmet.gov.br/uploads/dadoshistoricos/2024.zip) · [2025](https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip) · [2026](https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip)

```powershell
py -3 ml/dados/chuva_interlagos/extrair_interlagos.py --zips C:\dados\inmet --saida chuva_a771_conferencia.csv
Get-FileHash -Algorithm SHA256 chuva_a771_conferencia.csv
```

O SHA-256 do CSV versionado é `6b7c42f32ff93a95b9776f2e15cdcbb24fe443554d74ff98af1d75266f161c23`. As assinaturas abaixo são do CSV bruto completo da A771 dentro de cada ZIP consultado. O pacote do ano em andamento pode mudar quando o INMET acrescentar observações.

| Ano UTC | SHA-256 do CSV da A771 |
|---|---|
| 2022 | `0901762f6fdf4fad8f00ed1585744ffc6cd00cd33a4e98a31c445d773e47988c` |
| 2023 | `60d41df7f6603abd7476579fbf4d0ebd8d74b71626a1679ea06f06e34077b00b` |
| 2024 | `2c8d30b338d6f265c714563a66f4145232275d6d18995bb97f04afc3fd67ea31` |
| 2025 | `9471fa2fe763cc12e8eb4fddce31828d4ec1be985f0c64112ee50e9549df4892` |
| 2026 | `eae61d8de73747df3ce36b8377cad87dd1778b5fd9d9b7c01d707f7917069177` |
