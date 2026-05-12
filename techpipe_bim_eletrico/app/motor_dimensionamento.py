"""
motor_dimensionamento.py — Motor principal do sistema TechPipe
Orquestra todos os módulos de cálculo em um fluxo único e completo.
Este é o coração do sistema — tudo passa por aqui.
"""

from app.calculations.corrente import calcular_corrente
from app.calculations.fatores_correcao import aplicar_fatores_correcao
from app.calculations.ampacidade import selecionar_cabo
from app.calculations.queda_tensao import calcular_queda_tensao, secao_minima_para_queda
from app.calculations.disjuntores import selecionar_disjuntor
from app.calculations.conduites import dimensionar_conduit_completo
from app.utils.logger import get_logger

logger = get_logger(__name__)


def dimensionar_circuito(
    # ── Parâmetros elétricos ───────────────────────────────────
    potencia_w: float,
    tensao_v: float,
    sistema: str = "monofasico",
    fator_potencia: float = 1.0,
    fator_demanda: float = 1.0,
    fator_simultaneidade: float = 1.0,
    # ── Parâmetros da instalação ───────────────────────────────
    distancia_m: float = 10.0,
    temperatura_ambiente: float = 30.0,
    numero_circuitos_agrupados: int = 1,
    # ── Parâmetros do condutor ─────────────────────────────────
    material: str = "cobre",
    secao_minima_mm2: float = 1.5,
    queda_maxima_pct: float = 4.0,
    # ── Parâmetros do conduíte ─────────────────────────────────
    tipo_conduit: str = "PVC_rigido",
    com_neutro: bool = True,
    com_terra: bool = True,
    # ── Parâmetros do disjuntor ───────────────────────────────
    tipo_carga: str = "geral",
    corrente_curto_kA: float = 3.0,
) -> dict:
    """
    Dimensiona um circuito elétrico completo conforme NBR 5410.

    Fluxo interno:
        1. Calcular corrente de projeto
        2. Aplicar fatores de correção (temperatura + agrupamento)
        3. Selecionar cabo por ampacidade
        4. Verificar queda de tensão — aumentar cabo se necessário
        5. Selecionar disjuntor
        6. Dimensionar conduíte

    Retorna
    -------
    dict completo com todos os resultados, verificações e recomendações.
    """
    logger.info("=" * 60)
    logger.info("INÍCIO DO DIMENSIONAMENTO — TechPipe BIM Elétrico")
    logger.info(
        f"Entrada | P={potencia_w}W | V={tensao_v}V | sistema={sistema} | "
        f"L={distancia_m}m | T={temperatura_ambiente}°C | "
        f"agrup={numero_circuitos_agrupados}"
    )

    # ─────────────────────────────────────────────────────────
    # ETAPA 1 — Corrente de projeto
    # ─────────────────────────────────────────────────────────
    logger.info("ETAPA 1: Calculando corrente de projeto...")
    res_corrente = calcular_corrente(
        potencia_w=potencia_w,
        tensao_v=tensao_v,
        sistema=sistema,
        fator_potencia=fator_potencia,
        fator_demanda=fator_demanda,
        fator_simultaneidade=fator_simultaneidade,
    )
    corrente_projeto = res_corrente["corrente_projeto"]

    # ─────────────────────────────────────────────────────────
    # ETAPA 2 — Fatores de correção
    # ─────────────────────────────────────────────────────────
    logger.info("ETAPA 2: Aplicando fatores de correção...")
    res_fatores = aplicar_fatores_correcao(
        corrente_projeto=corrente_projeto,
        temperatura_ambiente=temperatura_ambiente,
        numero_circuitos=numero_circuitos_agrupados,
    )
    corrente_dimensionamento = res_fatores["corrente_final"]

    # ─────────────────────────────────────────────────────────
    # ETAPA 3 — Seleção do cabo por ampacidade
    # ─────────────────────────────────────────────────────────
    logger.info("ETAPA 3: Selecionando cabo por ampacidade...")
    res_cabo = selecionar_cabo(
        corrente_dimensionamento=corrente_dimensionamento,
        material=material,
        secao_minima=secao_minima_mm2,
    )
    secao_escolhida = res_cabo["secao_mm2"]

    # ─────────────────────────────────────────────────────────
    # ETAPA 4 — Verificar queda de tensão
    # Se reprovar, aumentar o cabo
    # ─────────────────────────────────────────────────────────
    logger.info("ETAPA 4: Verificando queda de tensão...")
    res_queda = calcular_queda_tensao(
        corrente_a=corrente_projeto,
        distancia_m=distancia_m,
        secao_mm2=secao_escolhida,
        tensao_v=tensao_v,
        material=material,
        sistema=sistema,
    )

    cabo_aumentado_por_queda = False

    if not res_queda["aprovado"]:
        logger.warning(
            f"Queda de tensão {res_queda['queda_tensao_pct']:.2f}% excede {queda_maxima_pct}%. "
            "Calculando seção mínima para queda de tensão..."
        )

        res_secao_queda = secao_minima_para_queda(
            corrente_a=corrente_projeto,
            distancia_m=distancia_m,
            tensao_v=tensao_v,
            queda_maxima_pct=queda_maxima_pct,
            material=material,
            sistema=sistema,
        )

        nova_secao = res_secao_queda["secao_normalizada_mm2"]

        if nova_secao and nova_secao > secao_escolhida:
            logger.info(
                f"Cabo aumentado de {secao_escolhida}mm² para {nova_secao}mm² "
                f"por exigência de queda de tensão."
            )
            secao_escolhida = nova_secao
            cabo_aumentado_por_queda = True

            # Recalcular queda com novo cabo
            res_queda = calcular_queda_tensao(
                corrente_a=corrente_projeto,
                distancia_m=distancia_m,
                secao_mm2=secao_escolhida,
                tensao_v=tensao_v,
                material=material,
                sistema=sistema,
            )

            # Atualizar info do cabo
            from app.calculations.ampacidade import verificar_cabo_existente
            res_cabo_verificado = verificar_cabo_existente(
                secao_mm2=secao_escolhida,
                corrente_dimensionamento=corrente_dimensionamento,
                material=material,
            )
            res_cabo = {
                **res_cabo,
                "secao_mm2":            secao_escolhida,
                "ampacidade_cabo":      res_cabo_verificado["ampacidade_cabo"],
                "motivo_aumento":       "queda de tensão",
            }

    # ─────────────────────────────────────────────────────────
    # ETAPA 5 — Disjuntor
    # ─────────────────────────────────────────────────────────
    logger.info("ETAPA 5: Dimensionando disjuntor...")
    res_disjuntor = selecionar_disjuntor(
        corrente_projeto=corrente_projeto,
        ampacidade_cabo=res_cabo["ampacidade_cabo"],
        tipo_carga=tipo_carga,
        tensao_v=tensao_v,
        corrente_curto_kA=corrente_curto_kA,
    )

    # ─────────────────────────────────────────────────────────
    # ETAPA 6 — Conduíte
    # ─────────────────────────────────────────────────────────
    logger.info("ETAPA 6: Dimensionando conduíte...")
    res_conduit = dimensionar_conduit_completo(
        secao_mm2=secao_escolhida,
        sistema=sistema,
        com_neutro=com_neutro,
        com_terra=com_terra,
        tipo_conduit=tipo_conduit,
    )

    # ─────────────────────────────────────────────────────────
    # RESULTADO FINAL
    # ─────────────────────────────────────────────────────────
    resultado = {
        # ── Entradas ──────────────────────────────────────────
        "entrada": {
            "potencia_w":                potencia_w,
            "tensao_v":                  tensao_v,
            "sistema":                   sistema,
            "fator_potencia":            fator_potencia,
            "distancia_m":               distancia_m,
            "temperatura_ambiente":      temperatura_ambiente,
            "numero_circuitos_agrupados": numero_circuitos_agrupados,
            "material":                  material,
            "tipo_carga":                tipo_carga,
        },

        # ── Correntes ─────────────────────────────────────────
        "correntes": {
            "corrente_nominal_a":         res_corrente["corrente_nominal"],
            "corrente_projeto_a":         res_corrente["corrente_projeto"],
            "corrente_dimensionamento_a": corrente_dimensionamento,
            "fator_temperatura":          res_fatores["fator_temperatura"],
            "fator_agrupamento":          res_fatores["fator_agrupamento"],
            "fator_combinado":            res_fatores["fator_combinado"],
        },

        # ── Cabo ──────────────────────────────────────────────
        "cabo": {
            "secao_mm2":             secao_escolhida,
            "material":              material,
            "ampacidade_a":          res_cabo["ampacidade_cabo"],
            "margem_seguranca_pct":  res_cabo.get("margem_seguranca_pct"),
            "aumentado_por_queda":   cabo_aumentado_por_queda,
        },

        # ── Queda de tensão ───────────────────────────────────
        "queda_tensao": {
            "queda_v":          res_queda["queda_tensao_v"],
            "queda_pct":        res_queda["queda_tensao_pct"],
            "tensao_residual_v": res_queda["tensao_residual_v"],
            "limite_pct":       res_queda["limite_normativo_pct"],
            "aprovado":         res_queda["aprovado"],
            "status":           res_queda["status"],
        },

        # ── Disjuntor ─────────────────────────────────────────
        "disjuntor": {
            "corrente_nominal_a":        res_disjuntor["corrente_nominal"],
            "curva":                     res_disjuntor["curva"],
            "capacidade_interrupcao_kA": res_disjuntor["capacidade_interrupcao_kA"],
            "regra_nbr5410_atendida":    res_disjuntor["regra_nbr5410_atendida"],
            "verificacao":               res_disjuntor["verificacao"],
        },

        # ── Conduíte ──────────────────────────────────────────
        "conduit": {
            "dn_mm":              res_conduit["dn_mm"],
            "tipo":               res_conduit["tipo"],
            "tipo_descricao":     res_conduit["tipo_descricao"],
            "qtd_condutores":     res_conduit["qtd_condutores"],
            "ocupacao_pct":       res_conduit["ocupacao_real_pct"],
            "aprovado":           res_conduit["aprovado"],
        },

        # ── Status geral ──────────────────────────────────────
        "status_geral": _avaliar_status_geral(res_queda, res_disjuntor, res_conduit),
    }

    logger.info("FIM DO DIMENSIONAMENTO")
    logger.info("=" * 60)

    return resultado


def _avaliar_status_geral(res_queda, res_disjuntor, res_conduit) -> dict:
    """Avalia o status geral do dimensionamento."""
    alertas = []

    if not res_queda["aprovado"]:
        alertas.append(f"Queda de tensão: {res_queda['queda_tensao_pct']:.2f}% excede limite")

    if not res_disjuntor["regra_nbr5410_atendida"]:
        alertas.append("Regra NBR 5410 do disjuntor não atendida — revisar cabo")

    if not res_conduit["aprovado"]:
        alertas.append(f"Ocupação do conduíte {res_conduit['ocupacao_real_pct']}% excede 40%")

    aprovado = len(alertas) == 0

    return {
        "aprovado": aprovado,
        "status":   "APROVADO" if aprovado else "ATENÇÃO — REVISAR",
        "alertas":  alertas,
    }
