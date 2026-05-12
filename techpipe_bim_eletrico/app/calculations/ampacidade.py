"""
calculations/ampacidade.py — Seleção de cabo por ampacidade
Escolhe a menor seção de cabo que suporte a corrente de dimensionamento.
NBR 5410 Tabela B.52.4 e seguintes.
"""

from app.config import CABOS_AMPACIDADE
from app.utils.logger import get_logger

logger = get_logger(__name__)


def selecionar_cabo(
    corrente_dimensionamento: float,
    material: str = "cobre",
    secao_minima: float = 1.5,
) -> dict:
    """
    Seleciona o cabo adequado por ampacidade.

    Lógica NBR 5410:
    - A corrente nominal do cabo deve ser ≥ corrente de dimensionamento
    - O cabo deve respeitar seção mínima por tipo de circuito
    - Material: cobre (padrão) ou alumínio (mínimo 10mm² para alumínio)

    Parâmetros
    ----------
    corrente_dimensionamento : corrente após aplicar todos os fatores de correção
    material                 : 'cobre' ou 'aluminio'
    secao_minima             : seção mínima obrigatória em mm² (padrão 1.5mm²)

    Retorna
    -------
    dict com cabo selecionado, ampacidade e margem de segurança
    """
    if material not in ("cobre", "aluminio"):
        raise ValueError("Material deve ser 'cobre' ou 'aluminio'.")

    idx_material = 0 if material == "cobre" else 1

    # Alumínio não existe abaixo de 10mm² — NBR 5410 item 6.2.3.1
    if material == "aluminio":
        secao_minima = max(secao_minima, 10.0)
        logger.info("Alumínio: seção mínima ajustada para 10mm²")

    secoes_ordenadas = sorted(CABOS_AMPACIDADE.keys())
    cabo_selecionado = None
    ampacidade_cabo = None

    for secao in secoes_ordenadas:
        # Respeita seção mínima
        if secao < secao_minima:
            continue

        ampacidade = CABOS_AMPACIDADE[secao][idx_material]

        # Alumínio pode não ter valor para seções pequenas
        if ampacidade is None:
            continue

        if ampacidade >= corrente_dimensionamento:
            cabo_selecionado = secao
            ampacidade_cabo = ampacidade
            break

    if cabo_selecionado is None:
        logger.error(
            f"Nenhum cabo {material} suporta {corrente_dimensionamento:.2f}A. "
            f"Verificar projeto (paralelo de cabos necessário)."
        )
        raise ValueError(
            f"Corrente {corrente_dimensionamento:.2f}A excede todos os cabos disponíveis "
            f"em {material}. Considere usar cabos em paralelo."
        )

    margem_seguranca = ((ampacidade_cabo - corrente_dimensionamento) / ampacidade_cabo) * 100

    logger.info(
        f"Cabo selecionado: {cabo_selecionado}mm² {material} | "
        f"Ampacidade={ampacidade_cabo}A | "
        f"Margem={margem_seguranca:.1f}%"
    )

    return {
        "secao_mm2":                 cabo_selecionado,
        "material":                  material,
        "ampacidade_cabo":           ampacidade_cabo,
        "corrente_dimensionamento":  round(corrente_dimensionamento, 2),
        "margem_seguranca_pct":      round(margem_seguranca, 1),
        "adequado":                  True,
    }


def verificar_cabo_existente(
    secao_mm2: float,
    corrente_dimensionamento: float,
    material: str = "cobre",
) -> dict:
    """
    Verifica se um cabo já definido no projeto suporta a corrente.
    Útil para validação de projetos existentes.

    Retorna
    -------
    dict com resultado da verificação e status (aprovado/reprovado)
    """
    if secao_mm2 not in CABOS_AMPACIDADE:
        raise ValueError(f"Seção {secao_mm2}mm² não está nas tabelas. Verifique o valor.")

    idx_material = 0 if material == "cobre" else 1
    ampacidade = CABOS_AMPACIDADE[secao_mm2][idx_material]

    if ampacidade is None:
        raise ValueError(f"Cabo {material} não disponível em {secao_mm2}mm².")

    aprovado = ampacidade >= corrente_dimensionamento
    margem = ((ampacidade - corrente_dimensionamento) / ampacidade) * 100

    status = "APROVADO" if aprovado else "REPROVADO"
    logger.info(
        f"Verificação cabo {secao_mm2}mm² {material}: {status} | "
        f"Ampacidade={ampacidade}A | I_dim={corrente_dimensionamento}A | Margem={margem:.1f}%"
    )

    return {
        "secao_mm2":                secao_mm2,
        "material":                 material,
        "ampacidade_cabo":          ampacidade,
        "corrente_dimensionamento": round(corrente_dimensionamento, 2),
        "aprovado":                 aprovado,
        "margem_pct":               round(margem, 1),
        "status":                   status,
    }
