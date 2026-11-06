
from typing import Literal

from pydantic import BaseModel, Field


class MovieExtraction(BaseModel):
    movie_title: str | None = Field(
        description="Explicitly mentioned movie title, if identifiable"
    )

    film_language: str | None = Field(
        description="Movie language when supported by the input"
    )

    is_kannada_film: Literal[
        "yes", "no", "unknown"
    ] = Field(
        description="Whether the movie is Kannada-language"
    )

    release_date: str | None = Field(
        description="Explicitly mentioned release date, otherwise null"
    )

    mentioned_people: list[str] = Field(
        description="People explicitly mentioned in the input"
    )

    evidence: list[str] = Field(
        description="Short factual phrases found in the input"
    )

    needs_review: bool = Field(
        description="Whether more evidence is required"
    )
