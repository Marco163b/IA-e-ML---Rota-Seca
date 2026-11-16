# Dados do Rota Seca

## Segunda rodada · chuva local e teste externo

Os mesmos quatro cruzamentos foram acompanhados até setembro de 2026. O desenvolvimento incorpora o primeiro semestre de 2023 e usa quatro validações semestrais em 2024 e 2025. O código reconstrói o desenvolvimento desde janeiro/2023 a partir das fontes e mantém 90.640 emissões com 60 janelas positivas na cobertura comum. A comparação usa a chuva de [Interlagos](chuva_interlagos/README.md), a precipitação do [Mirante](chuva/README.md) e testa o indicador de [chuva observada em Congonhas](chuva_local/README.md).

O novo [painel externo](avaliacao_2026/README.md) usa 273 dias de boletins. Das 26.204 emissões possíveis, 23.328 têm janela completa na A701. A exigência de cobertura da A771 elimina outras 96. A comparação final usa 23.232 emissões e nove dos dez inícios registrados. O décimo ocorreu no RS04 em 08/01/2026 às 17h05, em uma janela com medição incompleta em Interlagos. O indicador METAR ausente recebe marcação de ausência.

## Painel da primeira versão · 2023–2025

O [painel de modelagem](painel_trecho_hora.csv.gz) combina o início de alagamentos registrados pelo CGE, a chuva medida pelo INMET e a geografia de quatro cruzamentos de São Paulo. Cada linha representa uma previsão emitida em uma hora cheia para um cruzamento. O painel comprimido já acompanha o repositório.

## Fontes

