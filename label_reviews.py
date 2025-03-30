import json
from pathlib import Path

import torch
import torch.nn.functional as F
from tqdm import tqdm
from transformers import (
    AutoTokenizer,
    AutoModelForQuestionAnswering,
    AutoModelForSequenceClassification
)

# --- Настройка устройства ---
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Устройство: MPS (Apple GPU)")
elif torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"Устройство: CUDA ({torch.cuda.get_device_name(0)})")
else:
    device = torch.device("cpu")
    print("Устройство: CPU")

# --- Загрузка моделей ---
qa_tokenizer = AutoTokenizer.from_pretrained("models/qa_model")
qa_model = AutoModelForQuestionAnswering.from_pretrained("models/qa_model").to(device)
qa_model.eval()

sentiment_tokenizer = AutoTokenizer.from_pretrained("models/sentiment_model_final")
sentiment_model = AutoModelForSequenceClassification.from_pretrained("models/sentiment_model_final").to(device)
sentiment_model.eval()

# --- Вопросы и метки ---
QUESTION_DICT = {
    "ambience_and_interior": "Что сказано про атмосферу, интерьер, обстановку, музыку, освещение, мебель, цвета или уют в заведении?",
    "food_quality": "Что сказано про еду, напитки, вкус, подачу, свежесть, качество блюд, десерты, состав или температуру еды?",
    "service_and_staff": "Что сказано про персонал, обслуживание, официантов, администраторов, вежливость, внимательность, ошибки персонала или сервис в целом?",
    "location": "Что сказано про расположение заведения, его адрес, близость к транспорту, парковке, вход или удобство найти это место?",
    "cleanliness": "Что сказано про чистоту, санитарное состояние, запахи, гигиену, туалеты, столы, посуду или общий порядок в заведении?",
    "price": "Что сказано про цены, стоимость блюд, соотношение цена-качество, ожидания от цен, скидки или мнение о том, стоит ли цена качества?",
    "waiting_time": "Что сказано про время ожидания, скорость подачи блюд, очереди, задержки, обслуживание по времени или быстро ли обслужили?"
}
SENTIMENT_LABELS = ["NEUTRAL", "POSITIVE", "NEGATIVE"]
QUESTION_LIST = list(QUESTION_DICT.items())


def label_reviews(company_id: int):
    folder = Path(f"files/{company_id}")
    infile = folder / "reviews_cleaned.json"
    outfile = folder / "review_analysis.json"

    with infile.open("r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    for review in tqdm(data, desc=f"Разметка отзывов для {company_id}"):
        text = review["text"].strip()
        entry = {
            "review_text": text,
            "name": review.get("name"),
            "icon_href": review.get("icon_href"),
            "date": review.get("date"),
            "stars": review.get("stars"),
            "answer": review.get("answer"),
            "aspects": []
        }

        # --- QA батч ---
        questions = [q for _, q in QUESTION_LIST]
        inputs = qa_tokenizer(questions, [text] * len(questions), return_tensors="pt",
                              padding=True, truncation="only_second", max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = qa_model(**inputs)
            start_probs = F.softmax(outputs.start_logits, dim=-1)
            end_probs = F.softmax(outputs.end_logits, dim=-1)

        extracted_aspects = []

        for i, (category, question) in enumerate(QUESTION_LIST):
            start_idx = torch.argmax(start_probs[i])
            end_idx = torch.argmax(end_probs[i]) + 1
            confidence = (start_probs[i][start_idx] * end_probs[i][end_idx - 1]).item()
            confidence_percent = round(confidence * 100, 1)

            answer_ids = inputs["input_ids"][i][start_idx:end_idx]
            answer = qa_tokenizer.decode(answer_ids, skip_special_tokens=True).strip()

            if not answer or answer.lower() in question.lower():
                continue

            extracted_aspects.append({
                "category": category,
                "answer": answer,
                "confidence": confidence_percent
            })

        # --- Батч сентимента ---
        if extracted_aspects:
            answers = [a["answer"] for a in extracted_aspects]
            sentiment_inputs = sentiment_tokenizer(answers, return_tensors="pt", truncation=True, padding=True)
            sentiment_inputs = {k: v.to(device) for k, v in sentiment_inputs.items()}

            with torch.no_grad():
                sentiment_outputs = sentiment_model(**sentiment_inputs)
                sentiment_probs = torch.softmax(sentiment_outputs.logits, dim=1)
                sentiment_ids = torch.argmax(sentiment_probs, dim=1)

            for i, aspect in enumerate(extracted_aspects):
                label_id = sentiment_ids[i].item()
                label = SENTIMENT_LABELS[label_id]
                conf = round(sentiment_probs[i][label_id].item() * 100, 1)

                entry["aspects"].append({
                    "category": aspect["category"],
                    "answer": aspect["answer"],
                    "confidence": aspect["confidence"],
                    "sentiment": label,
                    "sentiment_confidence": conf
                })

        results.append(entry)

    with outfile.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
