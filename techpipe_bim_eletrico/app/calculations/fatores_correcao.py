"""
calculations/temperatura.py — Fatores de correção de temperatura
calculations/agrupamento.py — Fatores de correção de agrupamento

NBR 5410 Tabela 41 (temperatura) e Tabela 42 (agrupamento)
"""

from app.config import FATORES_TEMPERATURA, FATORES_AGRUPAMENTO
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════════
# TEMPERATURA
# ══════════════════════════════════════════════════════════════

def fator_correcao_temperatura(temperatura_ambiente: float) -> float:
    """
    Retorna o fator de correção de temperatura conforme NBR 5410 Tabela 41.
    Interpolação linear entre os valores tabelados.

    Parâmetros
    ----------
    temperatura_ambiente : temperatura em °C

    Retorna
    -------
    Fator de correção (float). Multiplica a ampacidade nominal do cabo.

    Exemplos
    --------
    30°C → 1.00 (sem correção)
    40°C → 0.87 (ampacidade reduzida em 13%)
    50°C → 0.71 (ampacidade reduzida em 29%)
    """
    temperaturas = sorted(FATORES_TEMPERATURA.keys())

    # Abaixo do mínimo tabelado
    if temperatura_ambiente <= temperaturas[0]:
        fator = FATORES_TEMPERATURA[temperaturas[0]]
        logger.info(f"Temperatura {temperatura_ambiente}°C → fator={fator} (limite inferior)")
        return fator

    # Acima do máximo tabelado — situação crítica
    if temperatura_ambiente >= temperaturas[-1]:
        fator = FATORES_TEMPERATURA[temperaturas[-1]]
        logger.warning(
            f"Temperatura {temperatura_ambiente}°C ACIMA do limite da tabela! "
            f"Verificar viabilidade da instalação. Fator={fator}"
        )
        return fator

    # Interpolação linear entre dois valores tabelados
    for i in range(len(temperaturas) - 1):
        t1 = temperaturas[i]
        t2 = temperaturas[i + 1]

        if t1 <= temperatura_ambiente <= t2:
            f1 = FATORES_TEMPERATURA[t1]
            f2 = FATORES_TEMPERATURA[t2]
            # Interpolação: y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
            fator = f1 + (temperatura_ambiente - t1) * (f2 - f1) / (t2 - t1)
            fator = round(fator, 4)
            logger.info(
                f"Temperatura {temperatura_ambiente}°C → "
                f"interpolado entre {t1}°C({f1}) e {t2}°C({f2}) → fator={fator}"
            )
            return fator

    return 1.0  # fallback (não deve chegar aqui)


def corrente_corrigida_temperatura(
    corrente_projeto: float,
    temperatura_ambiente: float,
) -> dict:
    """
    Calcula a corrente de dimensionamento após correção de temperatura.
    A corrente de projeto é DIVIDIDA pelo fator (pois o fator reduz a ampacidade).

    Parâmetros
    ----------
    corrente_projeto     : corrente calculada do circuito (A)
    temperatura_ambiente : temperatura local em °C

    Retorna
    -------
    dict com corrente corrigida e fator aplicado
    """
    fator = fator_correcao_temperatura(temperatura_ambiente)

    # Lógica: se o cabo suporta menos calor, precisamos de um cabo maior.
    # corrente_dimensionamento = I_projeto / fator_temperatura
    corrente_dimensionamento = corrente_projeto / fator

    return {
        "corrente_projeto":        round(corrente_projeto, 2),
        "corrente_dimensionamento": round(corrente_dimensionamento, 2),
        "fator_temperatura":       round(fator, 4),
        "temperatura_ambiente":    temperatura_ambiente,
        "requer_correcao":         temperatura_ambiente != 30,
    }


# ══════════════════════════════════════════════════════════════
# AGRUPAMENTO
# ══════════════════════════════════════════════════════════════

