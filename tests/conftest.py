"""Configuration commune des tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "analysis"))

COLONNES = [
    "platform",
    "source_id",
    "post_id",
    "interaction_id",
    "source_user",
    "target_user",
    "interaction_type",
    "text",
    "timestamp",
    "parent_id",
    "url",
]


def ligne(**valeurs) -> dict:
    base = {colonne: "" for colonne in COLONNES}
    base.update(valeurs)
    return base


@pytest.fixture
def cadre_minimal() -> pd.DataFrame:
    """Petit jeu valide : deux groupes reliés par une seule interaction croisée."""
    lignes = [
        ligne(
            platform="facebook",
            source_id="facebook_001",
            post_id="p001",
            interaction_id="p001",
            source_user="a1",
            interaction_type="post",
            text="Discussion sur la langue d'enseignement #arabisation",
            timestamp="2026-01-01T10:00:00",
            url="https://exemple.org/p001",
        ),
        ligne(
            platform="facebook",
            source_id="facebook_001",
            post_id="p001",
            interaction_id="i001",
            source_user="a2",
            target_user="a1",
            interaction_type="comment",
            text="Bravo, excellente analyse, merci beaucoup",
            timestamp="2026-01-01T10:10:00",
            parent_id="p001",
            url="https://exemple.org/p001",
        ),
        ligne(
            platform="facebook",
            source_id="facebook_001",
            post_id="p001",
            interaction_id="i002",
            source_user="a3",
            target_user="a2",
            interaction_type="reply",
            text="Je soutiens totalement, d'accord avec vous",
            timestamp="2026-01-01T10:20:00",
            parent_id="i001",
            url="https://exemple.org/p001",
        ),
        ligne(
            platform="x",
            source_id="x_001",
            post_id="p002",
            interaction_id="p002",
            source_user="b1",
            interaction_type="post",
            text="Débat sur l'immigration et le travail",
            timestamp="2026-01-02T09:00:00",
            url="https://exemple.org/p002",
        ),
        ligne(
            platform="x",
            source_id="x_001",
            post_id="p002",
            interaction_id="i003",
            source_user="b2",
            target_user="b1",
            interaction_type="quote",
            text="C'est une honte, scandaleux, ça suffit !!!",
            timestamp="2026-01-02T09:30:00",
            parent_id="p002",
            url="https://exemple.org/p002",
        ),
        ligne(
            platform="x",
            source_id="x_001",
            post_id="p002",
            interaction_id="i004",
            source_user="b3",
            target_user="b2",
            interaction_type="reply",
            text="Ces gens doivent dégagez, il faut expulser les immigrés",
            timestamp="2026-01-02T09:45:00",
            parent_id="i003",
            url="https://exemple.org/p002",
        ),
        ligne(
            platform="x",
            source_id="x_001",
            post_id="p002",
            interaction_id="i005",
            source_user="a1",
            target_user="b1",
            interaction_type="mention",
            text="Quelqu'un a-t-il une source sérieuse ?",
            timestamp="2026-01-02T10:00:00",
            parent_id="p002",
            url="https://exemple.org/p002",
        ),
    ]
    return pd.DataFrame(lignes, columns=COLONNES)
