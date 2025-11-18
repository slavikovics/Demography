import json
import sqlite3
from tqdm import tqdm  # для прогресс-бара (установите: pip install tqdm)

def update_shape_names_advanced(json_file_path: str, db_file_path: str, output_file_path: str):
    """
    Улучшенная версия с прогресс-баром и дополнительной проверкой данных
    """

    # Загружаем JSON данные
    print("Загрузка JSON файла...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    features = data.get('features', [])
    print(f"Найдено {len(features)} features в JSON")

    # Подключаемся к базе данных
    print("Подключение к базе данных...")
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()

    try:
        # Получаем mapping данных
        print("Загрузка данных из базы...")
        cursor.execute("SELECT id, name_ru, name_en FROM territories")
        territories = cursor.fetchall()

        region_mapping = {row[0]: {'name_ru': row[1], 'name_en': row[2]} for row in territories}
        print(f"Загружено {len(region_mapping)} территорий из базы данных")

        # Обновляем JSON
        updated_count = 0
        not_found_ids = set()

        print("Обновление JSON...")
        for feature in tqdm(features, desc="Обработка features"):
            properties = feature.get('properties', {})
            region_id = properties.get('regionId')

            if region_id and region_id in region_mapping:
                names = region_mapping[region_id]
                properties['shapeName'] = names['name_en']
                properties['shapeNameRu'] = names['name_ru']
                updated_count += 1
            elif region_id:
                not_found_ids.add(region_id)

        # Выводим статистику
        print(f"\n=== Результаты ===")
        print(f"Обновлено записей: {updated_count}/{len(features)}")
        print(f"Не найдено в базе: {len(not_found_ids)}")
        if not_found_ids:
            print(f"Не найденные regionId: {sorted(not_found_ids)}")

        # Сохраняем результат
        print(f"Сохранение в {output_file_path}...")
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("Готово!")

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

# Использование
if __name__ == "__main__":
    update_shape_names_advanced(
        json_file_path="Frontend/src/belarus-districts.json",
        db_file_path="data/demography.db",
        output_file_path="Frontend/src/belarus-districts.json"
    )