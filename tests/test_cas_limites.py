"""Tests des cas limites : absence de lien, absence de texte, données dégradées."""

from __future__ import annotations

import pandas as pd

import community_detection
import emotion_analysis
import hate_speech_analysis
import load_data
import network_analysis
import preprocess
import propagation_analysis
import sentiment_analysis
import text_analysis
from conftest import COLONNES, ligne


def _chaine_complete(cadre_brut: pd.DataFrame) -> pd.DataFrame:
    cadre = preprocess.pretraiter(load_data.normaliser(cadre_brut))
    cadre = sentiment_analysis.analyser_sentiment(cadre)
    cadre = emotion_analysis.analyser_emotions(cadre)
    cadre = hate_speech_analysis.analyser_discours_haineux(cadre)
    cadre["auteur_etiquette"] = [f"Utilisateur {i:03d}" for i in range(1, len(cadre) + 1)]
    return cadre


def test_jeu_sans_aucun_lien_relationnel():
    """Uniquement des publications : aucun lien, aucune communauté détectable."""
    lignes = [
        ligne(
            platform="facebook",
            source_id="facebook_001",
            post_id=f"p{index:03d}",
            interaction_id=f"p{index:03d}",
            source_user=f"u{index:03d}",
            interaction_type="post",
            text="Publication sans interaction",
            timestamp=f"2026-01-0{index}T10:00:00",
        )
        for index in range(1, 4)
    ]
    cadre = _chaine_complete(pd.DataFrame(lignes, columns=COLONNES))

    graphe = network_analysis.construire_graphe(cadre)
    assert graphe.number_of_edges() == 0

    metriques = network_analysis.calculer_metriques(graphe)
    assert metriques["liens"] == 0

    appartenance, modularite, algorithme = community_detection.detecter_communautes(graphe)
    assert modularite == 0.0
    assert "sans lien" in algorithme

    polarisation = community_detection.mesurer_polarisation(graphe, appartenance, modularite)
    assert polarisation["interactions_totales"] == 0
    assert polarisation["ratio_intra_inter"] is None


def test_jeu_sans_aucun_texte(cadre_minimal):
    cadre_minimal["text"] = ""
    cadre = _chaine_complete(cadre_minimal)

    assert not cadre["a_du_texte"].any()
    assert (cadre["sentiment"] == sentiment_analysis.NEUTRE).all()
    assert (cadre["emotion"] == emotion_analysis.AUTRE).all()
    assert (cadre["haine_label"] == hate_speech_analysis.NON_HAINEUX).all()

    profil = text_analysis.profil_lexical(cadre)
    assert profil["messages_avec_texte"] == 0
    assert "Aucun contenu textuel" in profil["message"]


def test_propagation_sur_un_jeu_vide():
    vide = pd.DataFrame(columns=[*COLONNES, "communaute_id", "a_du_texte"])
    resultat = propagation_analysis.construire_cascades(vide, {})
    assert resultat["nombre_cascades"] == 0
    assert resultat["cascades"] == []
    assert "Aucune interaction" in resultat["message"]


def test_propagation_tolere_un_parent_inexistant(cadre_minimal):
    cadre_minimal.loc[2, "parent_id"] = "i-inexistant"
    cadre = _chaine_complete(cadre_minimal)
    cadre["communaute_id"] = 1
    cadre["communaute"] = "Communauté 1"
    resultat = propagation_analysis.construire_cascades(cadre, {1: "Communauté 1"})
    assert resultat["nombre_cascades"] == 2
    assert all(cascade["profondeur"] >= 0 for cascade in resultat["cascades"])


def test_propagation_tolere_un_cycle_de_parents(cadre_minimal):
    # Deux interactions se déclarant mutuellement parentes.
    cadre_minimal.loc[1, "parent_id"] = "i002"
    cadre_minimal.loc[2, "parent_id"] = "i001"
    cadre = _chaine_complete(cadre_minimal)
    cadre["communaute_id"] = 1
    cadre["communaute"] = "Communauté 1"
    resultat = propagation_analysis.construire_cascades(cadre, {1: "Communauté 1"})
    assert resultat["nombre_cascades"] == 2


def test_utilisateur_isole_reste_un_noeud(cadre_minimal):
    supplement = pd.DataFrame(
        [
            ligne(
                platform="instagram",
                source_id="instagram_001",
                post_id="p003",
                interaction_id="p003",
                source_user="c1",
                interaction_type="post",
                text="Publication isolée",
                timestamp="2026-01-03T10:00:00",
            )
        ],
        columns=COLONNES,
    )
    cadre = _chaine_complete(pd.concat([cadre_minimal, supplement], ignore_index=True))
    graphe = network_analysis.construire_graphe(cadre)
    assert "c1" in graphe.nodes()
    assert graphe.degree("c1") == 0
