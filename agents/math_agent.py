"""
math_agent.py
-------------
Matematik sorularını yanıtlayan ajan.
Örnek: "12 * (3 + 4)" -> "84"

GÜVENLİK NOTU (önemli, müşteri bunu sorabilir):
Python'da hesaplama yapmak için akla ilk gelen şey eval() fonksiyonudur,
AMA eval() TEHLİKELİDİR: kullanıcı kötü niyetli kod yazarsa çalıştırır.
Bu yüzden burada Python'un 'ast' modülü ile GÜVENLİ bir hesaplayıcı yazdık:
sadece sayılara ve dört işlem gibi izin verilen işlemlere izin verir,
başka hiçbir kodu çalıştırmaz.
"""

import ast
import operator
import re

from .base_agent import BaseAgent


# İzin verilen matematik operatörleri. Bunların dışında hiçbir şey çalışmaz.
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,        # +
    ast.Sub: operator.sub,        # -
    ast.Mult: operator.mul,       # *
    ast.Div: operator.truediv,    # /
    ast.Pow: operator.pow,        # ** (üs alma)
    ast.Mod: operator.mod,        # % (mod)
    ast.USub: operator.neg,       # negatif sayı, örn -5
}


def _safe_eval(node):
    """Bir matematik ifadesini güvenli şekilde hesaplar (recursive).

    'ast' modülü ifadeyi bir ağaca çevirir; biz bu ağacı dolaşıp
    SADECE izin verdiğimiz işlemleri yaparız. Böylece kod enjeksiyonu
    imkânsız hale gelir.
    """
    if isinstance(node, ast.Constant):        # düz bir sayı, örn 5
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Sadece sayılar desteklenir.")
    if isinstance(node, ast.BinOp):           # iki taraflı işlem, örn 3 + 4
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError("Bu işleme izin verilmiyor.")
    if isinstance(node, ast.UnaryOp):         # tek taraflı işlem, örn -5
        operand = _safe_eval(node.operand)
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[op_type](operand)
        raise ValueError("Bu işleme izin verilmiyor.")
    raise ValueError("İfade çözümlenemedi.")


class MathAgent(BaseAgent):
    name = "math"

    # Bir mesajın matematik olup olmadığını anlamak için basit bir desen:
    # içinde rakam ve en az bir matematik operatörü varsa muhtemelen matematiktir.
    _MATH_PATTERN = re.compile(r"^[\d\s\+\-\*\/\(\)\.\%]+$")

    def can_handle(self, message: str) -> float:
        text = message.strip()
        # Mesaj tamamen sayı ve operatörlerden oluşuyor mu?
        if text and self._MATH_PATTERN.match(text):
            # Ve içinde en az bir operatör var mı? (yoksa sadece sayıdır)
            if any(op in text for op in "+-*/%"):
                return 0.95
        return 0.0

    def handle(self, message: str) -> str:
        try:
            # Mesajı ast ile ağaca çevir, sonra güvenli şekilde hesapla
            tree = ast.parse(message.strip(), mode="eval")
            result = _safe_eval(tree.body)
            return f"Sonuç: {result}"
        except ZeroDivisionError:
            return "Sıfıra bölme hatası: bir sayıyı sıfıra bölemezsin."
        except Exception:
            return "Bu matematik ifadesini çözemedim. Örn: 12 * (3 + 4)"
