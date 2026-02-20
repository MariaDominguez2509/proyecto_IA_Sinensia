"""
BookAI - Sistema Inteligente de Recomendación de Libros
Feature: 001-book-recommendations
Dataset: Best Selling Books 2023-2025
Enfoque: Content-based recommendations usando embeddings + LLM reasoning
"""

import re
import sys
import time
import warnings
from typing import Dict, List, Optional, Tuple

# Ensure stdout uses UTF-8 so emojis render on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Data loading & preprocessing
# ---------------------------------------------------------------------------

def load_data(path: str = "best sellin books total.csv") -> pd.DataFrame:
    df = pd.read_csv(path, encoding="latin-1")
    print(f"📚 Dataset cargado: {df.shape[0]} libros, {df.shape[1]} columnas")
    return df


def clean_rating(rating_str) -> Optional[float]:
    if pd.isna(rating_str):
        return None
    match = re.search(r"(\d+\.\d+)", str(rating_str))
    return float(match.group(1)) if match else None


def clean_price(price_str) -> Optional[float]:
    if pd.isna(price_str):
        return None
    match = re.search(r"\$(\d+\.\d+)", str(price_str))
    return float(match.group(1)) if match else None


def parse_genres(genre_str) -> List[str]:
    if pd.isna(genre_str):
        return []
    return [g.strip() for g in str(genre_str).split("&")]


def create_book_description(row) -> str:
    parts = [
        f"Title: {row['Book name']}",
        f"Author: {row['Author']}",
        f"Genre: {row['Genre']}" if pd.notna(row["Genre"]) else "",
    ]
    return " | ".join(p for p in parts if p)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rating_clean"] = df["Rating"].apply(clean_rating)
    df["price_clean"] = df["price"].apply(clean_price)
    df["reviews_count_clean"] = df["reviews count"].apply(
        lambda x: int(str(x).replace(",", "")) if pd.notna(x) else 0
    )
    df["genres_list"] = df["Genre"].apply(parse_genres)
    df["primary_genre"] = df["genres_list"].apply(lambda x: x[0] if x else "Unknown")
    df["pub_year"] = pd.to_datetime(df["Publishing date"], errors="coerce").dt.year
    df["book_description"] = df.apply(create_book_description, axis=1)
    print("✅ Datos preprocesados")
    return df


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

def build_embeddings(df: pd.DataFrame) -> Tuple[TfidfVectorizer, np.ndarray]:
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
        sublinear_tf=True,
    )
    embeddings = vectorizer.fit_transform(df["book_description"].tolist()).toarray()
    embeddings_norm = normalize(embeddings)
    print(f"✅ Vectores TF-IDF: {embeddings.shape} | vocab: {len(vectorizer.vocabulary_)} términos")
    return vectorizer, embeddings_norm


# ---------------------------------------------------------------------------
# BookRecommender class
# ---------------------------------------------------------------------------

