import re
import ast

def decode_xor_obfuscated(code: str) -> str:
    """Статически декодирует XOR-обфусцированный код"""
    # Извлекаем ключевые компоненты через AST
    key = None
    data = None
    exec_alias = None
    result_var = None
    
    # Парсим код для извлечения переменных
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == '_':
                if isinstance(node.value, ast.List):
                    key = [e.n for e in node.value.elts]
            
            elif isinstance(target, ast.Name) and target.id == '___':
                if isinstance(node.value, ast.Name):
                    exec_alias = node.value.id
            
            elif isinstance(target, ast.Name) and target.id.startswith('_____'):
                result_var = target.id
    
    # Извлекаем данные из цикла for
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            if isinstance(node.iter, ast.Call) and node.iter.func.id == 'enumerate':
                if isinstance(node.iter.args[0], ast.List):
                    data = [e.n for e in node.iter.args[0].elts]
    
    # Проверяем что все компоненты найдены
    if not all([key, data, exec_alias, result_var]):
        raise ValueError("Не удалось извлечь все компоненты кода")
    
    # Эмулируем декодирование
    key_len = len(key)
    decoded_chars = []
    for idx, val in enumerate(data):
        decoded_char = chr(val ^ key[idx % key_len])
        decoded_chars.append(decoded_char)
    
    return ''.join(decoded_chars)

def save_and_analyze(decoded: str, filename: str = "decoded_result.py"):
    """Сохраняет результат и анализирует на наличие опасных конструкций"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(decoded)
    
    print(f"✅ Результат сохранен в {filename}")
    print("🔍 Анализ безопасности:")
    
    # Проверка опасных паттернов
    dangerous_patterns = [
        r"os\.system",
        r"subprocess\.",
        r"__import__\(",
        r"eval\(",
        r"exec\(",
        r"open\(",
        r"rm -rf",
        r"shutil\.rmtree",
        r"import\s+ctypes",
        r"\.so\b",
        r"dll",
        r"http\.(client|server)",
        r"socket\."
    ]
    
    warnings = 0
    for pattern in dangerous_patterns:
        if re.search(pattern, decoded):
            print(f"⚠️  Обнаружено: {pattern}")
            warnings += 1
    
    if warnings == 0:
        print("✅ Опасные конструкции не обнаружены")
    else:
        print(f"🚨 Обнаружено {warnings} потенциально опасных конструкций")
    
    # Проверка вложенной обфускации
    obfuscation_patterns = [
        r"base64\.b[0-9]+decode",
        r"exec\(",
        r"eval\(",
        r"compile\(",
        r"chr\(\d+\)",
        r"\.[a-z]{3,15}\("
    ]
    
    obf_count = 0
    for pattern in obfuscation_patterns:
        obf_count += len(re.findall(pattern, decoded))
    
    print(f"\nℹ️ Признаки вложенной обфускации: {obf_count} совпадений")
    
    if "exec(" in decoded or "eval(" in decoded:
        print("\n🔧 Рекомендация: Повторите процесс декодирования для вложенного кода")

# Основной процесс
if __name__ == "__main__":
    # Сохраните ваш код в этот файл
    INPUT_FILENAME = "decoded_result copy.py"
    
    with open(INPUT_FILENAME, "r", encoding="utf-8") as f:
        obfuscated_code = f.read()
    
    try:
        print("🔍 Декодирование XOR-обфускации...")
        decoded_code = decode_xor_obfuscated(obfuscated_code)
        
        print("✅ Успешно декодировано!")
        save_and_analyze(decoded_code)
        
        print("\n💡 Советы для анализа:")
        print("1. Откройте decoded_result.py в текстовом редакторе")
        print("2. Ищите строки, начинающиеся с 'import' для понимания зависимостей")
        print("3. Проверьте наличие главной функции или точки входа")
        print("4. Если обнаружена вложенная обфускация - повторите процесс")
        
    except Exception as e:
        print(f"🚨 Ошибка декодирования: {str(e)}")
        print("ℹ️ Возможные причины:")
        print("- Некорректное извлечение ключа или данных")
        print("- Измененный алгоритм обфускации")
        print("- Поврежденный исходный код")
        print("\n✉️ Пожалуйста, предоставьте больше контекста для дальнейшей помощи")