
import os
import unicodedata
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from radar.agents.movie_extractor import extract_movie
from radar.agents.movie_schema import MovieExtraction
from radar.database.connection import get_connection
from radar.database.extraction_attempts import save_extraction_attempt
from radar.database.movie_candidates import (
    get_candidate_for_article,
    save_movie_candidate,
)
from radar.services.article_classifier import classify_article
from radar.services.text_cleaner import clean_text


class MovieState(TypedDict, total=False):
    article_id: int
    title: str
    article_url: str
    classification: str
    extraction: MovieExtraction
    candidate_id: int
    outcome: str
    reason: str
    error_type: str


def load_article(state: MovieState) -> dict:
    """Load one existing article from PostgreSQL."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT title, url
                FROM articles
                WHERE id = %s
                """,
                (state["article_id"],),
            )
            row = cursor.fetchone()

    if row is None:
        raise ValueError("Article not found")

    return {
        "title": row[0],
        "article_url": row[1],
    }


def classify_node(state: MovieState) -> dict:
    result = classify_article(state["title"])
    return {
        "classification": result.status,
        "reason": result.reason,
    }


def route_classification(state: MovieState) -> str:
    if state["classification"] == "not_relevant":
        return "skip"
    return "check"


def check_existing_node(state: MovieState) -> dict:
    existing = get_candidate_for_article(
        state["article_id"]
    )

    if existing is not None:
        return {
            "candidate_id": existing[0],
            "outcome": "existing",
        }

    return {}


def route_existing(state: MovieState) -> str:
    if state.get("outcome") == "existing":
        return "skip"
    return "extract"


def extract_node(state: MovieState) -> dict:
    try:
        extraction = extract_movie(state["title"])
        return {"extraction": extraction}

    except Exception as exc:
        return {
            "outcome": "failed",
            "error_type": type(exc).__name__,
        }


def route_extraction(state: MovieState) -> str:
    if state.get("outcome") == "failed":
        return "log"
    return "review"

def normalize_evidence(text: str) -> str:
    """Normalize punctuation and spacing for evidence comparison."""
    value = unicodedata.normalize("NFKC", clean_text(text)).casefold()

    return "".join(
        char
        for char in value
        if unicodedata.category(char)[0] in {"L", "N", "M"}
    )

def evidence_review_node(state: MovieState) -> dict:
    """Apply basic evidence checks, not factual verification."""

    extraction = state["extraction"]
    source_title = normalize_evidence(state["title"])
    if (
        not extraction.movie_title
        or not extraction.movie_title.strip()
    ):
        return {
            "outcome": "no_candidate",
            "reason": "No identifiable movie title",
        }

    if extraction.is_kannada_film == "no":
        return {
            "outcome": "no_candidate",
            "reason": "Non-Kannada film",
        }

    if not extraction.evidence:
        return {
            "outcome": "no_candidate",
            "reason": "No supporting evidence",
        }

    for item in extraction.evidence:
        normalized = normalize_evidence(item)

        if not normalized or normalized not in source_title:
            return {
                "outcome": "no_candidate",
                "reason": "Evidence not found in article title",
            }

    return {
        "outcome": "ready",
        "reason": "Preliminary evidence checks passed",
    }


def route_review(state: MovieState) -> str:
    if state["outcome"] == "ready":
        return "save"
    return "log"


def save_node(state: MovieState) -> dict:
    try:
        model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite",
        )

        candidate_id, inserted = save_movie_candidate(
            article_id=state["article_id"],
            extraction=state["extraction"],
            input_title=state["title"],
            model_name=model_name,
        )

        return {
            "candidate_id": candidate_id,
            "outcome": "saved" if inserted else "duplicate",
        }

    except Exception as exc:
        return {
            "outcome": "failed",
            "error_type": type(exc).__name__,
        }


def log_node(state: MovieState) -> dict:
    """Log the extraction attempt in PostgreSQL."""

    save_extraction_attempt(
        article_id=state["article_id"],
        model_name=os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite",
        ),
        status=state["outcome"],
        candidate_id=state.get("candidate_id"),
        error_type=state.get("error_type"),
    )

    return {}


def build_movie_graph():
    """Compile the Kannada cinema extraction workflow."""

    graph = StateGraph(MovieState)

    graph.add_node("load", load_article)
    graph.add_node("classify", classify_node)
    graph.add_node("check_existing", check_existing_node)
    graph.add_node("extract", extract_node)
    graph.add_node("review", evidence_review_node)
    graph.add_node("save", save_node)
    graph.add_node("log", log_node)

    graph.add_edge(START, "load")
    graph.add_edge("load", "classify")

    graph.add_conditional_edges(
        "classify",
        route_classification,
        {
            "skip": END,
            "check": "check_existing",
        },
    )

    graph.add_conditional_edges(
        "check_existing",
        route_existing,
        {
            "skip": END,
            "extract": "extract",
        },
    )

    graph.add_conditional_edges(
        "extract",
        route_extraction,
        {
            "log": "log",
            "review": "review",
        },
    )

    graph.add_conditional_edges(
        "review",
        route_review,
        {
            "save": "save",
            "log": "log",
        },
    )

    graph.add_edge("save", "log")
    graph.add_edge("log", END)

    return graph.compile()