class BookRecommender:
    """Sistema completo de recomendaciones de libros (P1/P2/P3/P4)."""

    def __init__(self, df: pd.DataFrame, embeddings: np.ndarray, vectorizer: TfidfVectorizer):
        self.df = df
        self.embeddings = embeddings  # already normalised
        self.vectorizer = vectorizer
        print(f"✅ BookRecommender listo | {len(df)} libros | {embeddings.shape[1]} dims")

    # --- public API --------------------------------------------------------

    def recommend(
        self,
        query: str = None,
        book_title: str = None,
        preferences: Dict = None,
        top_k: int = 10,
        min_rating: float = 0.0,
    ) -> Tuple[pd.DataFrame, str]:
        """Punto de entrada unificado. Devuelve (DataFrame, tipo)."""
        if book_title:
            return self._by_similarity(book_title, top_k), "similarity"
        if preferences:
            return self._personalized(preferences, top_k), "personalized"
        if query:
            return self._by_genre(query, top_k, min_rating), "genre"
        raise ValueError("Proporcione query, book_title o preferences")

    def explain(self, book: pd.Series, user_query: str, llm_client=None) -> str:
        """P4: explicación de recomendación. Usa LLM si llm_client es proporcionado."""
        if llm_client is None:
            return (
                f"Este libro coincide con tu búsqueda de '{user_query}'. "
                f"Es un libro de {book['Genre']} escrito por {book['Author']}. "
                f"Rating {book['rating_clean']:.1f}/5.0 con {book['reviews_count_clean']:,} reviews."
            )

        prompt = (
            f"El usuario buscó: \"{user_query}\"\n\n"
            f"Libro recomendado:\n"
            f"- Título: {book['Book name']}\n"
            f"- Autor: {book['Author']}\n"
            f"- Género: {book['Genre']}\n"
            f"- Rating: {book['rating_clean']}/5.0\n"
            f"- Precio: ${book['price_clean']}\n\n"
            "Genera una explicación breve (2-3 frases) de por qué este libro es una buena recomendación."
        )
        response = llm_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    # --- private helpers ---------------------------------------------------

    def _query_vector(self, text: str) -> np.ndarray:
        vec = self.vectorizer.transform([text]).toarray()
        return normalize(vec)

    def _by_genre(self, query: str, top_k: int, min_rating: float) -> pd.DataFrame:
        sims = cosine_similarity(self._query_vector(f"Genre: {query}"), self.embeddings)[0]
        df_tmp = self.df.copy()
        df_tmp["similarity"] = sims
        df_tmp = df_tmp[df_tmp["rating_clean"] >= min_rating]
        return df_tmp.nlargest(top_k, "similarity")[
            ["Book name", "Author", "Genre", "rating_clean", "price_clean", "Print Length", "similarity"]
        ]

    def _by_similarity(self, book_title: str, top_k: int) -> pd.DataFrame:
        matches = self.df[self.df["Book name"].str.contains(book_title, case=False, na=False)]
        if matches.empty:
            print(f"❌ Libro '{book_title}' no encontrado en el catálogo")
            return pd.DataFrame()
        idx = matches.index[0]
        print(f"✅ Referencia: {self.df.iloc[idx]['Book name']}")
        sims = cosine_similarity(self.embeddings[idx].reshape(1, -1), self.embeddings)[0]
        df_tmp = self.df.copy()
        df_tmp["similarity"] = sims
        df_tmp = df_tmp.drop(idx)
        return df_tmp.nlargest(top_k, "similarity")[
            ["Book name", "Author", "Genre", "rating_clean", "price_clean", "similarity"]
        ]

    def _personalized(self, preferences: Dict, top_k: int) -> pd.DataFrame:
        parts = []
        if "favorite_authors" in preferences:
            parts.append(f"Authors: {', '.join(preferences['favorite_authors'])}")
        if "favorite_genres" in preferences:
            parts.append(f"Genres: {', '.join(preferences['favorite_genres'])}")
        query_text = " | ".join(parts) if parts else "Books"

        sims = cosine_similarity(self._query_vector(query_text), self.embeddings)[0]
        df_tmp = self.df.copy()
        df_tmp["similarity"] = sims

        if "max_price" in preferences:
            df_tmp = df_tmp[df_tmp["price_clean"] <= preferences["max_price"]]
        if "min_rating" in preferences:
            df_tmp = df_tmp[df_tmp["rating_clean"] >= preferences["min_rating"]]
        if "max_length" in preferences:
            df_tmp = df_tmp[df_tmp["Print Length"] <= preferences["max_length"]]
        if "min_length" in preferences:
            df_tmp = df_tmp[df_tmp["Print Length"] >= preferences["min_length"]]
        if "disliked_genres" in preferences:
            for genre in preferences["disliked_genres"]:
                df_tmp = df_tmp[~df_tmp["Genre"].str.contains(genre, case=False, na=False)]
        if "favorite_authors" in preferences:
            for author in preferences["favorite_authors"]:
                mask = df_tmp["Author"].str.contains(author, case=False, na=False)
                df_tmp.loc[mask, "similarity"] *= 1.2

        return df_tmp.nlargest(top_k, "similarity")[
            ["Book name", "Author", "Genre", "rating_clean", "price_clean", "Print Length", "similarity"]
        ]


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def evaluate_performance(recommender: BookRecommender) -> None:
    queries = ["Science Fiction", "Business books", "Historical Fiction", "Self-Improvement", "Mystery and Thriller"]
    times = []
    print("⏱️  Evaluando performance (<1s objetivo):\n")
    for q in queries:
        t0 = time.time()
        recommender.recommend(query=q, top_k=10)
        elapsed = time.time() - t0
        times.append(elapsed)
        status = "✅" if elapsed < 1.0 else "⚠️"
        print(f"  {status} '{q}': {elapsed:.3f}s")

    pct = sum(t < 1.0 for t in times) / len(times) * 100
    print(f"\n  Promedio: {np.mean(times):.3f}s | <1s: {pct:.0f}%")
    print("✅ SC-001 PASSED" if pct >= 95 else "❌ SC-001 FAILED")


