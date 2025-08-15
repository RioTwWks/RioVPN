import re

def eval_chr_expr(expr):
    # Пример: chr(0b1010000 + 0o24)
    try:
        return str(eval(expr))
    except Exception:
        return expr

def decode_chr_strings(code):
    # Находит все chr(...) выражения
    pattern = r"chr\([^\)]+\)"
    matches = re.findall(pattern, code)
    for m in matches:
        decoded = eval_chr_expr(m)
        code = code.replace(m, decoded)
    return code

with open("decompressed_code_decoded.py", "r", encoding="utf-8") as f:
    code = f.read()

decoded_code = decode_chr_strings(code)

with open("decompressed_code_fully_decoded.py", "w", encoding="utf-8") as f:
    f.write(decoded_code)