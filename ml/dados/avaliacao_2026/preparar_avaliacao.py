"""Reconstrói as linhas de 2026 mantendo as regras e o histórico anteriores."""

import argparse
import gzip
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

import pandas as pd


PASTA = Path(__file__).resolve().parent
DADOS = PASTA.parent
sys.path.insert(0, str(DADOS))
from preparar_painel import preparar


def unir_periodos(legado, extensao, destino):
    """Concatena dois CSVs consecutivos com o mesmo cabeçalho."""
    with legado.open(encoding="utf-8") as anterior, extensao.open(encoding="utf-8") as novo:
        titulo = anterior.readline()
        if titulo != novo.readline():
            raise ValueError(f"Cabeçalho divergente em {extensao}.")
        with destino.open("w", encoding="utf-8", newline="\n") as saida:
            saida.write(titulo)
            shutil.copyfileobj(anterior, saida)
            shutil.copyfileobj(novo, saida)


def gerar(fontes, saida):
    calendario = pd.date_range("2026-01-01", "2026-09-30", freq="D")
    cobertura = pd.read_csv(fontes / "cobertura.csv", parse_dates=["data"])
    if cobertura.data.tolist() != list(calendario) or not cobertura.completo.eq(1).all():
        raise ValueError("O período de avaliação requer todos os boletins diários completos.")
    # O histórico do CGE e os acumulados da chuva na virada do ano usam 2023–2025.
    with TemporaryDirectory(prefix="rota-seca-painel-") as temporario:
        pasta = Path(temporario)
        for subpasta in ["cge", "chuva", "geografia"]:
            (pasta / subpasta).mkdir()
        for arquivo in ["cge/cobertura.csv", "cge/eventos.csv", "chuva/chuva_a701.csv"]:
            unir_periodos(DADOS / arquivo, fontes / Path(arquivo).name, pasta / arquivo)
        for arquivo in ["cge/trechos.csv", "geografia/atributos_trechos.csv"]:
            shutil.copyfile(DADOS / arquivo, pasta / arquivo)
        avaliacao = preparar(pasta, inicio_modelo=calendario[0])
    if avaliacao.empty or avaliacao.hora_local.max() > calendario[-1] + pd.Timedelta(hours=22):
        raise ValueError("Período de emissão inesperado.")
    saida.parent.mkdir(exist_ok=True, parents=True)
    with saida.open("wb") as bruto:
        with gzip.GzipFile(filename="", mode="wb", fileobj=bruto, mtime=0) as gz:
            avaliacao.to_csv(gz, index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S")
    print(f"{len(avaliacao)} previsões avaliáveis no período de 2026.")


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--fontes", type=Path, default=PASTA, help="Pasta com os três CSVs de 2026")
    argumentos.add_argument("--saida", type=Path, default=PASTA / "painel_trecho_hora.csv.gz")
    args = argumentos.parse_args()
    gerar(args.fontes, args.saida)
