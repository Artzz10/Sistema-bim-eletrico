"""
calculations/disjuntores.py — Dimensionamento de disjuntores
Seleciona corrente nominal, curva e capacidade de interrupção.
NBR 5410 item 6.3.
"""

from app.config import DISJUNTORES_NOMINAIS, CURVAS_DISJUNTOR
from app.utils.logger import get_logger

logger = get_logger(__name__)


def selecionar_disjuntor(
    corrente_projeto: float,
    ampacidade_cabo: float,
    tipo_carga: str = "geral",
    tensao_v: float = 220.0,
    corrente_curto_kA: float = 3.0,
) -> dict:
    """
    Seleciona o disjuntor termomagnético conforme NBR 5410.

    Regra fundamental NBR 5410 item 6.3.2.2:
        I_projeto ≤ I_n_disjuntor ≤ I_z_cabo

    Onde:
        I_projeto      = corrente de projeto do circuito
        I_n_disjuntor  = corrente nominal do disjuntor
        I_z_cabo       = ampacidade do cabo selecionado

    Parâmetros
    ----------
    corrente_projeto  : corrente de dimensionamento do circuito (A)
    ampacidade_cabo   : ampacidade do cabo selecionado (A)
    tipo_carga        : 'resistiva', 'indutiva', 'motor', 'geral'
    tensao_v          : tensão do circuito (para verificação)
    corrente_curto_kA : corrente de curto disponível no ponto (kA)

    Retorna
    -------
    dict com disjuntor selecionado, curva e verificações
    """
    # ── Seleção da corrente nominal ───────────────────────────
    # Regra: I_n deve ser >= I_projeto e <= ampacidade do cabo
    disjuntor_selecionado = None

    for in_disj in DISJUNTORES_NOMINAIS:
        if in_disj >= corrente_projeto and in_disj <= ampacidade_cabo:
            disjuntor_selecionado = in_disj
            break

    # Se nenhum atende I_n ≤ ampacidade, pegar o imediatamente superior a I_projeto
    # e sinalizar que o cabo pode precisar ser aumentado
    cabo_adequado = True
    if disjuntor_selecionado is None:
        logger.warning(
            "Nenhum disjuntor padrão cabe entre I_projeto e ampacidade_cabo. "
            "Selecionando imediatamente acima de I_projeto (cabo pode precisar aumentar)."
        )
        cabo_adequado = False
        for in_disj in DISJUNTORES_NOMINAIS:
            if in_disj >= corrente_projeto:
                disjuntor_selecionado = in_disj
                break

    if disjuntor_selecionado is None:
        raise ValueError(
            f"Corrente {corrente_projeto:.2f}A excede todos os disjuntores disponíveis."
        )

    # ── Seleção da curva ──────────────────────────────────────
    curva = _selecionar_curva(tipo_carga)

    # ── Capacidade de interrupção ─────────────────────────────
    # Padrão mínimo para instalações residenciais/comerciais: 3kA
    # Industrial: 6kA ou superior
    capacidade_interrupcao = _selecionar_capacidade_interrupcao(corrente_curto_kA)

    # ── Verificação da regra NBR 5410 ─────────────────────────
    regra_nbr = (
        corrente_projeto <= disjuntor_selecionado <= ampacidade_cabo
    )

    logger.info(
        f"Disjuntor | In={disjuntor_selecionado}A | Curva={curva} | "
        f"Icu={capacidade_interrupcao}kA | "
        f"Regra NBR5410: {corrente_projeto}≤{disjuntor_selecionado}≤{ampacidade_cabo} → "
        f"{'OK' if regra_nbr else 'ATENÇÃO'}"
    )

    return {
        "corrente_nominal":         disjuntor_selecionado,
        "curva":                    curva,
        "curva_descricao":          CURVAS_DISJUNTOR[curva],
        "capacidade_interrupcao_kA": capacidade_interrupcao,
        "regra_nbr5410_atendida":   regra_nbr,
        "cabo_adequado":            cabo_adequado,
        "corrente_projeto":         round(corrente_projeto, 2),
        "ampacidade_cabo":          ampacidade_cabo,
        "verificacao": (
            f"{corrente_projeto:.1f}A ≤ {disjuntor_selecionado}A ≤ {ampacidade_cabo}A"
        ),
    }


def _selecionar_curva(tipo_carga: str) -> str:
    """
    Seleciona a curva de disparo conforme o tipo de carga.

    B → cargas resistivas puras (pouco pico de partida)
    C → uso geral (mais comum em residencial/comercial)
    D → motores e cargas com alto pico de partida
    """
    mapa = {
        "resistiva":  "B",
        "iluminacao": "B",
        "geral":      "C",
        "indutiva":   "C",
        "eletronica": "C",
        "motor":      "D",
        "compressor": "D",
        "bomba":      "D",
    }
    curva = mapa.get(tipo_carga.lower(), "C")
    logger.info(f"Curva selecionada: {curva} para carga tipo '{tipo_carga}'")
    return curva


def _selecionar_capacidade_interrupcao(corrente_curto_kA: float) -> float:
    """
    Define a capacidade de interrupção (Icu) mínima necessária.
    O disjuntor deve interromper a corrente de curto-circuito disponível no ponto.

    Valores comerciais comuns: 3, 6, 10, 15, 25, 36, 50 kA
    """
    capacidades_padrão = [3.0, 6.0, 10.0, 15.0, 25.0, 36.0, 50.0]
    for cap in capacidades_padrão:
        if cap >= corrente_curto_kA:
            return cap
    return 50.0   # máximo disponível
