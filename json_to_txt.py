import json
from pathlib import Path
from datetime import datetime

CATEGORY_LABELS = {
    "ambience_and_interior": "Атмосфера и интерьер",
    "food_quality": "Еда и напитки",
    "service_and_staff": "Обслуживание",
    "location": "Расположение",
    "cleanliness": "Чистота",
    "price": "Цена",
    "waiting_time": "Время ожидания"
}

def export_annotations_to_txt(company_id: int):
    base_path = Path(f"files/{company_id}")
    input_path = base_path / "review_analysis.json"
    output_path = base_path / "review_analysis.txt"

    with input_path.open("r", encoding="utf-8") as f:
        reviews = json.load(f)

    lines = []

    for idx, review in enumerate(reviews, 1):
        text = review.get("review_text", "").replace("\n", " ").strip()
        name = review.get("name", "неизвестно")
        stars = review.get("stars", "?")
        date_val = review.get("date")
        try:
            date_str = datetime.fromtimestamp(date_val).strftime("%d.%m.%Y")
        except Exception:
            date_str = "неизвестно"

        lines.append(f"--- Отзыв {idx} ---")
        lines.append(f"Автор: {name}")
        lines.append(f"Оценка: {stars}")
        lines.append(f"Дата: {date_str}")
        lines.append(f"Текст: {text}")
        lines.append(f"Аспекты:")

        for asp in review.get("aspects", []):
            category_code = asp.get("category", "unknown")
            category = CATEGORY_LABELS.get(category_code, category_code)
            answer = asp.get("answer", "").replace("\n", " ").strip()
            sentiment = asp.get("sentiment", "?")
            conf = round(asp.get("confidence", 0), 1)
            sent_conf = round(asp.get("sentiment_confidence", 0), 1)

            lines.append(f"  - [{category}] «{answer}»")
            lines.append(f"    → Тональность: {sentiment} (уверенность {sent_conf}%), категория (уверенность {conf}%)")

        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Сохранено: {output_path}")
    return str(output_path)
