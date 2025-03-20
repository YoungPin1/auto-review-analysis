import json
from collections import Counter

MIN_QA_CONFIDENCE = 80.0
MIN_SENTIMENT_CONFIDENCE = 90.0

with open("review_analysis.json", "r", encoding="utf-8") as f:
    data = json.load(f)

all_pairs = []
for entry in data:
    for aspect in entry["aspects"]:
        pair = (aspect["category"], aspect["sentiment"])
        all_pairs.append(pair)

total_pairs_before = len(all_pairs)

filtered_data = []
filtered_pairs = []

for entry in data:
    new_entry = {
        "review_text": entry["review_text"],
        "aspects": []
    }
    for aspect in entry["aspects"]:
        if aspect["confidence"] >= MIN_QA_CONFIDENCE and aspect["sentiment_confidence"] >= MIN_SENTIMENT_CONFIDENCE:
            new_entry["aspects"].append(aspect)
            filtered_pairs.append((aspect["category"], aspect["sentiment"]))

    if new_entry["aspects"]:
        filtered_data.append(new_entry)

total_pairs_after = len(filtered_pairs)

with open("filtered_review_analysis.json", "w", encoding="utf-8") as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)

print(f"Пар категория-сентимент до фильтрации: {total_pairs_before}")
print(f"Осталось пар ПОСЛЕ фильтрации: {total_pairs_after}")
