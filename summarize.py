from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from razdel import sentenize
from tqdm import tqdm
import json
import torch

# Загрузка модели
model = SentenceTransformer("intfloat/multilingual-e5-large", cache_folder="./e5_model")

# Загрузка данных
with open("filtered_review_analysis.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# Группировка по category|sentiment
category_sentiment_fragments = {}
for item in tqdm(raw, desc="Группировка фрагментов"):
    for asp in item["aspects"]:
        key = f"{asp['category']}|{asp['sentiment']}"
        category_sentiment_fragments.setdefault(key, []).append(asp["answer"])

# Обработка кластеров
summary_by_group = {}

for key, fragments in tqdm(category_sentiment_fragments.items(), desc="Обработка категорий"):
    full_text = " ".join(fragments)
    sentences = [s.text for s in sentenize(full_text)]
    sentences = [s for s in sentences if len(s.split()) >= 10]

    if len(sentences) <= 5:
        summary_by_group[key] = sentences
        continue

    embeddings = model.encode(sentences, convert_to_tensor=True)
    k = min(10, max(2, round(len(sentences) ** 0.5)))
    kmeans = KMeans(n_clusters=k, random_state=0).fit(embeddings.cpu().numpy())
    labels = kmeans.labels_

    summary = []
    for label in set(labels):
        cluster_idxs = [i for i, lbl in enumerate(labels) if lbl == label]
        cluster_embeddings = embeddings[cluster_idxs]
        sim_matrix = cosine_similarity(cluster_embeddings.cpu(), cluster_embeddings.cpu())
        avg_sim = sim_matrix.mean(axis=1)
        best_idx = cluster_idxs[avg_sim.argmax()]
        summary.append(sentences[best_idx])

    summary_by_group[key] = summary

# Сохраняем JSON
with open("clustered_summary_21.json", "w", encoding="utf-8") as f:
    json.dump(summary_by_group, f, ensure_ascii=False, indent=2)

# Сохраняем читаемый .txt
with open("clustered_summary_21.txt", "w", encoding="utf-8") as f:
    for key, summary in summary_by_group.items():
        f.write(f"=== {key.upper()} ===\n")
        for s in summary:
            f.write(f"- {s.strip()}\n")
        f.write("\n")
