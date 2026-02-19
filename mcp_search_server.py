# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp>=1.0.0",
#   "pandas",
#   "scikit-learn",
# ]
# ///

import difflib
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
from mcp.server.fastmcp import FastMCP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# Data loading & indexing (done once at startup)
# ---------------------------------------------------------------------------
_DATA_PATH = Path(__file__).parent / "best sellin books total.csv"
# Load and deduplicate (same book can appear across multiple years)
_df = pd.read_csv(_DATA_PATH, encoding="cp1252")
_df = _df.drop_duplicates(subset=["Book name"]).reset_index(drop=True)


def _build_corpus(row: pd.Series) -> str:
    parts = [
        str(row.get("Book name", "")),
        str(row.get("Author", "")),
        str(row.get("Genre", "")),
        str(row.get("Reading age", "")),
        str(row.get("form", "")),
    ]
    return " ".join(p for p in parts if p and p.lower() != "nan")


_corpus = _df.apply(_build_corpus, axis=1).tolist()
_vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
_tfidf_matrix = _vectorizer.fit_transform(_corpus)

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP("BookSearch")


@mcp.tool()
def search_books(description: str, k: int = 5) -> str:
    """Search the book catalog using a natural language description.

    Args:
        description: What kind of book you are looking for.
                     E.g. "self-help for building better habits",
                     "fantasy romance with dragons and magic".
        k: Number of books to return (1–50, default 5).

    Returns:
        JSON array of the top-k matching books, ordered by relevance.
        Each entry includes title, author, genre, rating, reviews count,
        price, format, page count, publishing date, and a relevance score.
    """
    k = max(1, min(int(k), 50))

    query_vec = _vectorizer.transform([description])
    scores = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    top_indices = scores.argsort()[::-1][:k]

    results = []
    for idx in top_indices:
        row = _df.iloc[idx]

        def _int(val):
            try:
                return int(val) if pd.notna(val) else None
            except (ValueError, TypeError):
                return None

        results.append(
            {
                "title": row.get("Book name", ""),
                "author": row.get("Author", ""),
                "genre": row.get("Genre", ""),
                "rating": row.get("Rating", ""),
                "reviews": _int(row.get("reviews count")),
                "price": row.get("price", ""),
                "format": row.get("form", ""),
                "pages": _int(row.get("Print Length")),
                "published": row.get("Publishing date", ""),
                "relevance_score": round(float(scores[idx]), 4),
            }
        )

    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def get_book_description(title: str) -> str:
    """Get a short description of a book by title.

    Searches the local catalog for an exact match (case-insensitive).
    If not found, suggests up to 3 close alternatives from the catalog.
    Always fetches a short description from the internet (Google Books API).

    Args:
        title: The title of the book to look up.

    Returns:
        JSON object with catalog match status, close options (if any),
        and a short description fetched from the internet.
    """
    title_stripped = title.strip()
    title_lower = title_stripped.lower()
    catalog_titles = _df["Book name"].tolist()

    # 1. Exact match (case-insensitive)
    exact = _df[_df["Book name"].str.lower().str.strip() == title_lower]

    result: dict = {}
    if not exact.empty:
        result["status"] = "exact_match"
        result["catalog_match"] = exact.iloc[0]["Book name"]
    else:
        close = difflib.get_close_matches(title_stripped, catalog_titles, n=3, cutoff=0.4)
        if close:
            result["status"] = "no_exact_match"
            result["close_options"] = close
        else:
            result["status"] = "not_in_catalog"

    # 2. Fetch description from Google Books API
    query = urllib.parse.quote(f"intitle:{title_stripped}")
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1&langRestrict=en"

    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode())

        if data.get("totalItems", 0) > 0:
            info = data["items"][0].get("volumeInfo", {})
            description = info.get("description", "").strip()
            if len(description) > 400:
                description = description[:400].rsplit(" ", 1)[0] + "..."
            result["found_title"] = info.get("title", "")
            result["found_author"] = ", ".join(info.get("authors", []))
            result["description"] = description or "No description available."
        else:
            result["description"] = "No description found online."

    except Exception as exc:
        result["description"] = f"Could not fetch description: {exc}"

    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
