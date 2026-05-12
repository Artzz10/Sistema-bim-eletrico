"""
main.py — Interface terminal — Fase 1 do Roadmap TechPipe
Permite testar o motor de cálculos sem nenhuma dependência de Revit.
"""

import sys
import os

# Garante que o Python encontra os módulos do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.motor_dimensionamento import dimensionar_circuito
from app.config import SISTEMAS_ELETRICOS, TIPOS_CARGA, METODOS_INSTALACAO


# ──────────────────────────────────────────────────────────────
# HELPERS DE FORMATAÇÃO
# ──────────────────────────────────────────────────────────────

SEPARADOR = "═" * 60
LINHA = "─" * 60


def cabecalho():
    print(f"\n{SEPARADOR}")
    print("  TechPipe BIM Elétrico — Motor de Dimensionamento")
    print("  Norma: NBR 5410 | Fase 1 — Terminal")
    print(SEPARADOR)


def imprimir_resultado(r: dict):
    """Exibe o resultado do dimensionamento de forma clara e organizada."""

    print(f"\n{SEPARADOR}")
    print("  RESULTADO DO DIMENSIONAMENTO")
    print(SEPARADOR)

    # ── Correntes ─────────────────────────────────────────────
    print(f"\n{'CORRENTES':}")
    print(LINHA)
    c = r["correntes"]
    print(f"  Corrente nominal:          {c['corrente_nominal_a']:.2f} A")
    print(f"  Corrente de projeto:       {c['corrente_projeto_a']:.2f} A")
    print(f"  Fator temperatura:         {c['fator_temperatura']:.4f}")
    print(f"  Fator agrupamento:         {c['fator_agrupamento']:.4f}")
    print(f"  Fator combinado:           {c['fator_combinado']:.4f}")
    print(f"  Corrente dimensionamento:  {c['corrente_dimensionamento_a']:.2f} A")

    # ── Cabo ──────────────────────────────────────────────────
    print(f"\n{'CABO SELECIONADO':}")
    print(LINHA)
    cabo = r["cabo"]
    motivo_extra = " (aumentado p/ queda de tensão)" if cabo["aumentado_por_queda"] else ""
    print(f"  Bitola:                    {cabo['secao_mm2']} mm²{motivo_extra}")
    print(f"  Material:                  {cabo['material'].capitalize()}")
    print(f"  Ampacidade:                {cabo['ampacidade_a']} A")
    if cabo["margem_seguranca_pct"] is not None:
        print(f"  Margem de segurança:       {cabo['margem_seguranca_pct']:.1f}%")

    # ── Queda de tensão ───────────────────────────────────────
    print(f"\n{'QUEDA DE TENSÃO':}")
    print(LINHA)
    qt = r["queda_tensao"]
    status_qt = "✓ OK" if qt["aprovado"] else "✗ REPROVADO"
    print(f"  Queda de tensão:           {qt['queda_v']:.3f} V  ({qt['queda_pct']:.2f}%)")
    print(f"  Tensão residual:           {qt['tensao_residual_v']:.1f} V")
    print(f"  Limite NBR 5410:           {qt['limite_pct']:.0f}%")
    print(f"  Status:                    {status_qt} — {qt['status']}")

    # ── Disjuntor ─────────────────────────────────────────────
    print(f"\n{'DISJUNTOR':}")
    print(LINHA)
    disj = r["disjuntor"]
    print(f"  Corrente nominal:          {disj['corrente_nominal_a']} A")
    print(f"  Curva:                     {disj['curva']}")
    print(f"  Cap. de interrupção:       {disj['capacidade_interrupcao_kA']} kA")
    print(f"  Regra NBR 5410:            {disj['verificacao']}")

    # ── Conduíte ──────────────────────────────────────────────
    print(f"\n{'CONDUÍTE':}")
    print(LINHA)
    ct = r["conduit"]
    status_ct = "✓ OK" if ct["aprovado"] else "✗ REPROVADO"
    print(f"  Diâmetro nominal:          DN{ct['dn_mm']} mm")
    print(f"  Tipo:                      {ct['tipo_descricao']}")
    print(f"  Quantidade de condutores:  {ct['qtd_condutores']}")
    print(f"  Ocupação:                  {ct['ocupacao_pct']:.1f}% (limite 40%) — {status_ct}")

    # ── Status geral ──────────────────────────────────────────
    print(f"\n{'STATUS GERAL':}")
    print(LINHA)
    sg = r["status_geral"]
    simbolo = "✓" if sg["aprovado"] else "✗"
    print(f"  {simbolo} {sg['status']}")
    if sg["alertas"]:
        print("  Alertas:")
        for alerta in sg["alertas"]:
            print(f"    ▸ {alerta}")

    print(f"\n{SEPARADOR}\n")


# ──────────────────────────────────────────────────────────────
# MENUS DE ENTRADA
# ──────────────────────────────────────────────────────────────

