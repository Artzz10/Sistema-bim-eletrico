"""
calculations/queda_tensao.py — Cálculo de queda de tensão
Fórmula simplificada e verificação conforme NBR 5410 item 6.5.
"""

from app.config import RESISTIVIDADE, QUEDA_TENSAO_MAXIMA, CABOS_AMPACIDADE
from app.utils.logger import get_logger

logger = get_logger(__name__)


def calcular_queda_tensao(
    corrente_a: float,
    distancia_m: float,
    secao_mm2: float,
    tensao_v: float,
    material: str = "cobre",
    sistema: str = "monofasico",
) -> dict:
    """
    Calcula a queda de tensão de um circuito.

    Fórmula NBR 5410 (simplificada):
        ΔV = (2 × L × I × ρ) / S       ← monofásico / bifásico
        ΔV = (√3 × L × I × ρ) / S      ← trifásico

    Onde:
        ΔV  = queda de tensão (V)
        L   = comprimento do circuito (m)
        I   = corrente do circuito (A)
        ρ   = resistividade do condutor (Ω·mm²/m)
        S   = seção do condutor (mm²)

    Parâmetros
    ----------
    corrente_a   : corrente de projeto do circuito (A)
    distancia_m  : comprimento do circuito em metros (distância total do cabo)
    secao_mm2    : seção do condutor em mm²
    tensao_v     : tensão nominal do circuito (V)
    material     : 'cobre' ou 'aluminio'
    sistema      : 'monofasico', 'bifasico' ou 'trifasico'

    Retorna
    -------
    dict com ΔV em volts, percentual e status normativo
    """
    if material not in RESISTIVIDADE:
        raise ValueError(f"Material '{material}' inválido. Use 'cobre' ou 'aluminio'.")

    if secao_mm2 not in CABOS_AMPACIDADE:
        raise ValueError(f"Seção {secao_mm2}mm² não reconhecida.")

    rho = RESISTIVIDADE[material]

    # Fator de comprimento: ×2 para mono/bifásico (ida+volta), ×√3 para trifásico
    fator_sistema = 2.0 if sistema in ("monofasico", "bifasico") else 1.732

    # ΔV em Volts
    queda_v = (fator_sistema * distancia_m * corrente_a * rho) / secao_mm2

    # ΔV em percentual
    queda_pct = (queda_v / tensao_v) * 100

    # Limite normativo para circuito final (mais conservador)
    limite_pct = QUEDA_TENSAO_MAXIMA["circuito_final"] * 100   # 4%
    aprovado = queda_pct <= limite_pct

    status = "APROVADO" if aprovado else "REPROVADO"

    logger.info(
        f"Queda de tensão | I={corrente_a}A | L={distancia_m}m | "
        f"S={secao_mm2}mm² | ΔV={queda_v:.2f}V ({queda_pct:.2f}%) | "
        f"Limite={limite_pct}% | {status}"
    )

    return {
        "queda_tensao_v":       round(queda_v, 3),
        "queda_tensao_pct":     round(queda_pct, 2),
        "tensao_v":             tensao_v,
        "tensao_residual_v":    round(tensao_v - queda_v, 2),
        "limite_normativo_pct": limite_pct,
        "aprovado":             aprovado,
        "status":               status,
        "material":             material,
        "secao_mm2":            secao_mm2,
        "distancia_m":          distancia_m,
    }


def secao_minima_para_queda(
    corrente_a: float,
    distancia_m: float,
    tensao_v: float,
    queda_maxima_pct: float = 4.0,
    material: str = "cobre",
    sistema: str = "monofasico",
) -> dict:
    """
    Calcula a seção mínima necessária para não ultrapassar a queda de tensão máxima.
    Útil para verificar se o cabo escolhido por ampacidade é suficiente.

    Fórmula inversa:
        S_min = (fator × L × I × ρ) / ΔV_max

    Retorna
    -------
    dict com seção mínima calculada e cabo normalizado correspondente
    """
    rho = RESISTIVIDADE[material]
    fator_sistema = 2.0 if sistema in ("monofasico", "bifasico") else 1.732

    # Queda de tensão máxima em Volts
    queda_max_v = tensao_v * (queda_maxima_pct / 100)

    # Seção mínima (contínua)
    secao_minima_calculada = (fator_sistema * distancia_m * corrente_a * rho) / queda_max_v

    # Cabo normalizado imediatamente superior
    secoes = sorted(CABOS_AMPACIDADE.keys())
    secao_normalizada = None
    for s in secoes:
        if s >= secao_minima_calculada:
            secao_normalizada = s
            break

    logger.info(
        f"Seção mínima queda tensão: {secao_minima_calculada:.2f}mm² → "
        f"Normalizada: {secao_normalizada}mm²"
    )

    return {
        "secao_minima_calculada_mm2": round(secao_minima_calculada, 3),
        "secao_normalizada_mm2":      secao_normalizada,
        "queda_maxima_v":             round(queda_max_v, 2),
        "queda_maxima_pct":           queda_maxima_pct,
        "corrente_a":                 corrente_a,
        "distancia_m":                distancia_m,
        "material":                   material,
    }
