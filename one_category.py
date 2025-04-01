import json
import torch
import torch.nn.functional as F
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, AutoModelForSequenceClassification

# --- МОДЕЛИ ---
qa_tokenizer = AutoTokenizer.from_pretrained("./qa_model")
qa_model = AutoModelForQuestionAnswering.from_pretrained("./qa_model")
qa_model.eval()

sentiment_tokenizer = AutoTokenizer.from_pretrained("./sentiment_model_final")
sentiment_model = AutoModelForSequenceClassification.from_pretrained("./sentiment_model_final")
sentiment_model.eval()

# --- ВОПРОСЫ ---
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

# --- ИСХОДНЫЕ ОТЗЫВЫ ---
input_reviews = [
    {
        "text": "Больше всего понравились морские ежи, оказались очень свежие и невероятно вкусные. По ценам — всё достаточно недорого. Уровень заведения и качество блюд соответствуют. Немного разочаровало, что долго (минут 30) ждали основное блюдо. Очень красивый(молностью мраморный) и чистый туалет, похоже там каждые 10 минут убираются)). Общее впечатление — ухоженно, приятно находиться. Официанты вежливые, ненавязчивые, знают меню, могут что-то посоветовать и делают это с удовольствием. Атмосфера внутри уютная, есть уютная веранда, третий этаж с панорамными окнами, а при входе встречает витрина с выпечкой."
    },
    # Добавь сюда другие отзывы при необходимости
]

results = []

# --- ОБРАБОТКА ---
for review in tqdm(input_reviews, desc="Обработка отзывов"):
    text = review["text"].strip()
    entry = {
        "review_text": text,
        "aspects": []
    }

    for category, question in QUESTION_DICT.items():
        inputs = qa_tokenizer(question, text, return_tensors="pt", truncation="only_second", max_length=512)
        with torch.no_grad():
            outputs = qa_model(**inputs)
            start_probs = F.softmax(outputs.start_logits, dim=-1)
            end_probs = F.softmax(outputs.end_logits, dim=-1)

            start_idx = torch.argmax(start_probs)
            end_idx = torch.argmax(end_probs) + 1

            confidence = (start_probs[0][start_idx] * end_probs[0][end_idx - 1]).item()
            confidence_percent = round(confidence * 100, 1)

        answer_ids = inputs["input_ids"][0][start_idx:end_idx]
        answer = qa_tokenizer.decode(answer_ids, skip_special_tokens=True).strip()

        if not answer or answer.lower() in question.lower():
            continue

        # СЕНТИМЕНТ
        sentiment_inputs = sentiment_tokenizer(answer, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            sentiment_outputs = sentiment_model(**sentiment_inputs)
            sentiment_probs = torch.softmax(sentiment_outputs.logits, dim=1)
            sentiment_label_id = torch.argmax(sentiment_probs, dim=1).item()
            sentiment_label = SENTIMENT_LABELS[sentiment_label_id]
            sentiment_conf = round(sentiment_probs[0][sentiment_label_id].item() * 100, 1)

        entry["aspects"].append({
            "category": category,
            "answer": answer,
            "confidence": confidence_percent,
            "sentiment": sentiment_label,
            "sentiment_confidence": sentiment_conf
        })

    results.append(entry)

# --- СОХРАНЕНИЕ ---
with open("review_analysis.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
