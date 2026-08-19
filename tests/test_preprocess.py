"""Tests de prétraitement du texte (français, arabe, mixte)."""

from __future__ import annotations

import pandas as pd

import load_data
import preprocess


def test_url_et_mention_retirees_hashtag_conserve():
    texte = "Bravo @ali pour #arabisation https://exemple.org/a"
    nettoye = preprocess.nettoyer_texte(texte)
    assert "exemple.org" not in nettoye
    assert "@ali" not in nettoye
    assert "arabisation" in nettoye


def test_extraction_des_entites():
    texte = "Merci @ali #école #تعريب https://exemple.org 😡"
    assert preprocess.extraire_hashtags(texte) == ["#école", "#تعريب"]
    assert preprocess.extraire_mentions(texte) == ["ali"]
    assert preprocess.extraire_urls(texte) == ["https://exemple.org"]
    assert "😡" in preprocess.extraire_emojis(texte)


def test_normalisation_arabe_diacritiques_et_alef():
    nettoye = preprocess.nettoyer_texte("أَحْمَد إسلام آفاق")
    assert "َ" not in nettoye  # tashkeel supprimé
    assert nettoye.startswith("احمد")


def test_detection_de_langue():
    assert preprocess.detecter_langue("Bonjour tout le monde") == "fr"
    assert preprocess.detecter_langue("شكرا على هذا الطرح الممتاز") == "ar"
    assert preprocess.detecter_langue("Merci beaucoup شكرا جزيلا لك") == "mixte"
    assert preprocess.detecter_langue("123 !!!") == "indetermine"


def test_mots_vides_retires():
    jetons = preprocess.jetons(preprocess.nettoyer_texte("le débat sur la langue et de"))
    assert "le" not in jetons and "de" not in jetons
    assert "débat" in jetons and "langue" in jetons


def test_texte_vide_reste_gerable():
    assert preprocess.nettoyer_texte("") == ""
    assert preprocess.jetons("") == []
    assert preprocess.detecter_langue("") == "indetermine"


def test_pretraitement_ajoute_les_colonnes(cadre_minimal):
    cadre = preprocess.pretraiter(load_data.normaliser(cadre_minimal))
    for colonne in ["raw_text", "clean_text", "hashtags", "mentions", "langue", "jetons", "a_du_texte"]:
        assert colonne in cadre.columns
    assert cadre["a_du_texte"].all()


def test_absence_totale_de_texte(cadre_minimal):
    cadre_minimal["text"] = ""
    cadre = preprocess.pretraiter(load_data.normaliser(cadre_minimal))
    assert not cadre["a_du_texte"].any()
    assert cadre["clean_text"].eq("").all()
