"""
BookAI - Flask API + HTML frontend
Run:  python app.py
Open: http://localhost:5000
"""

import os
import sys

import pandas as pd
from flask import Flask, jsonify, render_template, request

sys.path.insert(0, os.path.dirname(__file__))
from ia import BookRecommender, build_embeddings, load_data, preprocess

app = Flask(__name__)

# ---------------------------------------------------------------------------
# CORS (for local dev)
# ---------------------------------------------------------------------------
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ---------------------------------------------------------------------------
# Lazy singletons
# ---------------------------------------------------------------------------
_rec = None
_llm = None


def get_recommender() -> BookRecommender:
    global _rec
    if _rec is None:
        df = load_data()
        df = preprocess(df)
        vectorizer, embeddings = build_embeddings(df)
        _rec = BookRecommender(df, embeddings, vectorizer)
    return _rec


def get_llm():
    global _llm
    if _llm is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            try:
                from anthropic import Anthropic
                _llm = Anthropic(api_key=api_key)
            except ImportError:
                pass
    return _llm


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    r = get_recommender()
    return jsonify({"book_count": len(r.df), "llm_available": get_llm() is not None})


@app.route("/api/recommend", methods=["POST", "OPTIONS"])
def recommend():
    if request.method == "OPTIONS":
        return "", 204

    data = request.json or {}
    mode = data.get("mode", "genre")
    top_k = int(data.get("top_k", 10))
    min_rating = float(data.get("min_rating", 0.0))
    explain = bool(data.get("explain", False))

    r = get_recommender()

    try:
        if mode == "genre":
            recs, _ = r.recommend(query=data.get("query", ""), top_k=top_k, min_rating=min_rating)
            label = data.get("query", "")
        elif mode == "similar":
            recs, _ = r.recommend(book_title=data.get("book_title", ""), top_k=top_k)
            label = data.get("book_title", "")
        elif mode == "personalized":
            recs, _ = r.recommend(preferences=data.get("preferences", {}), top_k=top_k)
            label = "your preferences"
        else:
            return jsonify({"error": "Invalid mode"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if recs.empty:
        return jsonify({"books": [], "count": 0})

    books = []
    for _, row in recs.iterrows():
        book = {
            "title": row["Book name"],
            "author": row["Author"],
            "genre": row["Genre"],
            "rating": row["rating_clean"],
            "price": round(float(row["price_clean"]), 2) if pd.notna(row.get("price_clean")) else None,
            "pages": int(row["Print Length"]) if pd.notna(row.get("Print Length")) else None,
            "similarity": round(float(row["similarity"]), 3),
            "explanation": None,
        }
        if explain:
            book["explanation"] = r.explain(row, label, llm_client=get_llm())
        books.append(book)

    return jsonify({"books": books, "count": len(books)})


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return "", 204

    llm = get_llm()
    if not llm:
        return jsonify({"error": "LLM not available. Set ANTHROPIC_API_KEY and restart."}), 400

    data = request.json or {}
    message = data.get("message", "")
    history = data.get("history", [])
    min_rating = float(data.get("min_rating", 0.0))

    r = get_recommender()
    recs, _ = r.recommend(query=message, top_k=5, min_rating=min_rating)
    catalog = "\n".join(
        f"- {row['Book name']} by {row['Author']} ({row['Genre']}, "
        f"rating {row['rating_clean']:.1f}, ${row['price_clean']:.2f})"
        for _, row in recs.iterrows()
    ) if not recs.empty else "No catalog matches found."

    messages = [{"role": h["role"], "content": h["content"]} for h in history[-6:]]
    messages.append({
        "role": "user",
        "content": (
            f"You are BookAI, a friendly book recommendation assistant.\n"
            f"Relevant books from our catalog:\n{catalog}\n\n"
            f"User message: {message}\n\n"
            f"Reply conversationally in 3-5 sentences, referencing specific books when relevant."
        ),
    })

    try:
        response = llm.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=messages,
        )
        return jsonify({"reply": response.content[0].text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Loading BookRecommender...")
    get_recommender()
    print("\nBookAI running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
