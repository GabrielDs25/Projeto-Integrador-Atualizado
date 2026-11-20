"""Baseline simples: aprova a resposta se contém alguma palavra-chave esperada.

Serve de comparação para o LLM juiz. É propositalmente ingênuo: não entende
negação ("não é 8") nem sinônimos fora da lista, e esses erros entram na
análise do trabalho.
"""

import re
import unicodedata


def normalizar(texto):
    """Minúsculas, sem acentos e com espaços simplificados."""
    if not texto:
        return ""
    sem_acentos = unicodedata.normalize("NFKD", texto)
    sem_acentos = "".join(c for c in sem_acentos if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acentos.lower()).strip()


def contem_palavra(texto_normalizado, palavra):
    """Procura a palavra-chave como termo inteiro (não como parte de outra palavra)."""
    alvo = re.escape(normalizar(palavra))
    return re.search(rf"(?<!\w){alvo}(?!\w)", texto_normalizado) is not None


def avaliar_baseline(resposta, palavras_chave):
    """Retorna True se a resposta contém ao menos uma palavra-chave."""
    texto = normalizar(resposta)
    if not texto:
        return False
    return any(contem_palavra(texto, palavra) for palavra in palavras_chave)
