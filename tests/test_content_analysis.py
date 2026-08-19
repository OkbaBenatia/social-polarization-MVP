"""Tests des analyses de contenu : lexique, sentiment, émotions, toxicité."""

from __future__ import annotations

import pandas as pd

import emotion_analysis
import hate_speech_analysis
import load_data
import preprocess
import sentiment_analysis
import text_analysis


def _preparer(cadre_brut) -> pd.DataFrame:
    return preprocess.pretraiter(load_data.normaliser(cadre_brut))


# --- Analyse lexicale -------------------------------------------------------
def test_profil_lexical_complet(cadre_minimal):
    profil = text_analysis.profil_lexical(_preparer(cadre_minimal))
    assert profil["messages_avec_texte"] == 7
    assert profil["mots"] and "terme" in profil["mots"][0]
    assert isinstance(profil["bigrammes"], list)
    assert profil["tfidf"]


def test_profil_lexical_sans_texte(cadre_minimal):
    cadre_minimal["text"] = ""
    profil = text_analysis.profil_lexical(_preparer(cadre_minimal))
    assert profil["messages_avec_texte"] == 0
    assert profil["mots"] == [] and profil["tfidf"] == []
    assert "Aucun contenu textuel" in profil["message"]


def test_profils_par_communaute_et_plateforme(cadre_minimal):
    cadre = _preparer(cadre_minimal)
    cadre["communaute_id"] = [1, 1, 1, 2, 2, 2, 1]
    resultat = text_analysis.analyser_contenu(
        cadre, {1: "Communauté 1", 2: "Communauté 2"}, ["facebook", "x"]
    )
    assert "toutes|toutes" in resultat["profils"]
    assert "1|facebook" in resultat["profils"]
    assert "2|x" in resultat["profils"]
    assert resultat["profils"]["toutes|toutes"]["messages_avec_texte"] == 7


# --- Sentiment ---------------------------------------------------------------
def test_sentiment_positif_negatif_neutre():
    positif, _, _ = sentiment_analysis.classer_texte(["bravo", "excellent", "merci"])
    negatif, _, _ = sentiment_analysis.classer_texte(["honte", "scandale", "mensonge"])
    neutre, _, _ = sentiment_analysis.classer_texte(["rapport", "publié", "page"])
    assert positif == sentiment_analysis.POSITIF
    assert negatif == sentiment_analysis.NEGATIF
    assert neutre == sentiment_analysis.NEUTRE


def test_sentiment_arabe():
    categorie, _, _ = sentiment_analysis.classer_texte(["شكرا", "ممتاز"])
    assert categorie == sentiment_analysis.POSITIF


def test_sentiment_texte_vide_est_neutre():
    categorie, score, confiance = sentiment_analysis.classer_texte([])
    assert categorie == sentiment_analysis.NEUTRE
    assert score == 0.0 and confiance == 0.0


def test_aucune_performance_annoncee():
    assert sentiment_analysis.METHODE["performance_evaluee"] is False
    assert sentiment_analysis.METHODE["modele_ml"] is None
    assert sentiment_analysis.METHODE["limites"]


def test_colonnes_de_sentiment_ajoutees(cadre_minimal):
    cadre = sentiment_analysis.analyser_sentiment(_preparer(cadre_minimal))
    assert set(cadre["sentiment"]).issubset(set(sentiment_analysis.CATEGORIES))
    assert cadre["sentiment_confiance"].between(0, 1).all()


# --- Colère / soutien ---------------------------------------------------------
def test_colere_et_soutien_distingues():
    colere, _, _ = emotion_analysis.classer_texte(["honte", "marre", "suffit"], "C'est une honte !!!")
    soutien, _, _ = emotion_analysis.classer_texte(["bravo", "soutien", "accord"], "Bravo")
    autre, _, _ = emotion_analysis.classer_texte(["rapport", "page"], "Rapport page 42")
    assert colere == emotion_analysis.COLERE
    assert soutien == emotion_analysis.SOUTIEN
    assert autre == emotion_analysis.AUTRE


def test_emotion_distincte_du_sentiment(cadre_minimal):
    cadre = emotion_analysis.analyser_emotions(
        sentiment_analysis.analyser_sentiment(_preparer(cadre_minimal))
    )
    # Les deux dimensions existent séparément et ne sont pas confondues.
    assert "sentiment" in cadre.columns and "emotion" in cadre.columns
    assert set(cadre["emotion"]).issubset(set(emotion_analysis.CATEGORIES))


def test_avertissement_sur_l_etat_psychologique():
    assert "état émotionnel réel" in emotion_analysis.METHODE["avertissement"]


# --- Toxicité et discours haineux ---------------------------------------------
def test_contenu_offensant_classe_toxique():
    label, confiance, signaux = hate_speech_analysis.classer_texte(["bande", "ignorants", "stupide"])
    assert label == hate_speech_analysis.TOXIQUE
    assert 0 < confiance <= 1
    assert signaux


def test_cooccurrence_groupe_exclusion_classe_potentiellement_haineux():
    label, confiance, signaux = hate_speech_analysis.classer_texte(
        ["expulser", "immigrés", "envahisseurs"]
    )
    assert label == hate_speech_analysis.POTENTIELLEMENT_HAINEUX
    assert confiance > 0.5
    assert any(signal.startswith("groupe:") for signal in signaux)
    assert any(signal.startswith("exclusion:") for signal in signaux)


def test_mention_d_un_groupe_seule_n_est_pas_haineuse():
    label, _, _ = hate_speech_analysis.classer_texte(["immigrés", "travail", "économie"])
    assert label == hate_speech_analysis.NON_HAINEUX


def test_critique_negative_seule_n_est_pas_haineuse():
    label, _, _ = hate_speech_analysis.classer_texte(["échec", "politique", "décevant"])
    assert label == hate_speech_analysis.NON_HAINEUX


def test_texte_vide_non_haineux():
    label, confiance, signaux = hate_speech_analysis.classer_texte([])
    assert label == hate_speech_analysis.NON_HAINEUX
    assert confiance == 0.0 and signaux == []


def test_categories_de_haine_distinctes_du_sentiment(cadre_minimal):
    cadre = hate_speech_analysis.analyser_discours_haineux(
        sentiment_analysis.analyser_sentiment(_preparer(cadre_minimal))
    )
    negatifs = cadre[cadre["sentiment"] == sentiment_analysis.NEGATIF]
    # Un sentiment négatif n'implique pas une classification haineuse.
    assert (negatifs["haine_label"] == hate_speech_analysis.NON_HAINEUX).any()


def test_aucune_performance_annoncee_pour_la_haine():
    assert hate_speech_analysis.METHODE["performance_evaluee"] is False
    assert "jamais sur des personnes" in hate_speech_analysis.METHODE["avertissement"]
