"""Extrai boletins diários do CGE e identifica quatro cruzamentos no eixo sul."""
import argparse
import csv
from datetime import date, datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


URL = "https://www.cgesp.org/v3/alagamentos.jsp"
TRECHOS = [
    ("RS01", "Avenida das Nações Unidas", "Rua Olívia Feder"),
    ("RS02", "Avenida das Nações Unidas", "Rua Jaime de Oliveira Souza"),
    ("RS03", "Avenida Roque Petroni Júnior", "Rua Cancioneiro Popular"),
    ("RS04", "Avenida Santo Amaro", "Avenida Roque Petroni Júnior"),
]
CAMPOS_EVENTOS = [
    "trecho_id", "inicio_local", "hora_fim_cge", "area_cge", "logradouro_cge",
    "referencia_cge", "sentido_cge", "situacao_cge",
]
ABREVIACOES = {
    "AVENIDA": "AV", "RUA": "R", "SANTO": "STO", "JR": "JUNIOR",
}


def normalizar(via):
    decomposicao = unicodedata.normalize("NFKD", via.upper())
    sem_acentos = "".join(c for c in decomposicao if not unicodedata.combining(c))
    palavras = re.findall(r"[A-Z0-9]+", sem_acentos)
    return " ".join(ABREVIACOES.get(palavra, palavra) for palavra in palavras)


def cruzamento(logradouro, referencia):
    return tuple(sorted((normalizar(logradouro), normalizar(referencia))))


def carregar(cache, dia, baixar):
    arquivo = cache / f"{dia.isoformat()}.html"
    if arquivo.is_file():
        return arquivo.read_bytes()
    if not baixar:
        raise FileNotFoundError(f"Boletim ausente em {arquivo}. Consulte --baixar.")
    consulta = urlencode({"dataBusca": dia.strftime("%d/%m/%Y")})
    pedido = Request(f"{URL}?{consulta}", headers={"User-Agent": "RotaSeca-EstudoAcademico/1.0"})
    # Os boletins são consultados em série; uma resposta de erro interrompe a coleta.
    time.sleep(1.0)
    with urlopen(pedido, timeout=30) as resposta:
        pagina = resposta.read()
    analisar(pagina, dia)
    arquivo.write_bytes(pagina)
    return pagina


def analisar(conteudo, dia):
    pagina = BeautifulSoup(conteudo.decode("utf-8"), "html.parser")
    data_consultada = pagina.select_one("input[name=dataBusca]")
    if data_consultada is None or data_consultada.get("value") != dia.strftime("%d/%m/%Y"):
        raise ValueError(f"{dia}: data do boletim divergente")
    totais = []
    for bloco in pagina.select(".alag-resumo h1"):
        valor = re.fullmatch(r"(?:Intransitáveis|Transitáveis)\s*=\s*(\d+)\s*pts?", bloco.get_text(strip=True), re.I)
        if valor is None:
            raise ValueError(f"{dia}: total do CGE irreconhecível")
        totais.append(int(valor[1]))
    registros = []
    for tabela in pagina.select("table.tb-pontos-de-alagamentos"):
        area = tabela.select_one("td.bairro").get_text(strip=True)
        for ponto in tabela.select(".ponto-de-alagamento"):
            celula_local, celula_detalhes = ponto.select("li.arial-descr-alag")
            local = list(celula_local.stripped_strings)
            situacao = ponto.select_one("li[title]")["title"]
            horas = re.fullmatch(r"De (\d{2}:\d{2}) a(?: (\d{2}:\d{2}|ATIVO))?", local[0], re.I)
            # O CGE pode deixar apenas "a" ao fim de uma ocorrência ainda ativa.
            if horas is None or (horas[2] is None and not situacao.lower().startswith("ativo ")):
                raise ValueError(f"{dia}: horário não reconhecido {local[0]}")
            detalhes = dict(
                campo.split(":", 1) for campo in celula_detalhes.stripped_strings if ":" in campo
            )
            inicio = datetime.combine(dia, datetime.strptime(horas[1], "%H:%M").time())
            registros.append({
                "inicio_local": inicio.isoformat(sep=" ", timespec="seconds"),
                "hora_fim_cge": horas[2] or "",
                "area_cge": area,
                "logradouro_cge": " ".join(local[1:]),
                "referencia_cge": detalhes.get("Referência", "").strip(),
                "sentido_cge": detalhes.get("Sentido", "").strip(),
                "situacao_cge": situacao,
            })
    if len(totais) != 4 or sum(totais) != len(registros):
        raise ValueError(f"{dia}: resumo {totais} e {len(registros)} registros incompatíveis")
    if not registros and "Não há registros de alagamentos para essa data" not in pagina.get_text():
        raise ValueError(f"{dia}: boletim sem confirmação explícita de ausência de registros")
    return registros


def escrever(arquivo, campos, linhas):
    with arquivo.open("w", encoding="utf-8", newline="") as saida:
        gravador = csv.DictWriter(saida, fieldnames=campos, lineterminator="\n")
        gravador.writeheader()
        gravador.writerows(linhas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True, help="Pasta dos boletins originais")
    parser.add_argument("--baixar", action="store_true", help="Baixar em série as datas ausentes")
    parser.add_argument("--inicio", type=date.fromisoformat, default=date(2023, 1, 1))
    parser.add_argument("--fim", type=date.fromisoformat, default=date(2025, 12, 31))
    parser.add_argument("--saida", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    if args.fim < args.inicio:
        parser.error("A data final deve ser posterior ou igual à inicial.")
    args.cache.mkdir(exist_ok=True, parents=True)
    args.saida.mkdir(exist_ok=True, parents=True)
    chaves = {cruzamento(a, b): codigo for codigo, a, b in TRECHOS}
    eventos, cobertura = [], []
    dia = args.inicio
    while dia <= args.fim:
        registros = analisar(carregar(args.cache, dia, args.baixar), dia)
        relacao = json.dumps(registros, ensure_ascii=False, separators=(",", ":"))
        cobertura.append({
            "data": dia, "completo": 1, "total_cge": len(registros),
            "sha256_relacao": sha256(relacao.encode("utf-8")).hexdigest(),
        })
        for item in registros:
            trecho = chaves.get(cruzamento(item["logradouro_cge"], item["referencia_cge"]))
            if trecho:
                eventos.append({"trecho_id": trecho, **item})
        dia += timedelta(days=1)
    eventos.sort(key=lambda linha: tuple(linha[c] for c in CAMPOS_EVENTOS))
    escrever(args.saida / "eventos.csv", CAMPOS_EVENTOS, eventos)
    escrever(args.saida / "cobertura.csv", ["data", "completo", "total_cge", "sha256_relacao"], cobertura)
    escrever(args.saida / "trechos.csv", ["trecho_id", "logradouro", "referencia"], [
        {"trecho_id": codigo, "logradouro": via, "referencia": ref} for codigo, via, ref in TRECHOS
    ])
    print(f"{len(cobertura)} boletins verificados e {len(eventos)} registros nos quatro cruzamentos.")


if __name__ == "__main__":
    main()