def evaluate_relevance(recommender: BookRecommender) -> None:
    cases = [
        ("Science Fiction", "Fiction"),
        ("Self-Improvement", "Self-Improvement"),
        ("Business", "Business"),
        ("Mystery", "Mystery"),
    ]
    print("\n🎯 Evaluando relevancia (≥80% objetivo):\n")
    total_rel, total = 0, 0
    for query, expected in cases:
        recs, _ = recommender.recommend(query=query, top_k=10)
        rel = recs["Genre"].str.contains(expected, case=False, na=False).sum()
        n = len(recs)
        pct = rel / n * 100 if n else 0
        total_rel += rel
        total += n
        status = "✅" if pct >= 80 else "⚠️"
        print(f"  {status} '{query}': {pct:.0f}% ({rel}/{n})")

    overall = total_rel / total * 100 if total else 0
    print(f"\n  Relevancia general: {overall:.0f}%")
    print("✅ SC-002 PASSED" if overall >= 80 else "❌ SC-002 FAILED")


def print_recs(recs: pd.DataFrame, label: str = "") -> None:
    if label:
        print(f"\n{'─'*50}\n{label}\n{'─'*50}")
    for _, row in recs.iterrows():
        length = f" | 📄 {int(row['Print Length'])}p" if "Print Length" in row and pd.notna(row.get("Print Length")) else ""
        print(
            f"  📚 {row['Book name']}\n"
            f"     ✍️  {row['Author']} | 🎭 {row['Genre']}\n"
            f"     ⭐ {row['rating_clean']:.1f} | 💰 ${row['price_clean']:.2f}{length}"
            f" | 🎯 {row['similarity']:.3f}\n"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # 1. Load & preprocess
    df = load_data()
    df = preprocess(df)

    # 2. Build embeddings
    vectorizer, embeddings = build_embeddings(df)

    # 3. Create recommender
    rec = BookRecommender(df, embeddings, vectorizer)

    # 4. Demo: P1 – genre
    recs, _ = rec.recommend(query="Science Fiction", top_k=5)
    print_recs(recs, "P1 – Género: Science Fiction")

    # 5. Demo: P2 – similarity
    recs, _ = rec.recommend(book_title="Atomic Habits", top_k=5)
    print_recs(recs, "P2 – Similares a: Atomic Habits")

    # 6. Demo: P3 – personalized
    prefs = {
        "favorite_authors": ["James Clear", "Malcolm Gladwell"],
        "favorite_genres": ["Self-Improvement", "Business"],
        "disliked_genres": ["Romance"],
        "max_price": 25.0,
        "min_rating": 4.5,
        "max_length": 400,
    }
    recs, _ = rec.recommend(preferences=prefs, top_k=5)
    print_recs(recs, "P3 – Personalizado")

    # 7. Demo: P4 – explanation (rule-based fallback)
    sample = df.iloc[0]
    explanation = rec.explain(sample, "Self-improvement books")
    print(f"\n{'─'*50}\nP4 – Explicación\n{'─'*50}")
    print(f"  📚 {sample['Book name']}\n  💡 {explanation}\n")

    # 8. Evaluation
    evaluate_performance(rec)
    evaluate_relevance(rec)


if __name__ == "__main__":
    main()
