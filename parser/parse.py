import json
from pathlib import Path
from parser.utils import YandexParser


def parse_reviews(company_id: int):
    folder = Path(f"files/{company_id}")
    folder.mkdir(parents=True, exist_ok=True)
    output_file = folder / "reviews_raw.json"

    parser = YandexParser(company_id)
    result = parser.parse()
    company_info = result.get("company_info", {})
    reviews = result.get("company_reviews", [])
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

    return company_info
