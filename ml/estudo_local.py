"""Validação temporal da chuva de Interlagos e Congonhas para o Rota Seca."""
from hashlib import sha256
from itertools import product
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from dados.preparar_painel import preparar
from prever import adicionar_calendario, logit_escore


ML = Path(__file__).resolve().parent
DADOS = ML / "dados"
SAIDA = ML / "resultados/otimizacao"
ALVO = "alagou_proxima_hora"
HORAS = (1, 3, 24)
BASE = ["hora_sen", "hora_cos", "mes_sen", "mes_cos", "historico_mensal",
        "elevacao_m", "declividade_pct", "distancia_corrego_m"]
CONFIGURACOES = ["Mirante", "Mais próxima", "Duas estações", "Duas estações + Congonhas"]
CORTE = pd.Timestamp("2026-01-01")
HORA = pd.Timedelta(hours=1)


def montar_atributos(linhas):
    quadro = adicionar_calendario(linhas)
    dias = (quadro.hora_local.dt.normalize() - pd.Timestamp("2023-01-01")).dt.days
    quadro["historico_mensal"] = np.log1p(30 * quadro.alagamentos_anteriores / (30 + dias))
    for h in HORAS:
        norte = quadro[f"chuva_{h}h_mm"]
        sul = quadro[f"interlagos_{h}h_mm"]
        quadro[f"mirante_{h}"] = np.log1p(norte)
        quadro[f"local_{h}"] = np.log1p(norte.where(quadro.trecho_id.eq("RS01"), sul))
        quadro[f"regional_{h}"] = np.log1p(np.maximum(norte, sul))
    quadro["sbsp_ausente"] = quadro.chuva_observada.isna().astype(int)
    quadro["sbsp_chuva"] = quadro.chuva_observada.fillna(0)
    return quadro


def juntar_fontes(painel, pasta_dados=DADOS):
    serie = pd.read_csv(pasta_dados / "chuva_interlagos/chuva_a771.csv", parse_dates=["hora_local"])
    chuva = serie.set_index("hora_local").chuva_mm.sort_index().asfreq("h")
    acumulados = pd.DataFrame({f"interlagos_{h}h_mm": chuva.rolling(h, min_periods=h).sum().round(2)
                               for h in HORAS})
    metar = pd.read_csv(pasta_dados / "chuva_local/sbsp.csv", parse_dates=["hora_local"])
    dados = painel.join(acumulados, on="hora_local", validate="many_to_one")
    dados = dados.join(metar.set_index("hora_local"), on="hora_local", validate="many_to_one")
    return montar_atributos(dados.dropna(subset=["interlagos_24h_mm"]).reset_index(drop=True))


def colunas(configuracao):
    prefixo = "mirante" if configuracao == "Mirante" else "local"
    cols = BASE + [f"{prefixo}_{h}" for h in HORAS]
    if configuracao in CONFIGURACOES[2:]:
        cols += [f"regional_{h}" for h in HORAS]
    if configuracao == CONFIGURACOES[-1]:
        cols += ["sbsp_chuva", "sbsp_ausente"]
    return cols


def estimador(parametros):
    arvores, profundidade, folha = parametros
    if arvores == 0:
        return make_pipeline(StandardScaler(), LogisticRegression(C=0.1, class_weight="balanced",
                                                                  max_iter=1000, random_state=42))
    return RandomForestClassifier(n_estimators=arvores, max_depth=profundidade,
                                  min_samples_leaf=folha, class_weight="balanced",
                                  random_state=42, n_jobs=2)


def amostra_ajuste(dados):
    positivos = dados.loc[dados[ALVO].eq(1)]
    negativos = dados.loc[dados[ALVO].eq(0)]
    return pd.concat([positivos, negativos.sample(min(20000, len(negativos)), random_state=42)]).sort_index()


def blocos_temporais(dados):
    blocos = []
    for inicio in pd.date_range("2024-01-01", periods=4, freq="6MS"):
        fim = inicio + pd.DateOffset(months=6)
        antes = dados.hora_local + HORA < inicio
        durante = (dados.hora_local >= inicio) & (dados.hora_local + HORA < fim)
        tr, va = amostra_ajuste(dados.loc[antes]), dados.loc[durante]
        assert tr.hora_local.max() + HORA < va.hora_local.min()
        blocos.append((tr, va))
    return blocos


