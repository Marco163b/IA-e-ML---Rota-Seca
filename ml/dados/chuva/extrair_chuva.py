"""Reconstrói a chuva horária da estação A701 a partir dos ZIPs oficiais do INMET."""

import argparse
import csv
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from io import TextIOWrapper
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile


FUSO_SP = timezone(timedelta(hours=-3))
INICIO = datetime(2022, 1, 1, tzinfo=FUSO_SP)
FIM = datetime(2026, 1, 1, tzinfo=FUSO_SP)
UMA_HORA = timedelta(hours=1)
CAMPO_CHUVA = "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)"


def ler_estacao(pacote, inicio=INICIO, fim=FIM):
    with ZipFile(pacote) as arquivo:
        membros = [nome for nome in arquivo.namelist()
                   if "_A701_" in nome.upper() and nome.lower().endswith(".csv")]
        if len(membros) != 1:
            raise ValueError(f"{pacote}: esperado um CSV da estação A701, encontrados {len(membros)}")
        with arquivo.open(membros[0]) as bruto, TextIOWrapper(bruto, encoding="latin-1", newline="") as texto:
            for _ in range(8):
                next(texto)
            linhas = csv.DictReader(texto, delimiter=";")
            if not {"Data", "Hora UTC", CAMPO_CHUVA}.issubset(linhas.fieldnames or []):
                raise ValueError(f"Cabeçalho inesperado em {membros[0]}")
            for linha in linhas:
                data_hora = f"{linha['Data']} {linha['Hora UTC']}"
                utc = datetime.strptime(data_hora, "%Y/%m/%d %H%M UTC").replace(tzinfo=UTC)
                if utc.minute:
                    raise ValueError(f"Leitura fora da hora cheia em {data_hora}")
                local = utc.astimezone(FUSO_SP)
                if inicio <= local < fim:
                    texto_chuva = linha[CAMPO_CHUVA].strip().replace(",", ".")
                    valor = Decimal(texto_chuva) if texto_chuva else None
                    if valor is not None and not valor.is_finite():
                        raise ValueError(f"Valor inesperado em {data_hora}")
                    yield local, (valor if valor is not None and valor >= 0 else None)


def reconstruir(pasta_zips, saida, inicio=INICIO, fim=FIM):
    if fim <= inicio:
        raise ValueError("O fim exclusivo deve vir depois do início.")
    registros = {}
    anos = range(inicio.astimezone(UTC).year, (fim - UMA_HORA).astimezone(UTC).year + 1)
    for ano in anos:
        for hora, chuva in ler_estacao(pasta_zips / f"{ano}.zip", inicio, fim):
            if hora in registros:
                raise ValueError(f"Hora duplicada no INMET: {hora}")
            registros[hora] = chuva

    saida.parent.mkdir(exist_ok=True, parents=True)
    with NamedTemporaryFile("w", dir=saida.parent, suffix=".tmp", delete=False,
                            encoding="utf-8", newline="") as arq:
        temporario = Path(arq.name)
    try:
        with temporario.open("w", encoding="utf-8", newline="") as arq:
            tabela = csv.writer(arq, lineterminator="\n")
            tabela.writerow(["hora_local", "chuva_mm"])
            hora = inicio
            while hora < fim:
                valor = registros.get(hora)
                tabela.writerow([hora.strftime("%Y-%m-%d %H:%M:%S"), format(valor, "f") if valor is not None else ""])
                hora += UMA_HORA
        temporario.replace(saida)
    finally:
        temporario.unlink(missing_ok=True)


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--zips", type=Path, required=True, help="Pasta com os ZIPs anuais do INMET")
    argumentos.add_argument("--saida", type=Path, required=True)
    argumentos.add_argument("--inicio", type=date.fromisoformat, default=INICIO.date(),
                            help="Primeiro dia no fuso de São Paulo (inclusive)")
    argumentos.add_argument("--fim-exclusivo", type=date.fromisoformat, default=FIM.date(),
                            help="Primeiro dia após o período desejado no fuso de São Paulo")
    opcoes = argumentos.parse_args()
    reconstruir(opcoes.zips, opcoes.saida,
                datetime.combine(opcoes.inicio, time.min, FUSO_SP),
                datetime.combine(opcoes.fim_exclusivo, time.min, FUSO_SP))
