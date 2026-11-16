"""Reconstrói os exemplos de previsão horária a partir dos CSVs das fontes."""

import argparse
import gzip
from pathlib import Path

import pandas as pd


PASTA = Path(__file__).resolve().parent
INICIO_SELECAO = pd.Timestamp("2023-01-01")
INICIO_MODELO = pd.Timestamp("2023-07-01")
UMA_HORA = pd.Timedelta(hours=1)
ATRIBUTOS_GEOGRAFICOS = ["elevacao_m", "declividade_pct", "distancia_corrego_m"]


def carregar_eventos(pasta):
    cobertura = pd.read_csv(pasta / "cge/cobertura.csv", parse_dates=["data"]).set_index("data")
    if not cobertura.index.is_unique:
        raise ValueError("Cobertura com datas duplicadas.")
    calendario = pd.date_range(INICIO_SELECAO, cobertura.index.max(), freq="D")
    dias_validos = cobertura.completo.reindex(calendario).eq(1)
    # A primeira lacuna também interrompe o histórico acumulado usado como entrada.
    continuo = dias_validos.cummin()
    dias = calendario[continuo]
    if dias.empty or dias[-1] < INICIO_MODELO:
        raise ValueError("Cobertura diária contínua insuficiente.")
    eventos = pd.read_csv(pasta / "cge/eventos.csv", parse_dates=["inicio_local"])
    observados = eventos.loc[eventos.inicio_local.dt.normalize().isin(dias)].copy()
    return observados, dias


def atributos_de_chuva(pasta):
    chuva = pd.read_csv(pasta / "chuva/chuva_a701.csv", parse_dates=["hora_local"])
    serie = chuva.set_index("hora_local").chuva_mm.sort_index().asfreq("h")
    if (serie.dropna() < 0).any():
        raise ValueError("Precipitação negativa no arquivo de observações.")
    return pd.DataFrame({
        "chuva_1h_mm": serie,
        "chuva_3h_mm": serie.rolling(3, min_periods=3).sum().round(2),
        "chuva_24h_mm": serie.rolling(24, min_periods=24).sum().round(2),
    })


def preparar(pasta, inicio_modelo=INICIO_MODELO):
    eventos, dias = carregar_eventos(pasta)
    cadastro = pd.read_csv(pasta / "cge/trechos.csv")
    geografia = pd.read_csv(pasta / "geografia/atributos_trechos.csv")
    if set(geografia.trecho_id) != set(cadastro.trecho_id) or not geografia.trecho_id.is_unique:
        raise ValueError("Cadastro geográfico incompatível com o catálogo de trechos.")
    if not set(eventos.trecho_id).issubset(cadastro.trecho_id):
        raise ValueError("Registro do CGE com trecho desconhecido.")
    if geografia[ATRIBUTOS_GEOGRAFICOS].isna().any().any():
        raise ValueError("Atributo estático ausente.")

    # O último horizonte termina às 23h do último dia com boletim íntegro.
    fim = dias[-1] + pd.Timedelta(hours=22)
    horas = pd.date_range(inicio_modelo, fim, freq="h", name="hora_local")
    chaves = ["hora_local", "trecho_id"]
    grade = pd.MultiIndex.from_product([horas, sorted(cadastro.trecho_id)], names=chaves)

    # Evento às 14h00 pertence à previsão das 13h. Evento às 14h01 pertence à das 14h.
    eventos["hora_local"] = eventos.inicio_local.dt.ceil("h") - UMA_HORA
    positivos = eventos.groupby(chaves).size()
    painel = positivos.reindex(grade, fill_value=0).gt(0).astype("int8")
    painel = painel.rename("alagou_proxima_hora").reset_index()
    painel["dia_local"] = painel.hora_local.dt.normalize()

    eventos["dia_local"] = eventos.inicio_local.dt.normalize()
    historico = eventos.groupby(["dia_local", "trecho_id"]).size().unstack(fill_value=0)
    historico = historico.reindex(index=dias, columns=cadastro.trecho_id, fill_value=0)
    historico = historico.cumsum().shift(1, fill_value=0).rename_axis("dia_local")
    historico = historico.stack().rename("alagamentos_anteriores")
    painel = painel.join(historico, on=["dia_local", "trecho_id"], validate="many_to_one")
    painel = painel.join(atributos_de_chuva(pasta), on="hora_local", validate="many_to_one")
    painel = painel.merge(geografia[["trecho_id", *ATRIBUTOS_GEOGRAFICOS]], on="trecho_id",
                          validate="many_to_one", how="left")
    completos = painel.chuva_24h_mm.notna()
    perdidos = painel.loc[~completos, "alagou_proxima_hora"].sum()
    print(f"Emissões possíveis: {len(painel)}; sem janela de chuva: {(~completos).sum()}; "
          f"inícios positivos excluídos: {perdidos}.")
    return painel.loc[completos].drop(columns="dia_local").reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pasta", type=Path, default=PASTA)
    parser.add_argument("--saida", type=Path, default=PASTA / "painel_trecho_hora.csv.gz")
    args = parser.parse_args()
    painel = preparar(args.pasta)
    # mtime fixo e nome vazio no cabeçalho tornam o gzip reproduzível.
    with args.saida.open("wb") as arquivo:
        with gzip.GzipFile(filename="", mode="wb", fileobj=arquivo, mtime=0) as gz:
            painel.to_csv(gz, index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S")
    print(f"{len(painel)} linhas de {painel.hora_local.min()} a {painel.hora_local.max()}.")


if __name__ == "__main__":
    main()
