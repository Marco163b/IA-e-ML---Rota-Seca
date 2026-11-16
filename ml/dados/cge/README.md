# Boletins de alagamento do CGE-SP

O Centro de Gerenciamento de Emergências Climáticas da Prefeitura de São Paulo (CGE) publica um boletim por data com início, fim, via, sentido e ponto de referência. Os agentes municipais de trânsito concentram a observação nos corredores principais e no centro expandido. O estudo usa a hora de início de um registro, tanto transitável quanto intransitável. Uma hora sem início registrado também pode corresponder a um alagamento em andamento ou a uma ocorrência que escapou ao monitoramento. [CGE e critérios de classificação](https://cge.prefeitura.sp.gov.br/v3/alagamentos-classificacao.jsp) · [Exemplo de boletim com registros em RS02 e RS03](https://www.cgesp.org/v3/alagamentos.jsp?dataBusca=16%2F01%2F2025)

## Cobertura e rótulo

Na consulta de 09/11/2026, conferimos **1.096 boletins diários consecutivos**, de 01/01/2023 a 31/12/2025. Eles contêm **2.159 registros na cidade** (822 em 2023, 705 em 2024 e 632 em 2025). Em 863 dias, o próprio CGE informou zero registros. A data exibida em cada página coincide com a solicitada, os quatro totais do resumo (ativos/inativos, transitáveis/intransitáveis) foram lidos e sua soma corresponde à quantidade de pontos extraídos. O registro conserva a data do boletim e o horário local civil de São Paulo (UTC−3 neste período). A hora do fim pode cair na madrugada seguinte.

O alvo é a presença de pelo menos **um início de registro** no cruzamento na hora que se deseja prever. A área administrativa informada pelo CGE varia em alguns boletins. Usamos o par de vias para identificar o local e guardamos separadamente a área originalmente publicada.

## Quatro cruzamentos

Escolhemos quatro referências recorrentes do eixo sul da cidade a partir dos boletins de **janeiro a junho de 2023**. A escolha considerou ligações pelas avenidas das Nações Unidas, Roque Petroni Júnior e Santo Amaro, com nomes das duas vias que permitem localizar o cruzamento. O semestre de seleção antecede as janelas de avaliação. A regra ignora caixa, acentuação, pontuação e abreviações de via listadas no script. Aceita as vias em qualquer ordem e ambos os sentidos. Outros pontos da mesma avenida exigem referências próprias.

| ID | Par de vias que identifica o local | Dias com registro na seleção |
|---|---|---:|
| RS01 | Av. das Nações Unidas × R. Olívia Feder | 8 |
| RS02 | Av. das Nações Unidas × R. Jaime de Oliveira Souza | 7 |
| RS03 | Av. Roque Petroni Júnior × R. Cancioneiro Popular | 5 |
| RS04 | Av. Santo Amaro × Av. Roque Petroni Júnior | 7 |

Em todo o recorte, as quatro referências coincidem com 64 registros em 64 combinações distintas de trecho e hora. Foram 27 no semestre de seleção, 26 de julho de 2023 a dezembro de 2024 e 11 em 2025, antes de cruzar com os dados meteorológicos. A seleção favorece locais já conhecidos e os poucos casos reservados para teste tornam o desempenho sensível a cada acerto ou omissão.

## Arquivos e reprodução

- [Lista de cruzamentos](trechos.csv) contém o identificador estável e os nomes de exibição das vias.
- [Registros selecionados](eventos.csv) conserva o identificador, o início local, a hora de término e os campos do CGE (área, via, referência, sentido e situação).
- [Cobertura diária](cobertura.csv) informa a data, a validação do boletim, o total da cidade e o SHA-256 da lista de registros extraída naquele dia. O digest é calculado sobre os campos que interessam ao estudo e independe de propagandas ou outros elementos da página.
- [Extrator](extrair_cge.py) reconstrói esses arquivos a partir das páginas oficiais. Para verificar um dia, substitua a data na consulta ao boletim.

Na raiz do repositório, com Python e as dependências instaladas, a reconstrução completa pode ser feita em uma pasta temporária. A leitura em série respeita um intervalo mínimo de um segundo entre consultas. As páginas já presentes no cache são reutilizadas. Um erro de acesso ou de interpretação interrompe o processo antes da gravação dos CSVs.

```powershell
$cacheCge = Join-Path $env:TEMP 'rota-seca-boletins-cge'
$saidaCge = Join-Path $env:TEMP 'rota-seca-saida-cge'
python ml/dados/cge/extrair_cge.py --cache "$cacheCge" --baixar --saida "$saidaCge"
```

Uma segunda extração, com leitura independente das 1.096 páginas públicas, confirmou os totais diários, os boletins vazios e as 64 combinações de cruzamento e horário de início. Uma revisão futura dos registros pelo CGE pode alterar o resultado da reconstrução. Os CSVs versionados conservam a edição usada para treinar e avaliar o modelo.
