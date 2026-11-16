"""Emite a previsão experimental da versão com observações locais de chuva."""

import argparse
from datetime import timedelta
import json
import math
from pathlib import Path

import joblib
import pandas as pd

from prever import COLUNAS_CHUVA, hora_paulo


PASTA = Path(__file__).resolve().parent
INTERLAGOS = ["interlagos_1h_mm", "interlagos_3h_mm", "interlagos_24h_mm"]
TERRENO = ["elevacao_m", "declividade_pct", "distancia_corrego_m"]


def validar_chuva(valores, origem):
    if any(type(x) not in (float, int) or not math.isfinite(x) for x in valores):
        raise ValueError(f"Informe três acumulados numéricos e finitos para {origem}.")
    if not 0 <= valores[0] <= valores[1] <= valores[2]:
        raise ValueError(f"Os acumulados de {origem} devem respeitar 0 ≤ 1h ≤ 3h ≤ 24h.")


def ler_entrada(arquivo, trecho, hora, pasta_dados):
    from estudo_local import montar_atributos

    dados = json.loads(arquivo.read_text(encoding="utf-8-sig"))
    aceitos = {"alagamentos_anteriores", "chuva_observada", *COLUNAS_CHUVA, *INTERLAGOS}
    if not isinstance(dados, dict) or set(dados) - aceitos:
        raise ValueError("Use um objeto JSON com as medições, chuva_observada e alagamentos_anteriores.")
    geo = pd.read_csv(pasta_dados / "geografia/atributos_trechos.csv").set_index("trecho_id")
    if trecho not in geo.index:
        raise ValueError("Trecho desconhecido no cadastro geográfico.")
    validar_chuva([dados.get(c) for c in COLUNAS_CHUVA], "A701")
    acumulados = [dados.get(c) for c in INTERLAGOS]
    validar_chuva(acumulados, "A771")
    historico = dados.get("alagamentos_anteriores")
    if type(historico) is not int or historico < 0:
        raise ValueError("Informe um histórico inteiro não negativo, acumulado até a véspera.")
    metar = dados.get("chuva_observada")
    if metar is not None and (type(metar) not in (float, int) or metar not in (0, 1)):
        raise ValueError("Use 0, 1 ou null para chuva_observada em Congonhas.")
    linha = {**dados, **geo.loc[trecho, TERRENO].to_dict(),
             "chuva_observada": float(metar) if metar is not None else float("nan"),
             "trecho_id": trecho, "hora_local": pd.Timestamp(hora.replace(tzinfo=None))}
    return montar_atributos(pd.DataFrame([linha]))


def ler_painel(trecho, hora, pasta_dados):
    from estudo_local import juntar_fontes

    arquivo = pasta_dados / "avaliacao_2026/painel_trecho_hora.csv.gz"
    colunas = ["hora_local", "trecho_id", "alagamentos_anteriores", *COLUNAS_CHUVA, *TERRENO]
    painel = pd.read_csv(arquivo, usecols=colunas, parse_dates=["hora_local"])
    instante = pd.Timestamp(hora.replace(tzinfo=None))
    linha = painel.loc[painel.hora_local.eq(instante) & painel.trecho_id.eq(trecho)]
    if len(linha) != 1:
        raise ValueError("Combinação de trecho e hora ausente ou ambígua no painel. Confira os dados ou use --entrada.")
    preparada = juntar_fontes(linha, pasta_dados)
    if len(preparada) != 1:
        raise ValueError("A hora solicitada tem cobertura de chuva insuficiente para a previsão.")
    return preparada


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Entradas JSON: chuva_1h_mm, chuva_3h_mm, chuva_24h_mm (A701), interlagos_1h_mm, "
        "interlagos_3h_mm, interlagos_24h_mm (A771), alagamentos_anteriores e, "
        "opcionalmente, chuva_observada (METAR de Congonhas, 0/1 ou null)."
    ))
    parser.add_argument("--trecho", required=True, choices=["RS01", "RS02", "RS03", "RS04"])
    parser.add_argument("--hora", required=True, type=hora_paulo, help="Hora cheia local de emissão em São Paulo")
    parser.add_argument("--entrada", type=Path, help="Arquivo JSON de medições da emissão. Sem ele, usar o painel de 2026.")
    args = parser.parse_args()
    from estudo_local import pontuar

    try:
        pacote = joblib.load(PASTA / "resultados/otimizacao/modelos.joblib")["local"]
        if args.entrada is None:
            painel = ler_painel(args.trecho, args.hora, PASTA / "dados")
            origem = "painel_historico"
        else:
            painel = ler_entrada(args.entrada, args.trecho, args.hora, PASTA / "dados")
            origem = "medicoes_informadas"
        prob = float(pontuar(pacote, painel)[0])
        if not 0 <= prob <= 1:
            raise ValueError("A pontuação do modelo ficou fora da faixa de probabilidade.")
    except (ValueError, OSError) as erro:
        parser.error(str(erro))
    limiar = float(pacote["limiar"])
    print(json.dumps({
        "trecho_id": args.trecho,
        "emitido_em": args.hora.isoformat(),
        "valido_ate": (args.hora + timedelta(hours=1)).isoformat(),
        "horizonte_min": 60,
        "probabilidade_registro_cge": prob,
        "limiar_estudo": limiar,
        "acima_limiar_estudo": prob >= limiar,
        "uso": "experimental",
        "versao": "chuva_local_2026",
        "configuracao": pacote["configuracao"],
        "fonte": origem,
    }, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
