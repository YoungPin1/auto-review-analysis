import json

with open("filtered_review_analysis.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("filtered_analysis_readable.txt", "w", encoding="utf-8") as f:
    for entry in data:
        f.write("📝 Отзыв:\n")
        f.write(entry["review_text"].strip() + "\n\n")

        for asp in entry["aspects"]:
            f.write(f"➤ Категория: {asp['category'].upper()}\n")
            f.write(f"   Текст: {asp['answer']}\n")
            f.write(f"   Сентимент: {asp['sentiment']} ({asp['sentiment_confidence']}%)\n")
            f.write(f"   Уверенность: {asp['confidence']}%\n\n")

        f.write("-" * 60 + "\n")

print("Готово: сохранено в filtered_analysis_readable.txt")
