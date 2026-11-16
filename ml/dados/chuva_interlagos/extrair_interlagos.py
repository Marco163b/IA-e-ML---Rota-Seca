"""Extrai a precipitação horária observada na A771 dos arquivos históricos do INMET."""

import argparse
import csv
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from io import TextIOWrapper
from pathlib import Path
from zipfile import ZipFile


FUSO = timezone(timedelta(hours=-3))
INICIO = datetime(2022, 1, 1, tzinfo=FUSO)
FIM = datetime(2026, 10, 1, tzinfo=FUSO)
HORA = timedelta(hours=1)
CAMPO = "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)"


def ler_observacoes(pacote):
    with ZipFile(pacote) as anual:
        arquivos = [nome for nome in anual.namelist()
                    if "_A771_" in nome.upper() and nome.lower().endswith(".csv")]
        if len(arquivos) != 1:
            raise ValueError(f"Esperado um arquivo da A771 em {pacote}; encontrados {len(arquivos)}")
        with anual.open(arquivos[0]) as bruto, TextIOWrapper(bruto, encoding="latin-1", newline="") as texto:
            metadados = dict(next(texto).rstrip().split(";", 1) for _ in range(8))
            if metadados.get("CODIGO (WMO):") != "A771":
                raise ValueError(f"Estação divergente em {arquivos[0]}")
            linhas = csv.DictReader(texto, delimiter=";")
            if not {"Data", "Hora UTC", CAMPO}.issubset(linhas.fieldnames or []):
                raise ValueError(f"Colunas inesperadas em {arquivos[0]}")
            for linha in linhas:
                utc = datetime.strptime(f"{linha['Data']} {linha['Hora UTC']}", "%Y/%m/%d %H%M UTC")
                if utc.minute:
                    raise ValueError(f"Observação fora da hora cheia: {utc}")
                local = utc.replace(tzinfo=UTC).astimezone(FUSO)
                if INICIO <= local < FIM:
                    leitura = linha[CAMPO].strip().replace(",", ".")
                    valor = Decimal(leitura) if leitura else None
                    if valor is not None and not valor.is_finite():
                        raise ValueError(f"Leitura não finita em {utc}")
                    yield local, valor if valor is not None and valor >= 0 else None


def reconstruir(pasta, destino):
    observacoes = {}
    for ano in range(INICIO.year, FIM.year + 1):
        for hora, valor in ler_observacoes(pasta / f"{ano}.zip"):
            if hora in observacoes:
                raise ValueError(f"Hora duplicada: {hora}")
            observacoes[hora] = valor
    with destino.open("w", encoding="utf-8", newline="") as saida:
        tabela = csv.writer(saida, lineterminator="\n")
        tabela.writerow(["hora_local", "chuva_mm"])
        hora = INICIO
        while hora < FIM:
            valor = observacoes.get(hora)
            tabela.writerow([hora.strftime("%Y-%m-%d %H:%M:%S"), format(valor, "f") if valor is not None else ""])
            hora += HORA


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zips", type=Path, required=True, help="Pasta com 2022.zip a 2026.zip do INMET")
    parser.add_argument("--saida", type=Path, default=Path(__file__).with_name("chuva_a771.csv"))
    args = parser.parse_args()
    reconstruir(args.zips, args.saida)
