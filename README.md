# Rota Seca | Inteligência Artificial & Machine Learning

[Assistir à apresentação do projeto no YouTube](https://youtu.be/I9Z06vReKtE)

## Pergunta do estudo

Com os dados de chuva disponíveis às 17h, é possível antecipar se o CGE registrará o início de um alagamento em um cruzamento de São Paulo entre as 17h e as 18h? O estudo acompanha quatro cruzamentos e compara as previsões com os boletins do CGE. Para quem passa por esses locais, importa tanto receber um aviso a tempo quanto saber com que frequência ele se confirma.

## Integrantes

| Nome | RM |
|---|---|
| Guilherme Barbiero | RM555185 |
| Marco Antonio Gonçalves | RM556818 |
| Vinicius Castro | RM556137 |
| Camila Mie Takara | RM555418 |
| Matheus Cantiere | RM558479 |

## Arquivos da entrega

- O [notebook executado](ml/rota_seca_ml.ipynb) apresenta o estudo inicial (seções 1–6) e a otimização com teste externo em 2026 (seções 7–9).
- O [relatório de IA e ML](ml/RELATORIO_ML.md) reúne método, resultados e implicações para a decisão de emitir alertas.
- A [documentação dos dados](ml/dados/README.md) descreve a origem das observações, as perdas de cobertura e a reconstrução do painel. As [tabelas e figuras](ml/resultados/) permitem conferir os resultados.

## Resultado principal · teste externo de 2026

O estudo compara os quatro cruzamentos em **23.232 emissões** entre janeiro e setembro de 2026. Havia dez inícios registrados pelo CGE. Nove ficaram em horas com todas as medições exigidas. No RS02, a estação de Interlagos está a 5,03 km do cruzamento, enquanto a de Mirante está a 21,86 km. A configuração escolhida no desenvolvimento combinou a chuva da estação mais próxima e o máximo entre as duas estações.

| Regra congelada antes do teste | Avisos | Inícios antecipados | Avisos sem confirmação | Precisão média (AP) |
|---|---:|---:|---:|---:|
| Floresta original · limiar 1,083% | 6 | 0 de 9 | 6 | 0,0075 |
| Floresta com chuva local · limiar 3,111% | 40 | 0 de 9 | 40 | 0,0181 |

A chuva local melhorou a ordenação dos casos. Com o limiar definido antes do teste, o modelo emitiu mais avisos e perdeu todos os inícios avaliáveis. O uso indicado para o piloto é a demonstração histórica. Uma próxima mudança precisa de outro período para confirmação. [Métricas e controles](ml/resultados/otimizacao/metricas_2026.csv) · [Previsões individuais](ml/resultados/otimizacao/previsoes_2026.csv.gz)

## Primeira versão · teste de 2025

Nos quatro cruzamentos, houve dez inícios de alagamento registrados em horas com chuva disponível. A Random Forest emitiu **19 avisos**, antecipou **1 dos 10 registros** e deixou passar nove. A regressão logística emitiu 224 avisos e perdeu os dez registros. Os resultados são insuficientes para orientar um desvio automático ou indicar que uma travessia é segura. [Métricas de treino e teste](ml/resultados/metricas.csv)

## Reprodução no Windows

O [painel horário](ml/dados/painel_trecho_hora.csv.gz) está incluído. Na raiz do repositório, abra o PowerShell com Python 3.14 instalado e execute os comandos abaixo.

```powershell
py -3.14 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r ml/requirements.txt
& .\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 ml/rota_seca_ml.ipynb
```

A lista de pacotes e versões está em [dependências do notebook](ml/requirements.txt). A seção 7 refaz a seleção em uma pasta temporária. A seção 8 calcula as métricas de 2026 com os modelos e os limiares preservados antes do teste. Para explorar as células e suas saídas, abra o notebook no JupyterLab.

```powershell
& .\.venv\Scripts\python.exe -m jupyter lab ml/rota_seca_ml.ipynb
```

## Reproduzir a previsão do vídeo

Na raiz do repositório, use o modelo com as duas estações para consultar o RS02 (Av. das Nações Unidas × R. Jaime de Oliveira Souza) em 16/01/2026 às 17h.

```powershell
& .\.venv\Scripts\python.exe ml/prever_local.py --trecho RS02 --hora "2026-01-16 17:00"
```

Para a hora seguinte, o modelo estimou 0,52% de probabilidade de um novo registro do CGE. O valor ficou abaixo do limiar de 3,11% e o modelo não emitiu aviso. O CGE registrou o início às 17h47. [Registro observado](ml/dados/avaliacao_2026/eventos.csv)

O [registro de prompts](prompts.md) reúne perguntas de apoio feitas durante o estudo.
