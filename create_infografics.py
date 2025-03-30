import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def generate_charts(company_id: int):
    base_path = Path(f"files/{company_id}")
    image_path = Path(f"images/{company_id}")
    image_path.mkdir(parents=True, exist_ok=True)

    # 1. Категории (filtered_analysis)
    with open(base_path / "filtered_analysis.json", "r", encoding="utf-8") as f:
        filtered_data = json.load(f)

    category_counter = {}
    for review in filtered_data:
        for aspect in review.get("aspects", []):
            cat = aspect["category"]
            category_counter[cat] = category_counter.get(cat, 0) + 1

    category_labels = {
        "ambience_and_interior": "Атмосфера",
        "food_quality": "Еда и напитки",
        "service_and_staff": "Обслуживание",
        "location": "Расположение",
        "cleanliness": "Чистота",
        "price": "Цена",
        "waiting_time": "Время ожидания"
    }

    ordered_keys = list(category_labels.keys())
    sizes = [category_counter.get(k, 0) for k in ordered_keys]
    labels = [category_labels[k] for k in ordered_keys]
    total = sum(sizes)
    sizes_percent = [round(100 * s / total) for s in sizes]

    colors = ['#4E79A7', '#F28E2B', '#76B7B2', '#59A14F', '#EDC948', '#B07AA1', '#FF9DA7']

    fig, ax = plt.subplots(figsize=(6, 6), dpi=300)
    wedges, _ = ax.pie(
        sizes_percent,
        labels=None,
        startangle=90,
        colors=colors,
        wedgeprops=dict(width=0.3, edgecolor='white')
    )
    legend_labels = [f"{label} — {size}%" for label, size in zip(labels, sizes_percent)]
    ax.legend(wedges, legend_labels, title="Категория", loc="center left", bbox_to_anchor=(1, 0.5))
    centre_circle = plt.Circle((0, 0), 0.7, fc='white')
    fig.gca().add_artist(centre_circle)
    plt.title("Аспекты оценки заведения", fontsize=18, ha='center')
    ax.axis('equal')
    plt.savefig(image_path / "category_donut_chart.png", dpi=300, bbox_inches="tight")
    plt.close()

    # 2 и 3. Общий сентимент и гистограмма — из review_analysis
    with open(base_path / "review_analysis.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    sentiment_labels = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
    sentiment_colors = ['#4CAF50', '#D3D3D3', '#F44336']
    sentiment_counter = {k: 0 for k in sentiment_labels}
    aspect_sentiment = {k: {s: 0 for s in sentiment_labels} for k in ordered_keys}

    for entry in raw_data:
        for asp in entry.get("aspects", []):
            sentiment = asp["sentiment"]
            category = asp["category"]
            sentiment_counter[sentiment] += 1
            if category in aspect_sentiment:
                aspect_sentiment[category][sentiment] += 1

    # Donut sentiment
    sentiment_sizes = [sentiment_counter[k] for k in sentiment_labels]
    sentiment_total = sum(sentiment_sizes)
    sentiment_percents = [round(100 * v / sentiment_total) for v in sentiment_sizes]
    sentiment_text = ['Позитивные', 'Нейтральные', 'Негативные']

    fig, ax = plt.subplots(figsize=(6, 6), dpi=300)
    wedges, _ = ax.pie(
        sentiment_percents,
        labels=None,
        startangle=90,
        colors=sentiment_colors,
        wedgeprops=dict(width=0.3, edgecolor='white')
    )
    legend_labels = [f"{label} — {size}%" for label, size in zip(sentiment_text, sentiment_percents)]
    ax.legend(wedges, legend_labels, title="Тональность", loc="center left", bbox_to_anchor=(1, 0.5))
    centre_circle = plt.Circle((0, 0), 0.7, fc='white')
    fig.gca().add_artist(centre_circle)
    plt.title("Общий тон отзывов", fontsize=18, ha='center')
    ax.axis('equal')
    plt.savefig(image_path / "sentiment_donut_chart.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Histogram
    categories = [category_labels[k] for k in ordered_keys]
    positive = np.array([aspect_sentiment[k]["POSITIVE"] for k in ordered_keys])
    neutral = np.array([aspect_sentiment[k]["NEUTRAL"] for k in ordered_keys])
    negative = np.array([aspect_sentiment[k]["NEGATIVE"] for k in ordered_keys])
    total = positive + neutral + negative

    bar_width = 0.5
    x = np.arange(len(categories)) * 1.5

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    ax.bar(x, positive, width=bar_width, color=sentiment_colors[0])
    ax.bar(x, neutral, width=bar_width, bottom=positive, color=sentiment_colors[1])
    ax.bar(x, negative, width=bar_width, bottom=positive + neutral, color=sentiment_colors[2])

    for i in range(len(categories)):
        y_offset = 0
        for val, color in zip([positive[i], neutral[i], negative[i]], sentiment_colors):
            if total[i] > 0:
                percent = f"{val / total[i] * 100:.0f}%"
                ax.text(x[i], y_offset + val / 2, percent, ha='center', va='center', fontsize=8, color='white')
                y_offset += val

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_yticks(np.arange(0, max(total) + 50, 50))
    ax.tick_params(axis='x', length=0)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    plt.title("Распределение тональности по аспектам", fontsize=14, pad=20)
    ax.legend(["Позитивная", "Нейтральная", "Негативная"],
              loc='center left',
              bbox_to_anchor=(1.15, 0.5))
    plt.tight_layout()
    plt.savefig(image_path / "histogram.png", dpi=300, bbox_inches="tight")
    plt.close()

    # 4. Heatmap
    df = pd.DataFrame(
        [list(aspect_sentiment[k].values()) for k in ordered_keys],
        columns=['Позитивные', 'Нейтральные', 'Негативные']
    )
    df.index = [category_labels[k] for k in ordered_keys]
    plt.figure(figsize=(10, 6), dpi=300)
    sns.heatmap(df, annot=True, cmap="RdYlGn", fmt="d", linewidths=0.5, cbar=True)
    plt.title("Тепловая карта: Категория × Тональность", fontsize=14)
    plt.tight_layout()
    plt.savefig(image_path / "heatmap_category_sentiment_rus.png", bbox_inches="tight", dpi=300)
    plt.close()

    #  5. Гистограмма по звёздам в каждой категории
    star_dist = {k: [0] * 5 for k in ordered_keys}
    star_sum = defaultdict(float)
    star_count = defaultdict(int)

    for review in filtered_data:
        stars = review.get("stars")
        for asp in review.get("aspects", []):
            cat = asp["category"]
            if cat in star_dist and isinstance(stars, (int, float)):
                star_idx = int(round(stars)) - 1
                if 0 <= star_idx < 5:
                    star_dist[cat][star_idx] += 1
                    star_sum[cat] += stars
                    star_count[cat] += 1

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    bar_width = 0.5
    x = np.arange(len(ordered_keys))
    star_colors = ['#FDD835', '#FBC02D', '#F9A825', '#F57F17', '#FFA000']

    stars_percent = []
    for cat in ordered_keys:
        total = sum(star_dist[cat])
        if total == 0:
            stars_percent.append([0] * 5)
        else:
            stars_percent.append([100 * count / total for count in star_dist[cat]])

    bottom = np.zeros(len(ordered_keys))
    for i in range(5):
        values = [stars_percent[j][i] for j in range(len(ordered_keys))]
        bars = ax.bar(x, values, bottom=bottom, width=bar_width, color=star_colors[i], label=f"{i + 1}★")
        bottom += values

        for j, val in enumerate(values):
            ax.text(x[j], bottom[j] - val / 2, f"{val:.0f}%", ha='center', va='center', fontsize=8, color='white')

    ax.set_xticks(x)
    ax.set_xticklabels([category_labels[k] for k in ordered_keys], rotation=45, ha='right')
    ax.set_title("Процентное распределение звёзд по категориям", fontsize=14)
    ax.set_ylabel("Проценты")
    ax.set_ylim(0, 100)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend(title="Оценка")
    plt.tight_layout()
    plt.savefig(image_path / "star_percent_stacked_bar.png", dpi=300, bbox_inches="tight")
    plt.close()

    # 6. Средняя оценка по категории
    avg_stars = [star_sum[k] / star_count[k] if star_count[k] else 0 for k in ordered_keys]
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    bars = ax.bar([category_labels[k] for k in ordered_keys], avg_stars, color='#4E79A7')
    ax.set_ylim(0, 5)
    ax.set_ylabel("Средняя оценка (звёзды)")
    ax.set_title("Средний рейтинг по категориям")
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1, f"{height:.1f}", ha='center', fontsize=9)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(image_path / "average_star_rating_per_category.png", dpi=300, bbox_inches="tight")
    plt.close()


