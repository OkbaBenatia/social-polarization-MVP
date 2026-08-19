"""Analyse lexicale : mots fréquents, bigrammes, TF-IDF et hashtags.

L'analyse est réalisée globalement puis par communauté et par plateforme, afin
de permettre une comparaison des champs lexicaux (RQ3).

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

TAILLE_TOP = 20
MIN_DOCUMENTS_TFIDF = 3


def _compter_mots(jetons_par_document: list[list[str]], taille: int = TAILLE_TOP) -> list[dict]:
    compteur: Counter[str] = Counter()
    for jetons in jetons_par_document:
        compteur.update(jetons)
    return [{"terme": terme, "occurrences": nombre} for terme, nombre in compteur.most_common(taille)]


def _compter_bigrammes(
    jetons_par_document: list[list[str]], taille: int = TAILLE_TOP
) -> list[dict]:
    compteur: Counter[str] = Counter()
    for jetons in jetons_par_document:
        for premier, second in zip(jetons, jetons[1:]):
            compteur[f"{premier} {second}"] += 1
    return [{"terme": terme, "occurrences": nombre} for terme, nombre in compteur.most_common(taille)]


def _compter_hashtags(listes_hashtags: list[list[str]], taille: int = TAILLE_TOP) -> list[dict]:
    compteur: Counter[str] = Counter()
    for hashtags in listes_hashtags:
        compteur.update(hashtags)
    return [
        {"terme": terme, "occurrences": nombre} for terme, nombre in compteur.most_common(taille)
    ]


def termes_caracteristiques(
    documents: list[str], taille: int = TAILLE_TOP
) -> list[dict]:
    """Termes les plus caractéristiques d'un ensemble de documents (TF-IDF).

    Le score retourné est la moyenne des poids TF-IDF du terme sur les documents
    du sous-ensemble analysé.
    """
    documents = [document for document in documents if document.strip()]
    if len(documents) < MIN_DOCUMENTS_TFIDF:
        return []
    try:
        vectoriseur = TfidfVectorizer(
            max_features=4000,
            ngram_range=(1, 1),
            min_df=1,
            sublinear_tf=True,
            token_pattern=r"(?u)\b\w\w+\b",
        )
        matrice = vectoriseur.fit_transform(documents)
    except ValueError:
        return []
    moyennes = matrice.mean(axis=0).A1
    vocabulaire = vectoriseur.get_feature_names_out()
    ordre = moyennes.argsort()[::-1][:taille]
    return [
        {"terme": str(vocabulaire[index]), "score": round(float(moyennes[index]), 4)}
        for index in ordre
        if moyennes[index] > 0
    ]


def profil_lexical(sous_ensemble: pd.DataFrame, taille: int = TAILLE_TOP) -> dict:
    """Profil lexical complet d'un sous-ensemble d'interactions."""
    avec_texte = sous_ensemble[sous_ensemble["a_du_texte"]]
    if avec_texte.empty:
        return {
            "messages_avec_texte": 0,
            "mots": [],
            "bigrammes": [],
            "tfidf": [],
            "hashtags": [],
            "message": "Aucun contenu textuel disponible pour cette sélection.",
        }
    jetons_par_document = avec_texte["jetons"].tolist()
    return {
        "messages_avec_texte": int(len(avec_texte)),
        "mots": _compter_mots(jetons_par_document, taille),
        "bigrammes": _compter_bigrammes(jetons_par_document, taille),
        "tfidf": termes_caracteristiques(
            [" ".join(jetons) for jetons in jetons_par_document], taille
        ),
        "hashtags": _compter_hashtags(avec_texte["hashtags"].tolist(), taille),
        "message": "",
    }


def analyser_contenu(
    cadre: pd.DataFrame, noms_communautes: dict[int, str], plateformes: list[str]
) -> dict:
    """Construit les profils lexicaux pour chaque combinaison communauté × plateforme."""
    profils: dict[str, dict] = {}
    identifiants = ["toutes"] + [str(identifiant) for identifiant in sorted(noms_communautes)]
    liste_plateformes = ["toutes"] + sorted(plateformes)

    for identifiant in identifiants:
        for plateforme in liste_plateformes:
            selection = cadre
            if identifiant != "toutes":
                selection = selection[selection["communaute_id"] == int(identifiant)]
            if plateforme != "toutes":
                selection = selection[selection["platform"] == plateforme]
            profils[f"{identifiant}|{plateforme}"] = profil_lexical(selection)

    return {
        "profils": profils,
        "communautes": [
            {"id": "toutes", "nom": "Toutes les communautés"},
            *[
                {"id": str(identifiant), "nom": nom}
                for identifiant, nom in sorted(noms_communautes.items())
            ],
        ],
        "plateformes": [
            {"id": "toutes", "nom": "Toutes les plateformes"},
            *[{"id": plateforme, "nom": plateforme.capitalize()} for plateforme in sorted(plateformes)],
        ],
        "taille_top": TAILLE_TOP,
        "methode": (
            "Fréquences brutes après suppression des mots vides (français et arabe), "
            "bigrammes consécutifs, et pondération TF-IDF (scikit-learn) calculée sur le "
            "sous-ensemble sélectionné."
        ),
    }
