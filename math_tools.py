"""
Real math computation using SymPy, so answers are exact rather than
LLM-guessed. Handles equations, expressions, calculus.
"""

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr


def solve_math(text: str) -> str:
    """
    Try to parse and solve a math expression or equation from natural text.
    Falls back gracefully if it can't parse anything.
    """
    x, y, z = sp.symbols('x y z')

    # crude cleanup: strip common filler words
    cleaned = (text.lower()
               .replace("solve", "")
               .replace("what is", "")
               .replace("calculate", "")
               .replace("?", "")
               .strip())

    try:
        if "=" in cleaned:
            left, right = cleaned.split("=", 1)
            eq = sp.Eq(parse_expr(left), parse_expr(right))
            result = sp.solve(eq)
            return f"{result}"
        else:
            expr = parse_expr(cleaned)
            result = sp.simplify(expr)
            return f"{result}"
    except Exception:
        return None  # signal caller to fall back to LLM-only reasoning


def derivative(expr_text: str, var: str = "x") -> str:
    v = sp.symbols(var)
    expr = parse_expr(expr_text)
    return str(sp.diff(expr, v))


def integral(expr_text: str, var: str = "x") -> str:
    v = sp.symbols(var)
    expr = parse_expr(expr_text)
    return str(sp.integrate(expr, v))