"""
calculations/conduites.py — Dimensionamento de conduítes
Calcula área ocupada pelos cabos e escolhe o menor conduíte adequado.
NBR 5410 item 6.2.9 — ocupação máxima de 40%.
"""

from app.config import CONDUITS_DADOS, CABO_AREA_TOTAL, OCUPACAO_MAXIMA_CONDUIT
from app.utils.logger import get_logger

logger = get_logger(__name__)


TIPOS_CONDUIT = {
    "PVC_rigido":       "PVC Rígido — uso em parede/laje",
    "PVC_flexivel":     "PVC Flexível (corrugado) — uso em forro/embutido",
    "aco_galvanizado":  "Aço Galvanizado — uso industrial / ambiente agressivo",
    "PEAD":             "PEAD — uso subterrâneo",
}


def calcular_area_cabos(
    secao_mm2: float,
    quantidade_condutores: int,
) -> dict:
    """
    Calcula a área total ocupada pelos condutores (fase + neutro + terra) no conduíte.

    Parâmetros
    ----------
    secao_mm2           : bitola dos condutores (todos do mesmo tipo)
    quantidade_condutores: número total de condutores no conduíte

    Retorna
    -------
    dict com área total e margem disponível
    """
    if secao_mm2 not in CABO_AREA_TOTAL:
        raise ValueError(f"Seção {secao_mm2}mm² não encontrada na tabela de áreas.")

    area_por_condutor = CABO_AREA_TOTAL[secao_mm2]
    area_total_cabos = area_por_condutor * quantidade_condutores

    logger.info(
        f"Área cabos | {quantidade_condutores}x {secao_mm2}mm² | "
        f"A_unit={area_por_condutor}mm² | A_total={area_total_cabos}mm²"
    )

    return {
        "area_por_condutor_mm2": area_por_condutor,
        "area_total_cabos_mm2":  area_total_cabos,
        "quantidade_condutores": quantidade_condutores,
        "secao_mm2":             secao_mm2,
    }


def calcular_area_cabos_mistos(condutores: list[dict]) -> dict:
    """
    Calcula área de condutores de bitolas diferentes no mesmo conduíte.

    Parâmetros
    ----------
    condutores : lista de dicts com {'secao_mm2': float, 'quantidade': int}
                 Ex: [{'secao_mm2': 6.0, 'quantidade': 2},
                      {'secao_mm2': 2.5, 'quantidade': 1}]

    Retorna
    -------
    dict com área total e detalhamento por bitola
    """
    detalhes = []
    area_total = 0.0

    for cond in condutores:
        secao = cond["secao_mm2"]
        qtd = cond["quantidade"]

        if secao not in CABO_AREA_TOTAL:
            raise ValueError(f"Seção {secao}mm² não encontrada.")

        area_unit = CABO_AREA_TOTAL[secao]
        area_parcial = area_unit * qtd
        area_total += area_parcial

        detalhes.append({
            "secao_mm2":      secao,
            "quantidade":     qtd,
            "area_unitaria":  area_unit,
            "area_parcial":   area_parcial,
        })

    logger.info(f"Área total cabos mistos: {area_total:.1f}mm²")

    return {
        "area_total_cabos_mm2": area_total,
        "detalhes":             detalhes,
    }


def selecionar_conduit(
    area_total_cabos_mm2: float,
    tipo: str = "PVC_rigido",
) -> dict:
    """
    Seleciona o menor conduíte que acomoda os cabos respeitando
    a ocupação máxima de 40% conforme NBR 5410.

    Parâmetros
    ----------
    area_total_cabos_mm2 : área somada de todos os condutores
    tipo                 : tipo de conduíte (PVC_rigido, aco_galvanizado, etc.)

    Retorna
    -------
    dict com DN selecionado, ocupação real e verificação normativa
    """
    if tipo not in TIPOS_CONDUIT:
        raise ValueError(
            f"Tipo '{tipo}' inválido. Use: {list(TIPOS_CONDUIT.keys())}"
        )

    # Área mínima de conduíte necessária (respeitando ocupação máxima)
    area_interna_necessaria = area_total_cabos_mm2 / OCUPACAO_MAXIMA_CONDUIT

    conduit_selecionado = None
    area_interna_conduit = None

    for dn, area in sorted(CONDUITS_DADOS.items()):
        if area >= area_interna_necessaria:
            conduit_selecionado = dn
            area_interna_conduit = area
            break

    if conduit_selecionado is None:
        raise ValueError(
            f"Área necessária {area_interna_necessaria:.1f}mm² excede o maior conduíte disponível. "
            "Considere dividir em dois conduítes."
        )

    ocupacao_real = (area_total_cabos_mm2 / area_interna_conduit) * 100

    logger.info(
        f"Conduíte | DN={conduit_selecionado}mm | Tipo={tipo} | "
        f"Ocupação={ocupacao_real:.1f}% (limite 40%)"
    )

    return {
        "dn_mm":                  conduit_selecionado,
        "tipo":                   tipo,
        "tipo_descricao":         TIPOS_CONDUIT[tipo],
        "area_interna_mm2":       area_interna_conduit,
        "area_cabos_mm2":         round(area_total_cabos_mm2, 1),
        "area_necessaria_mm2":    round(area_interna_necessaria, 1),
        "ocupacao_real_pct":      round(ocupacao_real, 1),
        "limite_ocupacao_pct":    OCUPACAO_MAXIMA_CONDUIT * 100,
        "aprovado":               ocupacao_real <= OCUPACAO_MAXIMA_CONDUIT * 100,
    }


def dimensionar_conduit_completo(
    secao_mm2: float,
    sistema: str = "monofasico",
    com_neutro: bool = True,
    com_terra: bool = True,
    tipo_conduit: str = "PVC_rigido",
) -> dict:
    """
    Função completa: calcula os condutores necessários e seleciona o conduíte.

    Parâmetros
    ----------
    secao_mm2  : bitola dos condutores de fase
    sistema    : define quantidade de fases
    com_neutro : inclui condutor neutro
    com_terra  : inclui condutor de proteção (PE)
    tipo_conduit: tipo de conduíte

    Retorna
    -------
    dict com conduíte selecionado e todos os detalhes
    """
    # Quantidade de condutores por sistema
    fases = {"monofasico": 1, "bifasico": 2, "trifasico": 3}
    qtd_fases = fases.get(sistema, 1)

    qtd_total = qtd_fases
    if com_neutro:
        qtd_total += 1
    if com_terra:
        qtd_total += 1

    # Terra pode ser menor — NBR 5410 Tabela 54G
    # Para simplificar fase 1: mesmo cabo para todas as vias
    area_info = calcular_area_cabos(secao_mm2, qtd_total)
    conduit_info = selecionar_conduit(
        area_total_cabos_mm2=area_info["area_total_cabos_mm2"],
        tipo=tipo_conduit,
    )

    resultado = {
        "sistema":           sistema,
        "secao_cabos_mm2":   secao_mm2,
        "qtd_fases":         qtd_fases,
        "com_neutro":        com_neutro,
        "com_terra":         com_terra,
        "qtd_condutores":    qtd_total,
        **area_info,
        **conduit_info,
    }

    logger.info(
        f"Conduíte completo: {qtd_total} condutores {secao_mm2}mm² → "
        f"DN{conduit_info['dn_mm']}mm {tipo_conduit}"
    )

    return resultado