def solicitar_float(mensagem: str, minimo: float = 0.0) -> float:
    while True:
        try:
            valor = float(input(f"  {mensagem}: "))
            if valor <= minimo:
                print(f"  ⚠ Valor deve ser maior que {minimo}. Tente novamente.")
                continue
            return valor
        except ValueError:
            print("  ⚠ Digite um número válido.")


def solicitar_opcao(mensagem: str, opcoes: dict) -> str:
    print(f"\n  {mensagem}")
    for chave, descricao in opcoes.items():
        print(f"    [{chave}] {descricao}")
    while True:
        escolha = input("  Escolha: ").strip().lower()
        if escolha in opcoes:
            return escolha
        print(f"  ⚠ Opção inválida. Escolha entre: {list(opcoes.keys())}")


def solicitar_int(mensagem: str, minimo: int = 1) -> int:
    while True:
        try:
            valor = int(input(f"  {mensagem}: "))
            if valor < minimo:
                print(f"  ⚠ Valor deve ser maior ou igual a {minimo}.")
                continue
            return valor
        except ValueError:
            print("  ⚠ Digite um número inteiro válido.")


def solicitar_sim_nao(mensagem: str, padrao: bool = True) -> bool:
    opcao = "S/n" if padrao else "s/N"
    while True:
        resp = input(f"  {mensagem} [{opcao}]: ").strip().lower()
        if resp == "" :
            return padrao
        if resp in ("s", "sim", "y", "yes"):
            return True
        if resp in ("n", "nao", "não", "no"):
            return False
        print("  ⚠ Responda S ou N.")


# ──────────────────────────────────────────────────────────────
# FLUXO PRINCIPAL
# ──────────────────────────────────────────────────────────────

def main():
    cabecalho()

    print("\n  → Insira os dados do circuito:\n")

    # Potência e tensão
    potencia_w = solicitar_float("Potência total instalada (W)")
    tensao_v   = solicitar_float("Tensão do circuito (V)", minimo=0.0)

    # Sistema elétrico
    sistema = solicitar_opcao(
        "Sistema elétrico:",
        {"monofasico": "Monofásico  | I = P / V",
         "bifasico":   "Bifásico    | I = P / (V × 1.414)",
         "trifasico":  "Trifásico   | I = P / (V × 1.732)"},
    )

    # Tipo de carga
    tipo_carga = solicitar_opcao(
        "Tipo de carga:",
        {k: v["descricao"] for k, v in TIPOS_CARGA.items()},
    )
    from app.config import TIPOS_CARGA as TC
    fator_potencia = TC[tipo_carga]["fp"]
    print(f"  ℹ Fator de potência automático: fp={fator_potencia}")

    # Distância
    distancia_m = solicitar_float("Distância do circuito (m)")

    # Temperatura
    temperatura = solicitar_float("Temperatura ambiente (°C)", minimo=-10.0)

    # Agrupamento
    agrupamento = solicitar_int("Quantidade de circuitos no mesmo conduíte", minimo=1)

    # Material
    material = solicitar_opcao(
        "Material do condutor:",
        {"cobre": "Cobre (padrão — seção mínima 1.5mm²)",
         "aluminio": "Alumínio (seção mínima 10mm²)"},
    )

    # Tipo de conduíte
    tipo_conduit = solicitar_opcao(
        "Tipo de conduíte:",
        {"PVC_rigido":      "PVC Rígido (uso em parede/laje)",
         "PVC_flexivel":    "PVC Flexível corrugado (forro/embutido)",
         "aco_galvanizado": "Aço Galvanizado (industrial)",
         "PEAD":            "PEAD (subterrâneo)"},
    )

    # Neutro e terra
    com_neutro = solicitar_sim_nao("Incluir condutor neutro?", padrao=True)
    com_terra  = solicitar_sim_nao("Incluir condutor de proteção (PE/terra)?", padrao=True)

    # ── Executar dimensionamento ───────────────────────────────
    print(f"\n{LINHA}")
    print("  Calculando...")
    print(LINHA)

    try:
        resultado = dimensionar_circuito(
            potencia_w=potencia_w,
            tensao_v=tensao_v,
            sistema=sistema,
            fator_potencia=fator_potencia,
            distancia_m=distancia_m,
            temperatura_ambiente=temperatura,
            numero_circuitos_agrupados=agrupamento,
            material=material,
            tipo_conduit=tipo_conduit,
            com_neutro=com_neutro,
            com_terra=com_terra,
            tipo_carga=tipo_carga,
        )

        imprimir_resultado(resultado)

    except ValueError as e:
        print(f"\n  ✗ Erro de validação: {e}\n")
    except Exception as e:
        print(f"\n  ✗ Erro inesperado: {e}\n")
        raise

    # ── Repetir? ──────────────────────────────────────────────
    if solicitar_sim_nao("\nDimensionar outro circuito?", padrao=True):
        main()
    else:
        print("\n  TechPipe BIM Elétrico — Encerrado.\n")


if __name__ == "__main__":
    main()
