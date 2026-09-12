from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingEngine:

    def __init__(
        self,
        model_name="BAAI/bge-small-en-v1.5"
    ):
        print(f"Loading embedding model: {model_name}")

        self.model = SentenceTransformer(
            model_name
        )

    # ---------------------------------------------------------
    # GENERATE EMBEDDING
    # ---------------------------------------------------------

    def generate_embedding(self, text: str):

        if not text:
            return np.zeros(384)

        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding

    # ---------------------------------------------------------
    # GENERATE MULTIPLE EMBEDDINGS
    # ---------------------------------------------------------

    def generate_embeddings(self, texts):

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True
        )

        return embeddings

    # ---------------------------------------------------------
    # COSINE SIMILARITY
    # ---------------------------------------------------------

    def similarity(
        self,
        embedding1,
        embedding2
    ):

        embedding1 = np.asarray(
            embedding1
        )

        embedding2 = np.asarray(
            embedding2
        )

        similarity = np.dot(
            embedding1,
            embedding2
        )

        return float(similarity)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    engine = EmbeddingEngine()

    descriptions = [
        "stainless steel hexagonal bolt m10 x 50 mm",
        "stainless steel hexagonal bolt 10 x 50 mm",
        "stainless steel hexagonal bolt m10 x 8 mm",
        "stainless steel circular bolt m10 x 8 mm"
    ]

    print("\n--- EMBEDDING TEST ---")

    embeddings = engine.generate_embeddings(
        descriptions
    )

    print(
        f"\nEmbedding dimension: "
        f"{len(embeddings[0])}"
    )

    print("\nPAIRWISE SIMILARITY:")

    for i in range(len(descriptions)):

        for j in range(i + 1, len(descriptions)):

            score = engine.similarity(
                embeddings[i],
                embeddings[j]
            )

            print(
                f"\n{i + 1} vs {j + 1}"
            )

            print(
                f"A: {descriptions[i]}"
            )

            print(
                f"B: {descriptions[j]}"
            )

            print(
                f"Similarity: {score:.4f}"
            )