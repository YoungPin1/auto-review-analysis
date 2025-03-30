import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm


def summarize_14_clusters(company_id: int):
    input_path = Path(f"files/{company_id}/filtered_analysis.json")
    output_path = Path(f"files/{company_id}/14_analysis.json")

    model = SentenceTransformer("intfloat/multilingual-e5-large", cache_folder="./models/e5_model")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    category_sentiment_fragments = {}

    for item in tqdm(data, desc="Группировка фрагментов"):
        name = item.get("name", "")
        date = item.get("date", None)

        for asp in item["aspects"]:
            if asp["sentiment"] == "NEUTRAL":
                continue
            if asp["confidence"] < 90 or asp["sentiment_confidence"] < 90:
                continue
            key = f"{asp['category']}|{asp['sentiment']}"
            entry = {
                "text": asp["answer"],
                "name": name,
                "date": date
            }
            category_sentiment_fragments.setdefault(key, []).append(entry)

    summary_by_group = {}

    def get_cluster_count(n):
        if n <= 5:
            return None
        elif n <= 25:
            return 6
        elif n <= 40:
            return 7
        elif n <= 55:
            return 8
        elif n <= 70:
            return 9
        else:
            return 10

    for key, entries in tqdm(category_sentiment_fragments.items(), desc="Обработка категорий"):
        long_entries = [e for e in entries if len(e["text"].split()) >= 10]

        cluster_n = get_cluster_count(len(long_entries))

        if not cluster_n:
            summary_by_group[key] = long_entries
            continue

        texts = [e["text"] for e in long_entries]
        embeddings = model.encode(texts, convert_to_tensor=True)
        kmeans = KMeans(n_clusters=cluster_n, random_state=0).fit(embeddings.cpu().numpy())
        labels = kmeans.labels_

        summary = []
        for label in set(labels):
            cluster_idxs = [i for i, lbl in enumerate(labels) if lbl == label]
            cluster_embeddings = embeddings[cluster_idxs]
            sim_matrix = cosine_similarity(cluster_embeddings.cpu(), cluster_embeddings.cpu())
            avg_sim = sim_matrix.mean(axis=1)
            best_idx = cluster_idxs[avg_sim.argmax()]
            summary.append(long_entries[best_idx])

        summary_by_group[key] = summary

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary_by_group, f, ensure_ascii=False, indent=2)

    return output_path.name


