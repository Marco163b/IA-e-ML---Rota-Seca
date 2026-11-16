# Chuva reportada no aeroporto de Congonhas

`sbsp.csv` contém uma linha por hora local de São Paulo. A variável descreve o tempo observado em Congonhas, separado dos cruzamentos RS01, RS02, RS03 e RS04 por aproximadamente 5,58 km, 7,25 km, 3,69 km e 3,27 km, respectivamente. Chuvas localizadas podem atingir apenas uma dessas posições. A fonte de observação é a estação aeronáutica SBSP e o arquivo histórico é do Iowa Environmental Mesonet (IEM). [Cadastro do aeródromo no DECEA](https://aisweb.decea.mil.br/index.cfm?codigo=SBSP&i=aerodromos) · [Arquivo METAR do IEM](https://mesonet.agron.iastate.edu/request/download.phtml?network=BR__ASOS)

## Como interpretar o CSV

| Campo | Definição |
|---|---|
| `hora_local` | Hora de emissão da estimativa, de 01/01/2023 00h a 30/09/2026 23h, em `America/Sao_Paulo`. |
| `chuva_observada` | 1 quando o METAR selecionado reporta chuva (RA) ou garoa (DZ) no aeroporto. 0 quando um informe interpretável não traz essas condições no aeroporto. Campo vazio quando a observação é indeterminada ou falta um informe no intervalo. |

A cada hora, o extrator seleciona o último METAR regular (tipo 3 da consulta IEM) observado entre 15 e 90 minutos antes da emissão, inclusive. Por exemplo, um informe das 14h é elegível para a emissão das 15h. A margem de 15 minutos considera a demora na divulgação. Como o arquivo fornece a hora de observação e não informa quando cada mensagem chegou ao usuário, atrasos reais maiores continuam possíveis. Um código desconhecido no informe mais recente deixa o indicador ausente. O extrator não o substitui por um informe anterior.

O extrator interpreta o texto original em UTC e converte os horários para São Paulo. Códigos como `-RA`, `TSRA` e `SHRA` indicam chuva presente. `VCSH` indica pancadas nas imediações e `RERA` descreve chuva recente. Esses códigos isolados não ativam o indicador. O cálculo ignora tendências após `TEMPO`, `BECMG` e `NOSIG`, assim como observações suplementares após `RMK`. CAVOK, NSW ou um informe com visibilidade, pressão e sem registro de chuva ou garoa permitem classificar o valor como zero. Informes ausentes, truncados sem informação suficiente, corrigidos (`COR` sem versão anterior confirmada) e códigos de tempo indeterminado (`//`, `UP`) resultam em campo vazio. [Guia de leitura do METAR do Met Office](https://docs.mavis.metoffice.gov.uk/guidance/metar-decode/)

## Cobertura

| Período | Horas | Com observação interpretável | Com chuva ou garoa | Sem valor |
|---|---:|---:|---:|---:|
| 2023 | 8.760 | 8.657 | 540 | 103 |
| 2024 | 8.784 | 8.681 | 589 | 103 |
| 2025 | 8.760 | 8.592 | 423 | 168 |
| jan–set/2026 | 6.552 | 6.352 | 513 | 200 |
| Total | 32.856 | 32.282 | 2.065 | 574 |

O indicador está disponível em 98,25% das horas. As contagens medem o tempo observado no aeroporto. O início de alagamento de cada cruzamento vem de uma fonte independente, o CGE.

## Reprodução

Na raiz do repositório, com as dependências de ML instaladas, execute `python ml/dados/chuva_local/extrair_sbsp.py`. O script consulta a rede `BR__ASOS` no IEM. A consulta inclui o dia anterior ao início para recuperar informes elegíveis nas primeiras emissões. Para reproduzir a partir de uma cópia do CSV bruto com os campos `station`, `valid` e `metar`, acrescente `--bruto CAMINHO`. Use `--saida CAMINHO` para gravar outra cópia do resultado.

SHA-256 do CSV bruto usado nesta versão: `a74ea0b8409e9a5a65ed6965fcec4b9202422ddcd16ad1653b37b67c251f005b`. SHA-256 de `sbsp.csv`: `9724f4aa4bc2fcfc3e1061058e9cc97cec87aa1e3a56757f6e3a937a7e602002`.
