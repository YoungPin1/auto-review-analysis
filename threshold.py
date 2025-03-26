import json
from pathlib import Path


def filter_labeled_reviews(company_id: int,
                           min_qa_conf: float = 30.0,
                           min_sent_conf: float = 80.0):

    folder = Path(f"files/{company_id}")
    infile = folder / "review_analysis.json"
    outfile = folder / "filtered_analysis.json"

    with infile.open("r", encoding="utf-8") as f:
        data = json.load(f)

    all_pairs = []
    filtered_pairs = []
    filtered_data = []

    for entry in data:
        for aspect in entry.get("aspects", []):
            all_pairs.append((aspect["category"], aspect["sentiment"]))

        new_entry = {
            "review_text": entry["review_text"],
            "name": entry.get("name"),
            "icon_href": entry.get("icon_href"),
            "date": entry.get("date"),
            "stars": entry.get("stars"),
            "answer": entry.get("answer"),
            "aspects": []
        }

        for aspect in entry.get("aspects", []):
            if (
                    aspect["confidence"] >= min_qa_conf and
                    aspect["sentiment_confidence"] >= min_sent_conf
            ):
                new_entry["aspects"].append(aspect)
                filtered_pairs.append((aspect["category"], aspect["sentiment"]))

        if new_entry["aspects"]:
            filtered_data.append(new_entry)

    with outfile.open("w", encoding="utf-8") as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)

