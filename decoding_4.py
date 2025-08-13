import re

def decode_xor(encoded_data: bytes) -> str:
    """Декодирует данные с помощью XOR по заданному ключу"""
    # Статический ключ из вашего кода
    key = [98, 158, 62, 139, 6, 226, 6, 25, 8, 143, 59, 194, 237, 65, 113, 53, 39, 186, 172, 240, 
           173, 122, 22, 21, 135, 126, 190, 227, 56, 187, 100, 224, 226, 67, 139, 24, 254, 103, 232, 125]
    
    # Применяем XOR-декодирование
    decoded_bytes = bytes(
        byte ^ key[index % len(key)] 
        for index, byte in enumerate(encoded_data)
    )
    
    # Пробуем декодировать как строку
    try:
        return decoded_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return decoded_bytes.hex()  # Возвращаем hex если не текст

def analyze_and_extract(encoded_data: bytes):
    """Анализирует и декодирует данные"""
    decoded = decode_xor(encoded_data)
    
    print("🔍 Результат декодирования:")
    if len(decoded) > 500:
        print(decoded[:300] + "..." + decoded[-100:])
    else:
        print(decoded)
    
    print("\n🔎 Анализ содержимого:")
    
    # Проверка на вложенный код
    if "exec(" in decoded or "eval(" in decoded:
        print("⚠️  Обнаружены вложенные exec/eval - возможна многослойная обфускация")
        
    # Проверка на опасные команды
    dangerous_patterns = {
        "os.system": "Вызовы системных команд",
        "subprocess": "Запуск внешних процессов",
        "__import__": "Динамический импорт модулей",
        "open(": "Работа с файловой системой",
        "http": "Сетевые операции",
        "socket": "Сетевые сокеты",
        "rm -rf": "Опасные системные команды"
    }
    
    found_dangers = []
    for pattern, description in dangerous_patterns.items():
        if pattern in decoded:
            found_dangers.append(f"• {description} ({pattern})")
    
    if found_dangers:
        print("🚨 Обнаружены потенциально опасные конструкции:")
        print("\n".join(found_dangers))
    else:
        print("✅ Потенциально опасные конструкции не обнаружены")
    
    # Проверка на следующую стадию обфускации
    obfuscation_patterns = [
        r"\\x[0-9a-f]{2}",  # HEX-последовательности
        r"base64\.b[0-9]+decode",  # Base64
        r"exec\s*\(",  # Вызовы exec
        r"eval\s*\(",  # Вызовы eval
        r"lambda\s+\w+:"  # Лямбда-функции
    ]
    
    found_obfuscation = []
    for pattern in obfuscation_patterns:
        if re.search(pattern, decoded):
            found_obfuscation.append(f"• {pattern}")
    
    if found_obfuscation:
        print("\n🔧 Признаки дополнительной обфускации:")
        print("\n".join(found_obfuscation))
    else:
        print("\nℹ️ Признаки дополнительной обфускации не обнаружены")

# Как использовать:
# 1. Найдите в вашем коде вызов лямбда-функции:
#    например: decoded_data = Nvm8L6FkudRf(b'\x12\x45\xab...')
# 2. Извлеките байтовую строку из аргумента
# 3. Вызовите функцию анализа:

# Пример вызова:
if __name__ == "__main__":
    # Закодированные данные из вашего кода (пример)
    # ВАЖНО: замените на реальные данные из вызова лямбды!
    encoded_data = b'\x14\xfbP\xfd'
    
    analyze_and_extract(encoded_data)
    
    # Для сохранения в файл
    """decoded = decode_xor(encoded_data)
    with open("decoded_stage.py", "w") as f:
        f.write(decoded if isinstance(decoded, str) else decoded.decode('latin1'))
    print("\n💾 Результат сохранен в decoded_stage.py")"""