| Fonte e uso | Evidência no repositório |
|---|---|
| CGE da Prefeitura de São Paulo. Os boletins diários informam os locais e horários dos registros de alagamento. O extrator confere a data e compara a quantidade de registros com os totais declarados no boletim. [Consulta pública por data](https://www.cgesp.org/v3/alagamentos.jsp) | [Critérios e reprodução](cge/README.md) · [Registros dos quatro cruzamentos](cge/eventos.csv) · [Cobertura de cada dia](cge/cobertura.csv) |
| INMET. A estação automática A701, Mirante de Santana, mede a precipitação acumulada na hora encerrada no horário indicado. Usamos a série horária local de 2022–2025. [Arquivos oficiais](https://portal.inmet.gov.br/dadoshistoricos) | [Série da estação, fuso, lacunas e hashes](chuva/README.md) |
| GeoSampa e NASA SRTMGL1 v3. Os eixos das vias localizam o cruzamento. A carta SRTM fornece a elevação e a declividade aproximada. A hidrografia municipal fornece a distância ao córrego mapeado mais próximo. [GeoSampa](https://novogeosampa.prefeitura.sp.gov.br/) · [NASA SRTM](https://doi.org/10.5067/MEaSUREs/SRTM/SRTMGL1.003) | [Método geográfico](geografia/README.md) · [Atributos e coordenadas](geografia/atributos_trechos.csv) |

## Como uma observação é formada

1. **Selecionar os locais antes do período de modelagem.** Usamos registros do primeiro semestre de 2023 com cruzamentos identificáveis e recorrentes. As linhas de modelagem começam em julho de 2023. O nome e a referência oficial de cada local estão no [cadastro dos trechos](cge/trechos.csv).
2. **Definir o horizonte.** Uma emissão às 14h tenta antecipar um início de registro entre 14h01 e 15h00, pois os horários do CGE têm precisão de minuto. Um registro exatamente às 14h00 pertence à emissão das 13h. Múltiplos inícios no mesmo local e janela contam como um único positivo. Apenas o início gera o rótulo, mesmo quando a ocorrência dura várias horas.
3. **Construir os negativos.** Consideramos apenas dias com boletim verificado. Zero significa que o CGE não registrou um início para aquele cruzamento na janela. Um cruzamento pode continuar alagado por uma ocorrência anterior ou ter água que ninguém registrou. O fim da série exclui a última emissão das 23h porque sua janela termina no dia seguinte.
4. **Calcular os atributos disponíveis.** Os acumulados incluem apenas chuva medida até a hora de emissão. Exigimos 24 leituras consecutivas. Falta de leitura impede a emissão no estudo. O histórico conta os registros do cruzamento até o fim do dia anterior, inclusive no semestre de seleção. O histórico é atualizado ao longo do teste, como aconteceria após a publicação dos boletins.
5. **Congelar o teste.** As divisões usam a data de emissão em São Paulo. Todos os cruzamentos da mesma hora ficam na mesma divisão. Nas fronteiras de treino, validação e teste, o notebook também verifica quando termina o horizonte de cada exemplo.

## Quantas observações entraram

Os **1.096 boletins consecutivos** entre 01/01/2023 e 31/12/2025 somaram 2.159 registros na cidade, 64 nos quatro cruzamentos. Destes, 27 ocorreram no semestre de seleção dos locais. O painel seguinte cobria 87.836 combinações possíveis de cruzamento e hora de emissão. Descartamos 9.340 por falta de uma janela completa de 24 h de chuva, incluindo quatro janelas positivas.

| Intervalo do painel | Cruzamento-hora com chuva | Janelas com início registrado |
|---|---:|---:|
| Julho a dezembro de 2023 | 12.576 | 10 |
| Janeiro a dezembro de 2024 | 33.952 | 13 |
| Janeiro a dezembro de 2025 | 31.968 | 10 |
| **Total** | **78.496** | **33** |

No teste de 2025, o CGE registrou 11 inícios nos quatro locais. Uma dessas janelas perdeu a cobertura necessária de chuva. Na separação do painel, o notebook retira outras oito linhas sem evento nas fronteiras de ajuste, calibração e teste para impedir que uma janela de previsão alcance o início do conjunto seguinte. A divisão final está no [quadro de períodos](../resultados/periodos.csv).

## Campos do painel

| Coluna | Significado |
|---|---|
| `hora_local`, `trecho_id` | Chave única da previsão. Data e hora de São Paulo (UTC−3 no período) e identificador de RS01 a RS04. |
| `alagou_proxima_hora` | Rótulo 0/1 de **início registrado** na hora seguinte. |
| `chuva_1h_mm`, `chuva_3h_mm`, `chuva_24h_mm` | Precipitação acumulada na estação em janelas encerradas na emissão, em milímetros. Para a janela de uma hora, o valor também corresponde à intensidade média em mm/h. |
| `alagamentos_anteriores` | Quantidade de registros anteriores no cruzamento, acumulada desde 01/01/2023 até a véspera da emissão. |
| `elevacao_m`, `declividade_pct`, `distancia_corrego_m` | Elevação no ponto representativo, inclinação aproximada do terreno e distância horizontal ao eixo do córrego mapeado mais próximo. |

## Limites de uso

O CGE observa a cidade de forma desigual. A chuva pode variar entre a estação e os quatro cruzamentos, que ficam de 12,47 a 21,86 km dela. Os atributos geográficos descrevem um ponto representativo de cada cruzamento. O modelo usa a cartografia consultada em 2026 e as medições históricas disponíveis na extração. A avaliação retrospectiva não mede atrasos reais de publicação, lâmina d’água, bloqueios em andamento ou segurança de travessia.

## Como reconstruir

Na raiz do repositório, com o ambiente de `ml/requirements.txt` instalado, execute:

```powershell
& .\.venv\Scripts\python.exe ml/dados/preparar_painel.py --saida painel_conferencia.csv.gz
Get-FileHash ml/dados/painel_trecho_hora.csv.gz,painel_conferencia.csv.gz -Algorithm SHA256
```

O SHA-256 do painel desta edição é `7ad9c72292f4a76ef3aa8eb2cc915277ab3a9cb21ca80ba3d3379bbeecf81b71`. As entradas são os CSVs de [eventos](cge/eventos.csv), [cobertura](cge/cobertura.csv), [chuva](chuva/chuva_a701.csv), [geografia](geografia/atributos_trechos.csv) e [cadastro dos trechos](cge/trechos.csv). Cada subpasta documenta a reconstrução a partir da fonte pública. A manutenção das bases oficiais pode alterar um download futuro.
