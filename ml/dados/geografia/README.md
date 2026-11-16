# Geografia dos quatro trechos

O [CSV de atributos](atributos_trechos.csv) associa cada identificador do estudo a um ponto representativo do cruzamento citado pelo CGE. Consultamos a cartografia da Prefeitura de São Paulo em 09/11/2026. A localização de referência é a mesma para todas as horas analisadas. [GeoSampa](https://novogeosampa.prefeitura.sp.gov.br/) · [Serviço municipal WFS](https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs?service=WFS&version=2.0.0&request=GetCapabilities)

| Trecho | Cruzamento de referência | Códigos municipais das vias | Distrito do ponto |
|---|---|---|---|
| RS01 | Av. das Nações Unidas × Rua Olívia Feder | 062383 × 480193 | Itaim Bibi |
| RS02 | Av. das Nações Unidas × Rua Jaime de Oliveira Souza | 062383 × 639664 | Campo Grande |
| RS03 | Av. Roque Petroni Júnior × Rua Cancioneiro Popular | 215147 × 181196 | Santo Amaro |
| RS04 | Av. Santo Amaro × Av. Roque Petroni Júnior | 009997 × 215147 | Santo Amaro |

## Localização e drenagem

O script reúne os segmentos da camada `geoportal:segmento_logradouro` pelo código municipal da via (`codlog`). Intersecta os dois conjuntos de eixos viários em SIRGAS 2000 / UTM 23S (EPSG:31983, em metros). Em vias com pistas separadas, usa o centro geométrico dos encontros das linhas. São 1, 2, 2 e 3 pontos respectivamente para RS01 a RS04. No RS04, o encontro mais distante fica a 22 m do centro calculado. A latitude e a longitude do CSV estão em WGS84, em graus decimais. A posição indica uma referência para o relato. A extensão da lâmina de água e a pista atingida exigiriam verificação local.

O distrito é o polígono de `geoportal:distrito_municipal` que contém o ponto representativo. RS03 e RS04 ficam a aproximadamente 22 m e 18 m da divisa distrital, respectivamente. O campo `distancia_corrego_m` mede a menor distância em linha reta entre o ponto e um eixo da camada `geoportal:drenagem` com `cd_tipo_acidente = COR` (córrego). Rios, galerias e demais classes têm categorias próprias nessa base. A consulta abrange o retângulo dos quatro pontos mais uma margem de 2 km. Todos os córregos encontrados ficaram a menos de 353 m. [Metadados dos distritos](https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/51f75eab-6d90-451e-9f80-c21c1ac72630)

Usar a cartografia disponível em 2026 na avaliação de 2022–2025 pressupõe que esses cruzamentos e córregos já ocupavam posições semelhantes no período. Mudanças viárias e de drenagem entre as datas são uma limitação. O campo `distancia_a701_km` mede a distância geodésica do cruzamento à estação Mirante de Santana, usando as coordenadas de 2025. [Estação de chuva](../chuva/README.md)

## Altitude e declividade

A missão SRTM da NASA adquiriu as observações por radar em fevereiro de 2000. Usamos a folha **S24W047** do modelo SRTM GL1 com amostras a cada segundo de arco (cerca de 30 m), coordenadas WGS84 e altitudes em metros em relação ao geoide EGM96. O valor de `elevacao_m` vem da amostra mais próxima, respeitando a posição do centro da célula indicada pelo GeoTIFF. A declividade é o módulo do gradiente de Horn em uma janela de 3 × 3 células, multiplicado por 100 e expresso em porcentagem. O script calcula os espaçamentos horizontais em metros para a latitude da amostra. Uma inclinação de 5% representa cerca de 5 m de variação vertical por 100 m na direção de maior inclinação. Edificações, vegetação, obras posteriores a 2000 e a presença de viadutos limitam a interpretação em escala de rua. [NASA SRTM GL1, versão 3](https://doi.org/10.5067/MEaSUREs/SRTM/SRTMGL1.003) · [Distribuição OpenTopography](https://doi.org/10.5069/G9445JDF) · [Baixar a folha usada](https://opentopography.s3.sdsc.edu/raster/SRTM_GL1/SRTM_GL1_srtm/S24W047.tif)

## Reprodução

O notebook lê o CSV pronto. Para refazer o cruzamento geográfico separadamente, use o extrator na raiz do repositório. O comando armazena as respostas do WFS e a folha SRTM em cache fora do projeto. A execução foi conferida com Python 3.14, Pillow 12.2.0, pyproj 3.8.0 e Shapely 2.2.0. Para consultar a versão corrente das camadas, indique uma nova pasta em `--cache`.

```powershell
py -3 -m pip install Pillow==12.2.0 pyproj==3.8.0 shapely==2.2.0
$cacheGeo = Join-Path $env:TEMP 'rota-seca-geografia'
$conferenciaGeo = Join-Path $env:TEMP 'rota-seca-atributos.csv'
py -3 .\ml\dados\geografia\extrair_geografia.py --cache $cacheGeo --saida $conferenciaGeo
Get-FileHash -Algorithm SHA256 $conferenciaGeo
```

Uma segunda execução com um cache vazio consultou novamente as três camadas e o relevo, e reproduziu todos os valores. O SHA-256 do CSV usado no estudo é `0724de93cde1d3cf750556dabb98bf5033c4c062c3a8aec491912d1529ac9c67` e o da folha de elevação é `aac2c1d4fc4bd8e1c6d7a94b5bb1ae8487127769949a012de9fd30356abbe000`. O GeoSampa atualiza as camadas periodicamente. Preserve o CSV desta edição ao comparar um novo levantamento com os resultados do estudo.
