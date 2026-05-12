# TechPipe BIM Elétrico

Sistema profissional de dimensionamento elétrico integrado ao Revit.
Norma base: **NBR 5410** | Python + pyRevit + Revit API

## Como rodar (Fase 1 — Terminal)

```bash
cd techpipe_bim_eletrico
python app/main.py
```

## Estrutura

```
app/
├── main.py                      ← Interface terminal (Fase 1)
├── config.py                    ← Tabelas e constantes normativas
├── motor_dimensionamento.py     ← Orquestrador principal
│
├── calculations/
│   ├── corrente.py              ← Cálculo de corrente (mono/bi/tri)
│   ├── fatores_correcao.py      ← Temperatura + Agrupamento NBR 5410
│   ├── ampacidade.py            ← Seleção de cabo
│   ├── queda_tensao.py          ← ΔV e seção mínima
│   ├── disjuntores.py           ← Dimensionamento de disjuntores
│   └── conduites.py             ← Dimensionamento de conduítes
│
└── utils/
    └── logger.py                ← Logger + Validators
```

## Exemplo de uso via código

```python
from app.motor_dimensionamento import dimensionar_circuito

resultado = dimensionar_circuito(
    potencia_w=5500,
    tensao_v=220,
    sistema='monofasico',
    distancia_m=40,
    temperatura_ambiente=35,
    tipo_carga='resistiva',
)
print(resultado['cabo']['secao_mm2'])     # → 6.0
print(resultado['disjuntor']['corrente_nominal_a'])  # → 25
print(resultado['conduit']['dn_mm'])      # → 20
```

## Roadmap

- [x] Fase 1 — Motor de cálculos + Terminal
- [ ] Fase 2 — Interface gráfica Python (Tkinter/WPF)
- [ ] Fase 3 — Banco de dados SQLite
- [ ] Fase 4 — Integração pyRevit + Revit API
- [ ] Fase 5 — Geração automática de conduítes no BIM
- [ ] Fase 6 — Relatório PDF (ReportLab)
