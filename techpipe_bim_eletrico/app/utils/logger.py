"""
utils/logger.py — Sistema de logging centralizado
utils/validators.py — Validações de entrada de dados
"""

# ══════════════════════════════════════════════════════════════
# LOGGER
# ══════════════════════════════════════════════════════════════

import logging
import os
from datetime import datetime


def get_logger(nome: str) -> logging.Logger:
    """
    Retorna um logger configurado para o módulo informado.
    Salva logs em arquivo e exibe no terminal.

    Uso:
        logger = get_logger(__name__)
        logger.info("Mensagem")
        logger.warning("Aviso")
        logger.error("Erro")
    """
    logger = logging.getLogger(nome)

    if logger.handlers:
        return logger   # evita duplicar handlers

    logger.setLevel(logging.DEBUG)

    # ── Formato ──────────────────────────────────────────────
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Handler: Terminal ─────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    # ── Handler: Arquivo ──────────────────────────────────────
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(
        log_dir,
        f"techpipe_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# ══════════════════════════════════════════════════════════════
# VALIDATORS
# ══════════════════════════════════════════════════════════════

def validar_positivo(valor: float, nome: str) -> None:
    """Garante que o valor seja positivo."""
    if valor <= 0:
        raise ValueError(f"'{nome}' deve ser maior que zero. Recebido: {valor}")


def validar_intervalo(valor: float, nome: str, minimo: float, maximo: float) -> None:
    """Garante que o valor esteja no intervalo [minimo, maximo]."""
    if not minimo <= valor <= maximo:
        raise ValueError(
            f"'{nome}' deve estar entre {minimo} e {maximo}. Recebido: {valor}"
        )


def validar_sistema_eletrico(sistema: str) -> None:
    """Valida o sistema elétrico informado."""
    validos = ("monofasico", "bifasico", "trifasico")
    if sistema not in validos:
        raise ValueError(
            f"Sistema '{sistema}' inválido. Use: {validos}"
        )


def validar_material(material: str) -> None:
    """Valida o material do condutor."""
    validos = ("cobre", "aluminio")
    if material not in validos:
        raise ValueError(
            f"Material '{material}' inválido. Use: {validos}"
        )