def fator_correcao_agrupamento(numero_circuitos: int) -> float:
    """
    Retorna o fator de correção de agrupamento conforme NBR 5410 Tabela 42.
    Quando vários circuitos passam pelo mesmo conduíte, o calor acumulado
    reduz a capacidade de cada cabo.

    Parâmetros
    ----------
    numero_circuitos : quantidade de circuitos agrupados no mesmo conduíte

    Retorna
    -------
    Fator de correção (float). Valores < 1.0 indicam redução de ampacidade.
    """
    if numero_circuitos <= 0:
        raise ValueError("Número de circuitos deve ser maior que zero.")

    # Busca exata na tabela
    if numero_circuitos in FATORES_AGRUPAMENTO:
        fator = FATORES_AGRUPAMENTO[numero_circuitos]
        logger.info(f"Agrupamento: {numero_circuitos} circuitos → fator={fator}")
        return fator

    # Interpolação para valores intermediários
    chaves = sorted(FATORES_AGRUPAMENTO.keys())

    if numero_circuitos > chaves[-1]:
        fator = FATORES_AGRUPAMENTO[chaves[-1]]
        logger.warning(
            f"Agrupamento com {numero_circuitos} circuitos acima da tabela. "
            f"Usando fator conservador={fator}"
        )
        return fator

    for i in range(len(chaves) - 1):
        n1 = chaves[i]
        n2 = chaves[i + 1]
        if n1 < numero_circuitos < n2:
            f1 = FATORES_AGRUPAMENTO[n1]
            f2 = FATORES_AGRUPAMENTO[n2]
            fator = f1 + (numero_circuitos - n1) * (f2 - f1) / (n2 - n1)
            fator = round(fator, 4)
            logger.info(
                f"Agrupamento {numero_circuitos} (interpolado entre {n1} e {n2}) → fator={fator}"
            )
            return fator

    return 1.0


def corrente_corrigida_agrupamento(
    corrente_dimensionamento: float,
    numero_circuitos: int,
) -> dict:
    """
    Aplica a correção de agrupamento sobre a corrente de dimensionamento.

    Parâmetros
    ----------
    corrente_dimensionamento : corrente já corrigida por temperatura
    numero_circuitos         : circuitos agrupados no mesmo conduíte

    Retorna
    -------
    dict com corrente final de dimensionamento e fatores aplicados
    """
    fator = fator_correcao_agrupamento(numero_circuitos)

    corrente_final = corrente_dimensionamento / fator

    return {
        "corrente_entrada":     round(corrente_dimensionamento, 2),
        "corrente_final":       round(corrente_final, 2),
        "fator_agrupamento":    round(fator, 4),
        "numero_circuitos":     numero_circuitos,
        "requer_correcao":      numero_circuitos > 1,
    }


# ══════════════════════════════════════════════════════════════
# FUNÇÃO COMBINADA
# ══════════════════════════════════════════════════════════════

def aplicar_fatores_correcao(
    corrente_projeto: float,
    temperatura_ambiente: float,
    numero_circuitos: int,
) -> dict:
    """
    Aplica TODOS os fatores de correção em sequência:
    temperatura → agrupamento

    Esta é a função principal que o motor de cálculo deve usar.

    Retorna
    -------
    dict completo com todos os fatores e a corrente final de dimensionamento
    """
    # 1. Corrigir temperatura
    res_temp = corrente_corrigida_temperatura(corrente_projeto, temperatura_ambiente)

    # 2. Corrigir agrupamento
    res_agrup = corrente_corrigida_agrupamento(
        corrente_dimensionamento=res_temp["corrente_dimensionamento"],
        numero_circuitos=numero_circuitos,
    )

    fator_combinado = res_temp["fator_temperatura"] * res_agrup["fator_agrupamento"]

    logger.info(
        f"Fatores combinados | Temp={res_temp['fator_temperatura']} × "
        f"Agrup={res_agrup['fator_agrupamento']} = {round(fator_combinado, 4)} | "
        f"I_projeto={corrente_projeto}A → I_final={res_agrup['corrente_final']}A"
    )

    return {
        "corrente_projeto":        corrente_projeto,
        "corrente_final":          res_agrup["corrente_final"],
        "fator_temperatura":       res_temp["fator_temperatura"],
        "fator_agrupamento":       res_agrup["fator_agrupamento"],
        "fator_combinado":         round(fator_combinado, 4),
        "temperatura_ambiente":    temperatura_ambiente,
        "numero_circuitos":        numero_circuitos,
    }
