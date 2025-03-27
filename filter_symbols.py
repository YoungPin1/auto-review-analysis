import json
import re
from pathlib import Path

import emoji


def clean_text(text: str) -> str:
    text = text.replace("\n", " ").replace("\\n", " ")
    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r"[!?.,…]{2,}", ".", text)
    text = re.sub(r"[-=*_~]{3,}", "", text)
    text = re.sub(r'\\+', '', text)
    text = re.sub(r'\\"', '"', text)

    allowed_chars = r"[^а-яА-ЯёЁa-zA-Z0-9,.!?;:()\"'\s\-–«»/%№&/]"

    text = re.sub(allowed_chars, "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def restore_basic_punctuation(text: str) -> str:
    text = re.sub(r'\s+([,.!?])', r'\1', text)
    text = re.sub(r'\s+\.', '.', text)
    text = re.sub(r'\.(\w)', r'. \1', text)
    text = re.sub(r'(?<=\.\s)(\w)', lambda m: m.group(1).upper(), text)
    if text:
        text = text[0].upper() + text[1:]
    return text


def clean_review_file(company_id: int):
    folder = Path(f"files/{company_id}")
    infile = folder / "reviews_raw.json"
    outfile = folder / "reviews_cleaned.json"

    with infile.open("r", encoding="utf-8") as fin:
        reviews = json.load(fin)

    for item in reviews:
        if "text" in item and isinstance(item["text"], str):
            cleaned = clean_text(item["text"])
            punctuated = restore_basic_punctuation(cleaned)
            item["text"] = punctuated

    with outfile.open("w", encoding="utf-8") as fout:
        json.dump(reviews, fout, ensure_ascii=False, indent=2)