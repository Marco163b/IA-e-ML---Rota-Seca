"""Calcula o escore experimental de registro do CGE para a próxima hora de um trecho."""

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

import joblib
import numpy as np
import pandas as pd


PASTA = Path(__file__).resolve().parent
FUSO_SP = timezone(timedelta(hours=-3))
COLUNAS_CHUVA = ["chuva_1h_mm", "chuva_3h_mm", "chuva_24h_mm"]


def adicionar_calendario(dados):
    resultado = dados.copy()
    horas = resultado["hora_local"].dt
    for campo, valores, ciclo in [("hora", horas.hour, 24), ("mes", horas.month - 1, 12)]:
        angulo = 2 * np.pi * valores / ciclo
        resultado[f"{campo}_sen"] = np.sin(angulo)
        resultado[f"{campo}_cos"] = np.cos(angulo)
    return resultado


def logit_escore(valores):
    valores = np.clip(np.asarray(valores, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(valores / (1 - valores)).reshape(-1, 1)


def hora_paulo(texto):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(-03:00)?", texto):
        raise argparse.ArgumentTypeError("Use AAAA-MM-DD HH:00, opcionalmente com -03:00.")
    try:
        hora = datetime.fromisoformat(texto)
    except ValueError as erro:
        raise argparse.ArgumentTypeError("Data ou hora inválida.") from erro
    if hora.minute or hora.second:
        raise argparse.ArgumentTypeError("A previsão requer uma hora cheia de São Paulo.")
    return hora.replace(tzinfo=FUSO_SP)


def entrada_modelo(trecho, hora, chuvas, historico):
    local = pd.Timestamp(hora.replace(tzinfo=None))
    geografia = pd.read_csv(PASTA / "dados/geografia/atributos_trechos.csv").set_index("trecho_id")
    if trecho not in geografia.index:
        raise ValueError("Trecho desconhecido. Escolha um de " + ", ".join(geografia.index) + ".")
    informados = [x is not None for x in [*chuvas, historico]]
    if not any(informados):
        painel = pd.read_csv(PASTA / "dados/painel_trecho_hora.csv.gz", parse_dates=["hora_local"])
        linha = painel.loc[painel.trecho_id.eq(trecho) & painel.hora_local.eq(local)]
        if len(linha) != 1:
            raise ValueError("Sem entrada no painel para esse trecho e hora. Informe os três acumulados e o histórico.")
        return adicionar_calendario(linha)
    if not all(informados):
        raise ValueError("Forneça --chuva-1h, --chuva-3h, --chuva-24h e --historico juntos.")
    mm_1h, mm_3h, mm_24h = chuvas
    if not np.isfinite(chuvas).all() or not 0 <= mm_1h <= mm_3h <= mm_24h:
        raise ValueError("As chuvas devem ser finitas, não negativas e respeitar 1h ≤ 3h ≤ 24h.")
    if historico < 0:
        raise ValueError("O número de registros anteriores precisa ser inteiro não negativo.")
    linha = geografia.loc[[trecho]].copy()
    linha["hora_local"] = local
    linha["alagamentos_anteriores"] = historico
    for coluna, mm in zip(COLUNAS_CHUVA, chuvas):
        linha[coluna] = mm
    return adicionar_calendario(linha)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trecho", required=True, help="Identificador do cadastro, por exemplo RS01")
    parser.add_argument("--hora", type=hora_paulo, required=True, help="Hora cheia de emissão em São Paulo")
    for horas in (1, 3, 24):
        parser.add_argument(f"--chuva-{horas}h", type=float,
                            help=f"Precipitação medida em mm nas {horas} h encerradas na emissão")
    parser.add_argument("--historico", type=int,
                        help="Contagem de inícios do CGE no trecho desde 01/01/2023 até o fim do dia anterior")
    args = parser.parse_args()
    try:
        linha = entrada_modelo(args.trecho, args.hora, [args.chuva_1h, args.chuva_3h, args.chuva_24h], args.historico)
    except ValueError as erro:
        parser.error(str(erro))
    arquivo = PASTA / "resultados/modelo_rf.joblib"
    if not arquivo.is_file():
        parser.error("Execute o notebook até o fim para gerar resultados/modelo_rf.joblib.")
    pacote = joblib.load(arquivo)
    bruto = pacote["modelo"].predict_proba(linha[pacote["atributos"]])[:, 1]
    prob = float(pacote["calibrador"].predict_proba(logit_escore(bruto))[0, 1])
    print(json.dumps({
        "trecho_id": args.trecho,
        "emitido_em": args.hora.isoformat(),
        "valido_ate": (args.hora + timedelta(hours=1)).isoformat(),
        "horizonte_min": 60,
        "probabilidade_registro_cge": prob,
        "acima_limiar_estudo": prob >= float(pacote["limiar"]),
        "uso": "experimental",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
