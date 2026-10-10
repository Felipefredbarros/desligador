"""Regras do PIN: formato, geração e hash (PBKDF2-SHA256).

O config guarda só o hash, no formato `pbkdf2_sha256$<iteracoes>$<sal>$<hash>` (base64).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import string

PIN_MINIMO = 6
DIGITOS_PIN_GERADO = 8
# Recomendação da OWASP para PBKDF2-HMAC-SHA256; deixa cada tentativa lenta de propósito.
ITERACOES_PADRAO = 600_000
_ALGORITMO = "pbkdf2_sha256"


class PinInvalido(ValueError):
    """O PIN não segue as regras de formato."""


def validar_pin(pin: object) -> str:
    """Garante que o PIN tem só dígitos e pelo menos `PIN_MINIMO` caracteres."""
    if not (isinstance(pin, str) and pin.isascii() and pin.isdigit() and len(pin) >= PIN_MINIMO):
        raise PinInvalido(f"O PIN deve ter pelo menos {PIN_MINIMO} dígitos (só números).")
    return pin


def gerar_pin(digitos: int = DIGITOS_PIN_GERADO) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(digitos))


def _derivar(pin: str, sal: bytes, iteracoes: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), sal, iteracoes)


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode("ascii")


def gerar_hash(pin: str, iteracoes: int = ITERACOES_PADRAO) -> str:
    sal = secrets.token_bytes(16)
    return f"{_ALGORITMO}${iteracoes}${_b64(sal)}${_b64(_derivar(pin, sal, iteracoes))}"


def _decompor(hash_salvo: object) -> tuple[int, bytes, bytes] | None:
    if not isinstance(hash_salvo, str):
        return None
    try:
        algoritmo, iteracoes, sal, esperado = hash_salvo.split("$")
        if algoritmo != _ALGORITMO or int(iteracoes) < 1:
            return None
        return (
            int(iteracoes),
            base64.b64decode(sal, validate=True),
            base64.b64decode(esperado, validate=True),
        )
    except ValueError:  # inclui binascii.Error (base64 inválido)
        return None


def hash_valido(hash_salvo: object) -> bool:
    return _decompor(hash_salvo) is not None


def conferir(pin: object, hash_salvo: str) -> bool:
    """True se `pin` gera o mesmo hash. Comparação em tempo constante."""
    partes = _decompor(hash_salvo)
    if partes is None or not isinstance(pin, str):
        return False
    iteracoes, sal, esperado = partes
    return hmac.compare_digest(_derivar(pin, sal, iteracoes), esperado)
