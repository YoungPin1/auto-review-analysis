import json
from pathlib import Path


def escape_latex(s: str) -> str:
    return (s.replace("\\", r"\textbackslash{}")
            .replace("&", r"\&")
            .replace("%", r"\%")
            .replace("$", r"\$")
            .replace("#", r"\#")
            .replace("_", r"\_")
            .replace("{", r"\{")
            .replace("}", r"\}")
            .replace("~", r"\textasciitilde{}")
            .replace("^", r"\^{}"))


def save_summary_and_examples(company_id: int):
    base_path = Path(f"files/{company_id}")
    base_path.mkdir(parents=True, exist_ok=True)

    # === 1. Генерация summary_section.tex ===
    summary_path = base_path / "14_analysis.json"
    summary_output_path = base_path / "summary_section.tex"

    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    CATEGORY_LABELS = {
        "ambience_and_interior": "Атмосфера",
        "food_quality": "Еда и напитки",
        "service_and_staff": "Обслуживание",
        "location": "Расположение",
        "cleanliness": "Чистота",
        "price": "Цена",
        "waiting_time": "Время ожидания"
    }

    SENTIMENT_NAMES = {
        "POSITIVE": "Позитивные впечатления гостей",
        "NEGATIVE": "Критика и замечания клиентов"
    }

    CATEGORY_ORDER = list(CATEGORY_LABELS.keys())
    SENTIMENT_ORDER = ["POSITIVE", "NEGATIVE"]

    lines = []

    for i, sentiment in enumerate(SENTIMENT_ORDER, start=1):
        sentiment_label = SENTIMENT_NAMES[sentiment]
        lines.append(f"\\subsection*{{2.{i} {sentiment_label}}}")

        if sentiment == "POSITIVE":
            lines.append("Это моменты и детали, о которых гости чаще всего писали положительные отзывы. "
                         "Из них можно понять, какие у заведения сильные стороны, которые больше всего завлекают клиентов.\n")
        else:
            lines.append("А здесь — примеры высказываний, в которых гости чаще всего выражали недовольство. "
                         "Можете понять, какие у заведения есть слабости, и на какие места нужно обратить особое внимание в будущем.\n")

        for j, category in enumerate(CATEGORY_ORDER, start=1):
            key = f"{category}|{sentiment}"
            if key not in data:
                continue

            sentences = data[key]
            if not sentences:
                continue

            cat_label = CATEGORY_LABELS[category]
            lines.append(f"\\subsubsection*{{2.{i}.{j} {sentiment_label} об {cat_label.lower()}}}")
            lines.append("\\begin{itemize}")
            for sentence in sentences:
                lines.append(f"  \\item {escape_latex(sentence)}")
            lines.append("\\end{itemize}\n")

    summary_output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Сохранено: {summary_output_path}")

    # === 2. Генерация annotated_examples.tex ===
    input_path = base_path / "filtered_analysis.json"
    output_path = base_path / "annotated_examples.tex"

    with open(input_path, "r", encoding="utf-8") as f:
        reviews = json.load(f)

    def avg_confidence(review):
        aspects = review.get("aspects", [])
        if not aspects:
            return 0
        return sum(a.get("confidence", 0) for a in aspects) / len(aspects)

    filtered_reviews = [r for r in reviews if len(r.get("review_text", "")) > 350]

    sorted_reviews = sorted(filtered_reviews, key=avg_confidence, reverse=True)
    top_reviews = sorted_reviews[:50]

    category_labels = CATEGORY_LABELS

    latex_lines = [
        r"\subsection*{3 Примеры полных отзывов с аннотацией}",
        r"\begingroup",
        r"\small",
        r"\setlength{\parskip}{0.5em}",
        r"\setlength{\parindent}{0pt}",
        ""
    ]

    for idx, review in enumerate(top_reviews, 1):
        text = escape_latex(review["review_text"].replace("\n", " "))
        latex_lines.append(rf"\textbf{{Отзыв {idx}.}}  ")
        latex_lines.append(text + "\n")
        latex_lines.append(r"\textbf{Аспекты:}")
        latex_lines.append(r"\begin{itemize}")
        for asp in review.get("aspects", []):
            cat = category_labels.get(asp["category"], asp["category"])
            ans = escape_latex(asp["answer"].replace("\n", " "))
            conf_cat = round(asp["confidence"], 1)
            sentiment = asp["sentiment"]
            conf_sent = round(asp["sentiment_confidence"], 1)
            line = rf"\item \textbf{{{cat}:}} ``{ans}'' (уверенность: {conf_cat}\%) --- \textbf{{{sentiment.capitalize()}}} (уверенность: {conf_sent}\%)"
            latex_lines.append(line)
        latex_lines.append(r"\end{itemize}")
        latex_lines.append(r"\vspace{1em}")

    latex_lines.append(r"\endgroup")

    output_path.write_text("\n".join(latex_lines), encoding="utf-8")
    print(f"✅ Сохранено: {output_path}")

    return str(summary_output_path), str(output_path)

