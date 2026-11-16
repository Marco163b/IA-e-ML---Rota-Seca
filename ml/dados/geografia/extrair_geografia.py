"""Cruza eixos de rua do GeoSampa e extrai relevo SRTM e distância à drenagem."""

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image
from pyproj import Geod, Transformer
from shapely.geometry import shape
from shapely.ops import unary_union


WFS = "https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs"
SRTM = "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1/SRTM_GL1_srtm/S24W047.tif"
PARA_WGS84 = Transformer.from_crs(31983, 4326, always_xy=True)
GEOD = Geod(ellps="WGS84")
CRUZAMENTOS = [
    ("RS01", "062383", "480193"),
    ("RS02", "062383", "639664"),
    ("RS03", "215147", "181196"),
    ("RS04", "009997", "215147"),
]


def obter(url, destino):
    if destino.exists():
        return
    pedido = Request(url, headers={"User-Agent": "Rota-Seca-FIAP/1.0"})
    with urlopen(pedido, timeout=120) as resposta:
        dados = resposta.read()
    destino.write_bytes(dados)


def feicoes(pasta, nome, camada, campos, filtros):
    parametros = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": f"geoportal:{camada}", "outputFormat": "application/json",
        "srsName": "EPSG:31983", "propertyName": campos, **filtros,
    }
    destino = pasta / f"{nome}.geojson"
    obter(WFS + "?" + urlencode(parametros), destino)
    colecao = json.loads(destino.read_bytes())
    registros = colecao["features"]
    if int(colecao["totalFeatures"]) != len(registros):
        raise ValueError(f"Resposta incompleta para {nome}")
    return [(shape(item["geometry"]), item["properties"]) for item in registros]


def atributos_relevo(imagem, lon, lat):
    # PixelIsPoint. O primeiro pixel coincide com a coordenada do tiepoint.
    _, _, _, oeste, norte, _ = imagem.tag_v2[33922]
    passo_x, passo_y, _ = imagem.tag_v2[33550]
    x, y = round((lon - oeste) / passo_x), round((norte - lat) / passo_y)
    if not (0 < x < imagem.width - 1 and 0 < y < imagem.height - 1):
        raise ValueError("Janela de relevo fora da folha S24W047")
    alturas = [imagem.getpixel((x + coluna, y + linha))
               for linha in (-1, 0, 1) for coluna in (-1, 0, 1)]
    if int(imagem.tag_v2[42113]) in alturas:
        raise ValueError("A vizinhança SRTM contém célula ausente")
    a, b, c, d, centro, f, g, h, i = alturas
    centro_lon = oeste + x * passo_x
    centro_lat = norte - y * passo_y
    _, _, dx = GEOD.inv(centro_lon, centro_lat, centro_lon + passo_x, centro_lat)
    _, _, dy = GEOD.inv(centro_lon, centro_lat, centro_lon, centro_lat + passo_y)
    grad_x = ((c + 2*f + i) - (a + 2*d + g)) / (8 * dx)
    grad_y = ((g + 2*h + i) - (a + 2*b + c)) / (8 * dy)
    return centro, 100 * (grad_x**2 + grad_y**2)**0.5


def reconstruir(pasta, saida):
    pasta.mkdir(parents=True, exist_ok=True)
    codigos = sorted({cod for _, via1, via2 in CRUZAMENTOS for cod in (via1, via2)})
    selecao = ",".join(f"'{cod}'" for cod in codigos)
    ruas = feicoes(pasta, "vias", "segmento_logradouro", "codlog,ge_linha",
                   {"CQL_FILTER": f"codlog IN ({selecao})"})
    eixos = {cod: unary_union([geom for geom, p in ruas if p["codlog"] == cod]) for cod in codigos}
    pontos = {}
    for trecho, primeira, segunda in CRUZAMENTOS:
        encontro = eixos[primeira].intersection(eixos[segunda])
        if encontro.is_empty or encontro.geom_type not in ("MultiPoint", "Point"):
            raise ValueError(f"Interseção pontual esperada em {trecho}: {encontro.geom_type}")
        pontos[trecho] = encontro.centroid

    area = unary_union(list(pontos.values())).buffer(2000).bounds
    bbox = ",".join(str(v) for v in area) + ",EPSG:31983"
    distritos = feicoes(pasta, "distritos", "distrito_municipal", "nm_distrito_municipal,ge_poligono",
                        {"bbox": bbox})
    drenagem = feicoes(pasta, "drenagem", "drenagem", "cd_tipo_acidente,nm_acidente,ge_linha",
                       {"bbox": bbox})
    corregos = [(g, p) for g, p in drenagem if p["cd_tipo_acidente"] == "COR"]
    raster = pasta / "S24W047.tif"
    obter(SRTM, raster)
    linhas = []
    with Image.open(raster) as imagem:
        for trecho, ponto in pontos.items():
            lon, lat = PARA_WGS84.transform(ponto.x, ponto.y)
            elevacao, declividade = atributos_relevo(imagem, lon, lat)
            geom, dados = min(corregos, key=lambda item: item[0].distance(ponto))
            distancia = ponto.distance(geom)
            if distancia >= 2000:
                raise ValueError(f"Área de busca insuficiente para {trecho}")
            regioes = sorted(p["nm_distrito_municipal"] for g, p in distritos if g.covers(ponto))
            if not regioes:
                raise ValueError(f"Distrito desconhecido para {trecho}")
            _, _, dist_estacao = GEOD.inv(lon, lat, -46.6200666, -23.4962888)
            linhas.append({
                "trecho_id": trecho, "latitude": f"{lat:.7f}", "longitude": f"{lon:.7f}",
                "elevacao_m": elevacao, "declividade_pct": f"{declividade:.2f}",
                "distancia_corrego_m": f"{distancia:.1f}", "corrego": dados["nm_acidente"] or "",
                "distrito": " / ".join(regioes), "distancia_a701_km": f"{dist_estacao / 1000:.2f}",
            })
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8", newline="") as arquivo:
        tabela = csv.DictWriter(arquivo, fieldnames=list(linhas[0]), lineterminator="\n")
        tabela.writeheader()
        tabela.writerows(linhas)


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--cache", type=Path, required=True, help="Pasta para as respostas WFS e a folha SRTM")
    argumentos.add_argument("--saida", type=Path, required=True)
    opcoes = argumentos.parse_args()
    reconstruir(opcoes.cache, opcoes.saida)
