import logging
import re

logging.basicConfig(level=logging.DEBUG, filename='decode.log', encoding='utf-8', filemode='a')

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
    
    logging.debug(f"🔍 Результат декодирования:")
    if len(decoded) > 500:
        logging.debug(f"{decoded[:300]}...{decoded[-100:]}")
    else:
        logging.debug(f"{decoded}")
    
    logging.debug(f"\n🔎 Анализ содержимого:")
    
    # Проверка на вложенный код
    if "exec(" in decoded or "eval(" in decoded:
        logging.debug(f"⚠️  Обнаружены вложенные exec/eval - возможна многослойная обфускация")
        
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
        logging.debug(f"🚨 Обнаружены потенциально опасные конструкции:")
        logging.debug(f"\n".join(found_dangers))
    else:
        logging.debug(f"✅ Потенциально опасные конструкции не обнаружены")
    
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
        logging.debug(f"\n🔧 Признаки дополнительной обфускации:")
        logging.debug(f"\n".join(found_obfuscation))
    else:
        logging.debug(f"\nℹ️ Признаки дополнительной обфускации не обнаружены")

# Как использовать:
# 1. Найдите в вашем коде вызов лямбда-функции:
#    например: decoded_data = Nvm8L6FkudRf(b'\x12\x45\xab...')
# 2. Извлеките байтовую строку из аргумента
# 3. Вызовите функцию анализа:

# Пример вызова:
"""if __name__ == "__main__":
    # Закодированные данные из вашего кода (пример)
    # ВАЖНО: замените на реальные данные из вызова лямбды!
    encoded_data = b'\x14\xfbP\xfd'
    
    analyze_and_extract(encoded_data)
    
    # Для сохранения в файл
    decoded = decode_xor(encoded_data)
    with open("decoded_stage.py", "w") as f:
        f.write(decoded if isinstance(decoded, str) else decoded.decode('latin1'))
    logging.debug(f"\n💾 Результат сохранен в decoded_stage.py")"""




def extract_and_decode_all(filename):
    with open(filename, "r", encoding="utf-8") as f:
        code = f.read()
    # Находит все байтовые строки, передаваемые в Nvm8L6FkudRf
    pattern = r"Nvm8L6FkudRf\s*\(\s*b'(.*?)'\s*\)"
    matches = re.findall(pattern, code, re.DOTALL)
    logging.debug(f"Найдено {len(matches)} вызовов Nvm8L6FkudRf:")
    for i, hex_bytes in enumerate(matches, 1):
        # Преобразуем строку байтов в bytes
        try:
            encoded_data = bytes.fromhex(hex_bytes.replace("\\x", ""))
        except Exception:
            # Если не hex, пробуем eval
            try:
                encoded_data = eval(f"b'{hex_bytes}'")
            except Exception as e:
                logging.debug(f"{i}) Ошибка парсинга: {e}")
                continue
        logging.debug(f"\n{i}) Аргумент: b'{hex_bytes}'")
        analyze_and_extract(encoded_data)

"""if __name__ == "__main__":
    # ...ваш существующий код...
    # Добавьте вызов для автоматического декодирования:
    extract_and_decode_all("decompressed_code.py")"""




def replace_nvm8_calls(src_path, dst_path):
    with open(src_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Найти все вызовы Nvm8L6FkudRf(b'...')
    pattern = r"Nvm8L6FkudRf\s*\(\s*b'(.*?)'\s*\)"
    matches = re.findall(pattern, code, re.DOTALL)

    for hex_bytes in matches:
        try:
            encoded_data = bytes.fromhex(hex_bytes.replace("\\x", ""))
        except Exception:
            try:
                encoded_data = eval(f"b'{hex_bytes}'")
            except Exception:
                continue
        decoded = decode_xor(encoded_data)
        # Экранируем кавычки и переносы строк
        safe_decoded = repr(decoded)
        code = code.replace(f"Nvm8L6FkudRf(b'{hex_bytes}')", safe_decoded)

    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"✅ Замена завершена. Результат сохранён в {dst_path}")

if __name__ == "__main__":
    # Заменить все вызовы Nvm8L6FkudRf(b'...') на декодированные строки
    replace_nvm8_calls("decompressed_code.py", "decompressed_code_decoded.py")
