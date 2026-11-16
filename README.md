# Rota Seca | Inteligência Artificial & Machine Learning

[Assistir à apresentação do projeto no YouTube](https://youtu.be/I9Z06vReKtE)

## Ficha da CitizenTech

| Campo | Projeto |
|---|---|
| Cidade e público | São Paulo (SP). O Rota Seca atende quem se desloca a pé, de bicicleta, moto, ônibus ou carro e precisa decidir quando sair e por onde passar durante a chuva. |
| Problema | Uma pessoa pode descobrir que o cruzamento alagou só quando chega lá, depois de perder a chance de mudar o caminho. |
| Funcionamento proposto | O aplicativo e o bot de WhatsApp avisam sobre locais salvos e apresentam desvios. O serviço de risco combina chuva, histórico, relevo e confirmações locais. |
| Entrega de IA e ML | Com a chuva observada até a hora de emissão, estimar a probabilidade de um novo registro de alagamento do CGE no cruzamento durante a hora seguinte. A análise usa quatro cruzamentos com histórico documentado no município. |
| Participantes e tecnologias | A equipe desenvolve o modelo em Python. O CGE, o INMET e o GeoSampa fornecem dados públicos. Na proposta do produto, o serviço da rua disponibiliza os resultados à API, aos alertas e ao roteador. |
| Impacto | No teste histórico, medir quantos registros o modelo anteciparia e quantos alertas coincidem com um registro. No piloto com usuários, medir que proporção recebeu o aviso a tempo de mudar o caminho. A expansão para novos trechos exige nova avaliação. |
| ODS | O projeto prioriza as metas 11.5 (reduzir o impacto de desastres relacionados à água) e 13.1 e 13.3 (adaptação e alerta precoce). A proposta do grupo também relaciona a exposição à água contaminada à meta 3.9, a infraestrutura resiliente à 9.1 e o acesso inclusivo aos avisos à 10.2. |

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
- O [relatório de IA e ML](ml/RELATORIO_ML.md) reúne método, resultados e implicações para a decisão de emitir alertas. A [versão em PDF](ml/RELATORIO_ML.pdf) tem duas páginas.
- A [documentação dos dados](ml/dados/README.md) descreve a origem das observações, as perdas de cobertura e a reconstrução do painel. As [tabelas e figuras](ml/resultados/) permitem conferir os resultados.

## Resultado principal · teste externo de 2026

O estudo compara os quatro cruzamentos em **23.232 emissões** entre janeiro e setembro de 2026. Havia dez inícios registrados pelo CGE. Nove ficaram em horas com todas as medições exigidas. No RS02, a estação de Interlagos está a 5,03 km do cruzamento, enquanto a de Mirante está a 21,86 km. A configuração escolhida no desenvolvimento combinou a chuva da estação mais próxima e o máximo entre as duas estações.

| Regra congelada antes do teste | Avisos | Inícios antecipados | Avisos sem confirmação | Precisão média (AP) |
|---|---:|---:|---:|---:|
| Floresta original · limiar 1,083% | 6 | 0 de 9 | 6 | 0,0075 |
| Floresta com chuva local · limiar 3,111% | 40 | 0 de 9 | 40 | 0,0181 |

A chuva local melhorou a ordenação dos casos. Com o limiar definido antes do teste, o modelo emitiu mais avisos e perdeu todos os inícios avaliáveis. O uso indicado para o piloto é a demonstração histórica. Uma próxima mudança precisa de outro período para confirmação. [Métricas e controles](ml/resultados/otimizacao/metricas_2026.csv) · [Previsões individuais](ml/resultados/otimizacao/previsoes_2026.csv.gz)

## Primeira versão · teste de 2025

Nos quatro cruzamentos, houve dez inícios de alagamento registrados em horas com chuva disponível. A Random Forest emitiu **19 avisos**, antecipou **1 dos 10 registros** e deixou passar nove. A regressão logística emitiu 224 avisos e perdeu os dez registros. Para a demonstração, o grupo pode mostrar o horário de emissão e a consulta ao CGE. Os resultados são insuficientes para orientar um desvio automático ou indicar que uma travessia é segura. [Métricas de treino e teste](ml/resultados/metricas.csv)

## Reprodução no Windows

O [painel horário](ml/dados/painel_trecho_hora.csv.gz) está incluído. Na raiz do repositório, abra o PowerShell com Python 3.14 instalado e execute os comandos abaixo.

```powershell
py -3.14 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r ml/requirements.txt
& .\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 ml/rota_seca_ml.ipynb
```

A seção 7 refaz a seleção em uma pasta temporária. A seção 8 calcula as métricas de 2026 com os modelos e os limiares preservados antes do teste. Para explorar as células e suas saídas, abra o notebook no JupyterLab.

```powershell
& .\.venv\Scripts\python.exe -m jupyter lab ml/rota_seca_ml.ipynb
```

## Como consultar os dois modelos

Para consultar a versão estudada em 2026, use uma emissão com cobertura nos dois pluviômetros. O comando devolve a probabilidade e o limiar específicos da versão local.

```powershell
& .\.venv\Scripts\python.exe ml/prever_local.py --trecho RS02 --hora "2026-02-01 12:00"
```

O exemplo abaixo reproduz a versão original em 2025, com o limiar usado na primeira demonstração.

Este comando usa as medições e o histórico que correspondem a uma emissão real do painel. Ele aplica a floresta e a calibração salvas durante o treino.

```powershell
& .\.venv\Scripts\python.exe ml/prever.py --trecho RS02 --hora "2025-01-16 18:00"
```

A resposta em JSON identifica o cruzamento, o horário de emissão, o fim da janela, a probabilidade de início de registro do CGE e a indicação de que o escore alcançou o limiar experimental. Para uma nova emissão, o serviço pode informar `--chuva-1h`, `--chuva-3h`, `--chuva-24h` e `--historico`. Os três valores de chuva devem ser medições acumuladas na A701 até a hora informada. O histórico é a contagem do CGE até o fim da véspera naquele cruzamento. A integração proposta usa uma estimativa por hora. Uma consulta a cada 15 minutos deve conservar o horário de emissão até haver uma nova estimativa. [Código de inferência](ml/prever.py)

**Exemplo para o Mobile.** Ao reproduzir a emissão histórica das 18h de 16/01/2025, a IA devolve a resposta abaixo. O campo de probabilidade vai de 0 a 1. A tela pode exibir **1,77%** e, para o aviso experimental, usar diretamente `acima_limiar_estudo`. A comparação usa o valor completo do limiar antes do arredondamento.

```json
{
  "trecho_id": "RS02",
  "emitido_em": "2025-01-16T18:00:00-03:00",
  "valido_ate": "2025-01-16T19:00:00-03:00",
  "horizonte_min": 60,
  "probabilidade_registro_cge": 0.01767396367683185,
  "acima_limiar_estudo": true,
  "uso": "experimental"
}
```

No RS02 (Av. das Nações Unidas × R. Jaime de Oliveira Souza), o CGE registrou o início às **18h48**. Na demonstração, esse registro entra na tela depois da previsão das 18h. O fluxo sugerido na proposta é o app consultar `GET /alertas` da API C#. A API usa o Serviço de Risco da Rua (SOA), que disponibiliza previsões por trecho em `GET /risco?bbox=...`. Os responsáveis por C# e SOA ainda precisam confirmar esse contrato. [Registro do CGE](ml/dados/cge/eventos.csv)

O [registro do uso de IA](prompts.md) descreve a assistência recebida.
