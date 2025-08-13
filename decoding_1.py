import base64
import re
import ast

def decode_hex(hex_str):
    """Декодирует hex-строку с экранированными символами"""
    return bytes.fromhex(hex_str.replace(r'\x', '')).decode('utf-8')

def extract_b85_string(code):
    """Извлекает Base85 строку из кода"""
    # Ищем шаблон: _(b'...') или _(b"...")
    pattern = r'_\(\s*b([\'"])((?:[^\1]|\\.)*)\1\s*\)'
    match = re.search(pattern, code)
    if match:
        return match.group(2)
    return None

def decode_layers(input_file, output_file):
    with open(input_file, 'r') as f:
        code = f.read()

    # Шаг 1: Декодируем первый hex-слой
    hex_match = re.search(r'_\s*\(\s*[\'"](.+?)[\'"]\s*\)', code)
    if not hex_match:
        print("Hex-строка не найдена в коде")
        return

    hex_str = hex_match.group(1)
    decoded = decode_hex(hex_str)
    print(f"▶ Первый слой (hex) декодирован:\n{decoded[:200]}...\n")

    # Шаг 2: Извлекаем Base85 строку
    b85_str = extract_b85_string(decoded)
    if not b85_str:
        print("Base85 строка не найдена")
        return

    # Шаг 3: Декодируем Base85
    try:
        b85_decoded = base64.b85decode(b85_str).decode('utf-8')
        print(f"▶ Base85 слой декодирован:\n{b85_decoded[:200]}...\n")
        result = b85_decoded
    except Exception as e:
        print(f"Ошибка декодирования Base85: {e}")
        return

    # Шаг 4: Декодируем дополнительные слои
    layer_count = 2
    while True:
        if 'exec(' in result or 'eval(' in result:
            # Заменяем exec/eval на print для безопасного вывода
            cleaned = re.sub(r'(exec|eval)\s*\(', 'print(', result)
            try:
                # Пытаемся выполнить преобразованный код в песочнице
                compiled = ast.parse(cleaned, '<string>', 'exec')
                new_result = []
                for node in compiled.body:
                    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                        new_result.append(ast.unparse(node))
                result = '\n'.join(new_result)
                print(f"▶ Слой {layer_count} (exec/eval) преобразован:\n{result[:200]}...\n")
                layer_count += 1
            except:
                break
        else:
            break

    # Сохраняем результат
    with open(output_file, 'w') as f:
        f.write(result)
    print(f"✅ Декодирование завершено! Результат сохранен в {output_file}")
    print(f"🔍 Проверьте файл {output_file} перед запуском!")

if __name__ == "__main__":
    input_filename = "main.py"
    output_filename = "decoded_result.py"
    decode_layers(input_filename, output_filename)