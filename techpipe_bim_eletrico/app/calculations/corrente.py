"""
calculations/corrente.py — Cálculo de corrente elétrica
Aplica as fórmulas corretas para cada sistema elétrico conforme NBR 5410.
"""

from app.config import SISTEMAS_ELETRICOS, TIPOS_CARGA
from app.utils.logger import get_logger
from app.utils.validators import validar_positivo

logger = get_logger(__name__)


def calcular_corrente(
    potencia_w: float,
    tensao_v: float,
    sistema: str = "monofasico",
    fator_potencia: float = 1.0,
    fator_demanda: float = 1.0,
    fator_simultaneidade: float = 1.0,
) -> dict:
    """
    Calcula a corrente de projeto de um circuito elétrico.

    Parâmetros
    ----------
    potencia_w          : Potência total instalada em Watts
    tensao_v            : Tensão do circuito em Volts
    sistema             : 'monofasico', 'bifasico' ou 'trifasico'
    fator_potencia      : cos φ da carga (0.0 a 1.0)
    fator_demanda       : fração da carga que realmente opera (0.0 a 1.0)
    fator_simultaneidade: fração de circuitos operando ao mesmo tempo

    Retorna
    -------
    dict com:
        corrente_nominal   : corrente sem fatores de demanda
        corrente_projeto   : corrente real de dimensionamento
        potencia_efetiva   : potência após aplicar fatores
        sistema            : sistema elétrico utilizado
    """

    # ── Validações ────────────────────────────────────────────
    validar_positivo(potencia_w, "potência")
    validar_positivo(tensao_v, "tensão")

    if sistema not in SISTEMAS_ELETRICOS:
        raise ValueError(
            f"Sistema '{sistema}' inválido. "
            f"Use: {list(SISTEMAS_ELETRICOS.keys())}"
        )

    if not 0.0 < fator_potencia <= 1.0:
        raise ValueError("Fator de potência deve ser entre 0 e 1.")

    if not 0.0 < fator_demanda <= 1.0:
        raise ValueError("Fator de demanda deve ser entre 0 e 1.")

    if not 0.0 < fator_simultaneidade <= 1.0:
        raise ValueError("Fator de simultaneidade deve ser entre 0 e 1.")

    # ── Cálculo ───────────────────────────────────────────────
    fator_sistema = SISTEMAS_ELETRICOS[sistema]

    # Potência efetiva após fatores operacionais
    potencia_efetiva = potencia_w * fator_demanda * fator_simultaneidade

    # Corrente sem correção de fp (apenas sistema)
    # I = P / (V × √3 × fp) para trifásico
    # I = P / (V × fp) para mono
    corrente_nominal = potencia_w / (tensao_v * fator_sistema * fator_potencia)

    # Corrente de projeto (com fatores de demanda)
    corrente_projeto = potencia_efetiva / (tensao_v * fator_sistema * fator_potencia)

    logger.info(
        f"Corrente calculada | Sistema: {sistema} | "
        f"P={potencia_w}W | V={tensao_v}V | fp={fator_potencia} | "
        f"I_nominal={corrente_nominal:.2f}A | I_projeto={corrente_projeto:.2f}A"
    )

    return {
        "corrente_nominal":    round(corrente_nominal, 2),
        "corrente_projeto":    round(corrente_projeto, 2),
        "potencia_efetiva":    round(potencia_efetiva, 2),
        "sistema":             sistema,
        "fator_sistema":       fator_sistema,
        "fator_potencia":      fator_potencia,
        "fator_demanda":       fator_demanda,
        "fator_simultaneidade": fator_simultaneidade,
    }


def corrente_por_tipo_carga(
    potencia_w: float,
    tensao_v: float,
    sistema: str,
    tipo_carga: str,
) -> dict:
    """
    Versão simplificada: busca o fator de potência pelo tipo de carga.

    Parâmetros
    ----------
    tipo_carga : chave em TIPOS_CARGA (ex: 'resistiva', 'indutiva')
    """
    if tipo_carga not in TIPOS_CARGA:
        raise ValueError(
            f"Tipo de carga '{tipo_carga}' inválido. "
            f"Use: {list(TIPOS_CARGA.keys())}"
        )

    fp = TIPOS_CARGA[tipo_carga]["fp"]
    logger.info(f"Tipo de carga: {tipo_carga} → fp={fp}")

    return calcular_corrente(
        potencia_w=potencia_w,
        tensao_v=tensao_v,
        sistema=sistema,
        fator_potencia=fp,
    )
