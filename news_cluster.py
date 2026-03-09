from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")


def cluster_headlines(headlines, threshold=0.7):
    """
    Groups similar headlines together.
    """

    if not headlines:
        return []

    texts = [h["title"] for h in headlines]

    embeddings = model.encode(texts)

    similarity_matrix = cosine_similarity(embeddings)

    clusters = []
    used = set()

    for i in range(len(texts)):

        if i in used:
            continue

        cluster = [headlines[i]]
        used.add(i)

        for j in range(i + 1, len(texts)):
            if similarity_matrix[i][j] > threshold:
                cluster.append(headlines[j])
                used.add(j)

        clusters.append(cluster)

    return clusters