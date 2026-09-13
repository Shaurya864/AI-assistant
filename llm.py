"""
Wrapper around your local Ollama instance.
Handles talking to the LLM, with model routing (general / code / math).
"""

import requests
import config


def ask_llm(prompt: str, model: str = None, system: str = None) -> str:
    """Send a prompt to the local Ollama model and return the text response."""
    model = model or config.GENERAL_MODEL
    system = system or config.SYSTEM_PROMPT

    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
    }

    try:
        response = requests.post(config.OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return ("I can't reach Ollama. Make sure it's installed and running "
                "(try `ollama serve` in a terminal, or just open the Ollama app).")
    except Exception as e:
        return f"Something went wrong talking to the model: {e}"


def ask_code(prompt: str) -> str:
    """Route coding questions to the code-specialist model."""
    system = (config.SYSTEM_PROMPT +
              "\nYou are especially skilled at writing clean, correct code. "
              "When asked for code, return a working code block with brief explanation.")
    return ask_llm(prompt, model=config.CODE_MODEL, system=system)


def ask_math_explanation(problem: str, computed_result: str) -> str:
    """Ask the LLM to explain a result that SymPy already computed."""
    prompt = (f"The math problem was: {problem}\n"
              f"The computed answer is: {computed_result}\n"
              "Briefly explain the steps to get there, in plain language.")
    return ask_llm(prompt, model=config.MATH_MODEL)