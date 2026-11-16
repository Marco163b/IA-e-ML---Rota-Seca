"""Reconstrói o indicador horário de chuva reportada no METAR de Congonhas."""
import argparse
import re
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd


PASTA = Path(__file__).resolve().parent
PARAMETROS = dict(station="SBSP", network="BR__ASOS", data=["metar", "wxcodes"],
                  year1=2022, month1=12, day1=31, year2=2026, month2=10, day2=2,
                  tz="Etc/UTC", format="onlycomma", latlon="yes", elev="yes",
                  missing="M", trace="T", direct="no", report_type="3")
URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?" + urlencode(PARAMETROS, doseq=True)
PRECIPITACAO = re.compile(r"[+-]?(?:MI|PR|BC|DR|BL|SH|TS|FZ)?(?:RA|DZ|SN|SG|IC|PL|GR|GS|UP){1,3}")


def chuva_presente(mensagem):
    # Descartar informações suplementares, tendências, mudanças e previsões.
    observacao = re.split(r"\s+(?:RMK|TEMPO|BECMG|NOSIG|PROB30|PROB40|FM\d{4,6})\b",
                          mensagem.strip().upper().rstrip("="), maxsplit=1)[0]
    grupos = observacao.split()
    if "SBSP" not in grupos or "NIL" in grupos or "COR" in grupos:
        return pd.NA
    if not any(re.fullmatch(r"\d{6}Z", grupo) for grupo in grupos):
        return pd.NA
    for grupo in grupos:
        if PRECIPITACAO.fullmatch(grupo) and ("RA" in grupo or "DZ" in grupo):
            return 1
    if "//" in grupos or any(PRECIPITACAO.fullmatch(g) and "UP" in g for g in grupos):
        return pd.NA
    if "CAVOK" in grupos or "NSW" in grupos:
        return 0
    # Exigir visibilidade e QNH para distinguir um informe utilizável de texto truncado.
    if any(re.fullmatch(r"\d{4}", g) for g in grupos) and any(re.fullmatch(r"Q\d{4}", g) for g in grupos):
        return 0
    return pd.NA


def reconstruir(origem):
    bruto = pd.read_csv(origem, dtype=str, keep_default_na=False)
    if bruto.empty or not bruto["station"].eq("SBSP").all():
        raise ValueError("O arquivo precisa conter os informes de Congonhas (SBSP).")
    observacoes = pd.DataFrame({
        "observada": pd.to_datetime(bruto["valid"], format="%Y-%m-%d %H:%M", utc=True)
                        .dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None),
        "chuva_observada": bruto["metar"].map(chuva_presente).astype("Int8"),
    }).sort_values("observada")
    if observacoes["observada"].duplicated().any():
        raise ValueError("O arquivo contém mais de um informe para o mesmo minuto.")
    horas = pd.DataFrame({"hora_local": pd.date_range("2023-01-01", "2026-10-01", inclusive="left", freq="h")})
    horas["corte"] = horas["hora_local"] - pd.Timedelta(minutes=15)
    # A tolerância é relativa ao corte. Assim, 15 a 90 min separam observação e emissão.
    dados = pd.merge_asof(horas, observacoes, left_on="corte", right_on="observada",
                          tolerance=pd.Timedelta(minutes=75), direction="backward")
    return dados[["hora_local", "chuva_observada"]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bruto", type=Path, help="CSV já obtido do IEM. Sem esta opção, consulta a fonte.")
    parser.add_argument("--saida", type=Path, default=PASTA / "sbsp.csv")
    argumentos = parser.parse_args()
    dados = reconstruir(argumentos.bruto or URL)
    dados.to_csv(argumentos.saida, index=False, date_format="%Y-%m-%d %H:%M:%S", lineterminator="\n")