def escolher_limiar(y, probabilidades):
    # Agrupar empates garante que a taxa corresponda à comparação inclusiva da aplicação.
    tab = pd.DataFrame({"prob": probabilidades, "y": np.asarray(y)}).groupby("prob").y.agg(["sum", "size"])
    tab = tab.sort_index(ascending=False).cumsum()
    tab = tab.loc[tab["size"] <= len(y) * 25 / 10000]
    if tab.empty or tab["sum"].max() == 0:
        return float(np.nextafter(max(probabilidades), np.inf))
    return float((5 * tab["sum"] / (4 * np.sum(y) + tab["size"])).idxmax())


def pontuar(pacote, painel_preparado):
    bruto = pacote["modelo"].predict_proba(painel_preparado[pacote["atributos"]])[:, 1]
    return pacote["calibrador"].predict_proba(logit_escore(bruto))[:, 1]


def medir(nome, periodo, y, probs, limiar):
    tn, fp, fn, tp = confusion_matrix(y, probs >= limiar, labels=[0, 1]).ravel()
    return dict(modelo=nome, periodo=periodo, linhas=len(y), positivos=int(np.sum(y)), tp=tp,
                fp=fp, fn=fn, tn=tn, avisos=tp+fp, precisao=tp/max(1,tp+fp),
                recall=tp/max(1,tp+fn), f2=5*tp/max(1,5*tp+4*fn+fp),
                avisos_10mil=(tp+fp)*10000/len(y), ap=average_precision_score(y, probs),
                roc_auc=roc_auc_score(y, probs), brier=brier_score_loss(y, probs), limiar=limiar)


def dados_desenvolvimento():
    historico = preparar(DADOS, inicio_modelo=pd.Timestamp("2023-01-01"))
    dados = juntar_fontes(historico)
    assert dados.hora_local.max() + HORA < CORTE
    return dados


def treinar(diretorio):
    """Refaz a seleção em um diretório separado do pacote oficial de avaliação."""
    if diretorio.resolve() == SAIDA.resolve():
        raise ValueError("Escolha outra pasta para preservar os modelos congelados do estudo.")
    diretorio.mkdir(parents=True, exist_ok=True)
    dados = dados_desenvolvimento()
    blocos = blocos_temporais(dados)
    validacao = pd.concat([va for tr, va in blocos])
    y = validacao[ALVO].to_numpy()
    grade = [(0, 0, 0), *product([32, 64], [3, 5, 8], [8, 32])]
    previsoes, resultados = {}, []
    for config in CONFIGURACOES:
        cols = colunas(config)
        for params in grade:
            parciais, aps = [], []
            for tr, va in blocos:
                mod = estimador(params).fit(tr[cols], tr[ALVO])
                escore = mod.predict_proba(va[cols])[:, 1]
                parciais.append(escore)
                aps.append(average_precision_score(va[ALVO], escore))
            scores = np.concatenate(parciais)
            previsoes[(config, params)] = scores
            resultados.append(dict(configuracao=config, arvores=params[0], profundidade=params[1],
                                   folha=params[2], ap=average_precision_score(y, scores),
                                   **{f"ap_bloco_{i+1}": v for i,v in enumerate(aps)}))
    ranking = pd.DataFrame(resultados).sort_values("ap", ascending=False, kind="stable")
    ranking.to_csv(diretorio/"grade.csv", index=False)
    def chave(linha):
        return linha.configuracao, (int(linha.arvores), int(linha.profundidade), int(linha.folha))
    local = chave(ranking.loc[ranking.configuracao.ne("Mirante")].iloc[0])
    escolhas = {"local": local, "mirante": chave(ranking.loc[ranking.configuracao.eq("Mirante")].iloc[0]),
                "controle": ("Mirante", local[1])}
    modelos, metricas, especificacao = {}, [], {}
    ajuste = amostra_ajuste(dados)
    for nome, (config, params) in escolhas.items():
        cols = colunas(config)
        fora = previsoes[(config, params)]
        calibrador = LogisticRegression(max_iter=1000).fit(logit_escore(fora), y)
        probabilidades = calibrador.predict_proba(logit_escore(fora))[:, 1]
        limiar = escolher_limiar(y, probabilidades)
        modelo = estimador(params).fit(ajuste[cols], ajuste[ALVO])
        metodo = "Random Forest" if params[0] else "Regressão logística"
        modelos[nome] = dict(configuracao=config, metodo=metodo, atributos=cols, modelo=modelo,
                             calibrador=calibrador, limiar=limiar)
        especificacao[nome] = dict(configuracao=config, metodo=metodo, parametros=params, limiar=limiar)
        metricas.append(medir(nome, "Validação temporal", y, probabilidades, limiar))
        metricas.append(medir(nome, "Desenvolvimento (reajuste)", dados[ALVO], pontuar(modelos[nome], dados), limiar))
    arquivo = diretorio / "modelos.joblib"
    joblib.dump(modelos, arquivo, compress=3)
    especificacao.update(linhas_ajuste=len(dados), positivos_ajuste=int(dados[ALVO].sum()),
                         linhas_validacao=len(y), positivos_validacao=int(y.sum()),
                         sha256_pacote=sha256(arquivo.read_bytes()).hexdigest())
    (diretorio / "congelamento.json").write_text(json.dumps(especificacao, indent=2, ensure_ascii=False)+"\n",
                                                encoding="utf-8")
    pd.DataFrame(metricas).to_csv(diretorio/"metricas_desenvolvimento.csv", index=False)
    return ranking, especificacao


