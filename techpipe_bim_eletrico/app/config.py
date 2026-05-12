"""
config.py — Configurações globais do sistema TechPipe BIM Elétrico
Centraliza todas as constantes, limites normativos e parâmetros padrão.
"""

# ─────────────────────────────────────────────
# RESISTIVIDADE DOS CONDUTORES (Ω·mm²/m) — NBR 5410
# ─────────────────────────────────────────────
RESISTIVIDADE = {
    "cobre":     0.01786,   # Cobre a 20°C
    "aluminio":  0.02941,   # Alumínio a 20°C
}

# ─────────────────────────────────────────────
# SISTEMAS ELÉTRICOS
# ─────────────────────────────────────────────
SISTEMAS_ELETRICOS = {
    "monofasico":  1.0,
    "bifasico":    1.414,
    "trifasico":   1.732,
}

# ─────────────────────────────────────────────
# LIMITES DE QUEDA DE TENSÃO — NBR 5410 (item 6.5)
# ─────────────────────────────────────────────
QUEDA_TENSAO_MAXIMA = {
    "circuito_final":        0.04,   # 4% para circuitos terminais
    "circuito_distribuicao": 0.02,   # 2% para circuitos de distribuição
    "total":                 0.07,   # 7% total da instalação
}

# ─────────────────────────────────────────────
# FATORES DE CORREÇÃO DE TEMPERATURA — NBR 5410 Tabela 41
# Base: 30°C, isolação PVC (70°C)
# ─────────────────────────────────────────────
FATORES_TEMPERATURA = {
    10: 1.22,
    15: 1.17,
    20: 1.12,
    25: 1.06,
    30: 1.00,   # temperatura de referência
    35: 0.94,
    40: 0.87,
    45: 0.79,
    50: 0.71,
    55: 0.61,
    60: 0.50,
}

# ─────────────────────────────────────────────
# FATORES DE CORREÇÃO DE AGRUPAMENTO — NBR 5410 Tabela 42
# Número de circuitos agrupados no mesmo conduíte/bandeja
# ─────────────────────────────────────────────
FATORES_AGRUPAMENTO = {
    1:  1.00,
    2:  0.80,
    3:  0.70,
    4:  0.65,
    5:  0.60,
    6:  0.57,
    7:  0.54,
    8:  0.52,
    9:  0.50,
    10: 0.48,
    12: 0.45,
    14: 0.43,
    16: 0.41,
    20: 0.38,
}

# ─────────────────────────────────────────────
# TABELA DE CABOS — Ampacidade base (A)
# Método B2: condutor em conduíte embutido na parede
# Isolação PVC, temperatura ambiente 30°C — NBR 5410 Tabela B.52.4
# ─────────────────────────────────────────────
CABOS_AMPACIDADE = {
    # seção (mm²): (cobre, aluminio)
    1.5:  (15.5,  None),
    2.5:  (21.0,  None),
    4.0:  (28.0,  None),
    6.0:  (36.0,  None),
    10.0: (50.0,  39.0),
    16.0: (68.0,  52.0),
    25.0: (89.0,  68.0),
    35.0: (111.0, 85.0),
    50.0: (134.0, 103.0),
    70.0: (171.0, 132.0),
    95.0: (207.0, 160.0),
    120.0:(239.0, 187.0),
    150.0:(272.0, 212.0),
    185.0:(310.0, 245.0),
    240.0:(364.0, 287.0),
}

# ─────────────────────────────────────────────
# TABELA DE CONDUÍTES — Diâmetro nominal (mm)
# Área interna útil e ocupação máxima (40% — NBR 5410)
# ─────────────────────────────────────────────
CONDUITS_DADOS = {
    # DN: área_interna_mm²
    16:  133.0,
    20:  201.0,
    25:  380.0,
    32:  572.0,
    40:  855.0,
    50:  1385.0,
    63:  2290.0,
    75:  3848.0,
    100: 6648.0,
}

OCUPACAO_MAXIMA_CONDUIT = 0.40   # 40% da área interna

# Seção transversal dos cabos por bitola (mm²) — valor real com isolação PVC
CABO_AREA_TOTAL = {
    1.5:   8.0,
    2.5:   11.0,
    4.0:   15.0,
    6.0:   20.0,
    10.0:  30.0,
    16.0:  43.0,
    25.0:  60.0,
    35.0:  78.0,
    50.0:  105.0,
    70.0:  140.0,
    95.0:  180.0,
    120.0: 220.0,
    150.0: 265.0,
    185.0: 320.0,
    240.0: 400.0,
}

# ─────────────────────────────────────────────
# DISJUNTORES — Correntes nominais padrão (A)
# ─────────────────────────────────────────────
DISJUNTORES_NOMINAIS = [
    6, 10, 16, 20, 25, 32, 40, 50, 63,
    80, 100, 125, 160, 200, 250, 315, 400,
]

# Curvas de disparo
CURVAS_DISJUNTOR = {
    "B": "Uso geral / resistivo — disparo entre 3x e 5x In",
    "C": "Uso geral / indutivo — disparo entre 5x e 10x In (mais comum)",
    "D": "Cargas com alto pico de partida (motores, transformadores)",
}

# ─────────────────────────────────────────────
# MÉTODOS DE INSTALAÇÃO — NBR 5410 Tabela 33
# ─────────────────────────────────────────────
METODOS_INSTALACAO = {
    "A1": "Condutor isolado em eletroduto embutido em parede térmica",
    "A2": "Cabo em eletroduto embutido em parede térmica",
    "B1": "Condutor isolado em eletroduto aparente",
    "B2": "Cabo em eletroduto aparente",
    "C":  "Cabo fixado diretamente na parede",
    "D":  "Cabo enterrado diretamente no solo",
    "E":  "Cabo ao ar livre em bandeja perfurada",
    "F":  "Cabo ao ar livre em bandeja não perfurada",
}

# ─────────────────────────────────────────────
# TIPOS DE CARGA
# ─────────────────────────────────────────────
TIPOS_CARGA = {
    "resistiva":    {"fp": 1.0,  "descricao": "Chuveiros, aquecedores, resistências"},
    "indutiva":     {"fp": 0.85, "descricao": "Motores, compressores, bombas"},
    "eletronica":   {"fp": 0.90, "descricao": "Computadores, inversores, fontes"},
    "iluminacao":   {"fp": 0.92, "descricao": "Luminárias fluorescentes e LED"},
    "mista":        {"fp": 0.85, "descricao": "Combinação de cargas"},
}