def ler_modelos_congelados(diretorio):
    arquivo = diretorio / "modelos.joblib"
    ficha = json.loads((diretorio / "congelamento.json").read_text(encoding="utf-8"))
    assert ficha["sha256_pacote"] == sha256(arquivo.read_bytes()).hexdigest()
    return joblib.load(arquivo)


def avaliar_amostra_treino(diretorio=SAIDA):
    """Pontua as mesmas linhas selecionadas para o ajuste final de cada floresta."""
    modelos = ler_modelos_congelados(diretorio)
    ajuste = amostra_ajuste(dados_desenvolvimento())
    metricas = [
        medir(nome, "Treino efetivo", ajuste[ALVO], pontuar(pacote, ajuste), pacote["limiar"])
        for nome, pacote in modelos.items()
    ]
    tabela = pd.DataFrame(metricas)
    tabela.to_csv(diretorio / "metricas_treino_efetivo.csv", index=False)
    return tabela


def avaliar(diretorio=SAIDA):
    # Este caminho só é usado depois do congelamento.
    modelos = ler_modelos_congelados(diretorio)
    modelos["original"] = joblib.load(ML / "resultados/modelo_rf.joblib")
    base = pd.read_csv(DADOS / "avaliacao_2026/painel_trecho_hora.csv.gz", parse_dates=["hora_local"])
    teste = juntar_fontes(base)
    assert teste.hora_local.min() >= CORTE and teste.hora_local.max() < pd.Timestamp("2026-10-01")
    assert not teste.duplicated(["hora_local","trecho_id"]).any()
    saidas = teste[["hora_local","trecho_id",ALVO]].copy()
    metricas = []
    for nome, pacote in modelos.items():
        p = pontuar(pacote, teste)
        saidas[f"prob_{nome}"] = p
        saidas[f"aviso_{nome}"] = (p >= pacote["limiar"]).astype(int)
        metricas.append(medir(nome, "Teste 2026", teste[ALVO], p, pacote["limiar"]))
    tab = pd.DataFrame(metricas)
    tab.to_csv(diretorio/"metricas_2026.csv", index=False)
    saidas.to_csv(diretorio/"previsoes_2026.csv.gz", index=False, compression={"method":"gzip","mtime":0})
    return tab


def grafico_comparacao(tabela, diretorio=SAIDA):
    import matplotlib.pyplot as plt
    ordem = ["original", "mirante", "controle", "local"]
    nomes = ["Floresta original", "Mirante reajustado", "Controle pareado", "Candidato local"]
    cores = ["#a7b4bc", "#668899", "#507b85", "#13715f"]
    m = tabela.set_index("modelo").loc[ordem]
    fig, eixos = plt.subplots(1, 2, figsize=(9, 2.6), sharey=True, layout="constrained")
    for ax, campo, titulo in zip(eixos, ["fp", "ap"], ["Avisos sem confirmação", "Precisão média (AP)"]):
        valores = m[campo]
        barras = ax.barh(nomes, valores, color=cores)
        ax.set_xlim(0, valores.max()*1.42)
        ax.set_title(titulo)
        rotulos = [str(int(v)) if campo == "fp" else f"{v:.4f}".replace(".", ",") for v in valores]
        ax.bar_label(barras, labels=rotulos, padding=3)
        ax.spines[["top", "right"]].set_visible(False)
    eixos[0].invert_yaxis()
    fig.savefig(diretorio/"comparacao_2026.png", dpi=165)
    plt.close(fig)
