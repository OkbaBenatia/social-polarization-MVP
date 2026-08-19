"""Analyse de sentiment (indicative) — français, arabe et texte mixte.

Méthode : classification lexicale à base de règles, exécutée **hors ligne** en
Python. Aucun modèle d'apprentissage automatique n'est chargé par le tableau de
bord.

Choix méthodologique assumé : aucun modèle multilingue pré-entraîné n'est
utilisé ici, faute de pouvoir en documenter honnêtement les performances sur ce
corpus (français, arabe et darija mêlés). La classification est donc présentée
comme **indicative** et l'architecture reste remplaçable : il suffit de
réimplémenter ``classer_texte`` pour brancher un autre classifieur.

Aucune performance (exactitude, F1) n'est annoncée : aucune évaluation sur
corpus annoté n'a été réalisée.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import pandas as pd

POSITIF = "Positif"
NEUTRE = "Neutre"
NEGATIF = "Négatif"
CATEGORIES = [POSITIF, NEUTRE, NEGATIF]

METHODE = {
    "nom": "Classification lexicale à base de règles (implémentation du projet)",
    "version": "0.1",
    "langues": ["français", "arabe", "texte mixte français/arabe"],
    "type": "heuristique lexicale (dictionnaires + négation + intensification)",
    "modele_ml": None,
    "performance_evaluee": False,
    "limites": [
        "Aucune évaluation sur corpus annoté n'a été réalisée : aucune mesure de "
        "précision, de rappel ou de F1 ne peut être annoncée.",
        "L'ironie, le sarcasme et l'implicite ne sont pas détectés.",
        "La darija écrite en caractères latins n'est couverte que partiellement.",
        "Les dictionnaires sont volontairement courts et donc incomplets.",
    ],
    "remplacable": (
        "La fonction classer_texte() constitue le point d'extension unique : elle peut "
        "être remplacée par un classifieur entraîné sans modifier le reste du pipeline."
    ),
}

LEXIQUE_POSITIF = {
    # français
    "bravo": 2, "excellent": 2, "excellente": 2, "merci": 1, "respect": 1,
    "magnifique": 2, "utile": 1, "clair": 1, "clarté": 1, "juste": 1,
    "courage": 1, "accord": 2, "soutien": 2, "soutiens": 2, "félicitations": 2,
    "bien": 1, "bonne": 1, "bon": 1, "intéressant": 1, "documenté": 1,
    "constructif": 1, "apaisé": 1, "raison": 1, "vérité": 1, "défendre": 1,
    "partager": 1, "exactement": 1, "continuez": 1,
    # arabe
    "شكرا": 2, "ممتاز": 2, "رائع": 2, "احسنت": 2, "أحسنت": 2, "بارك": 2,
    "نؤيد": 2, "صحيح": 1, "جميل": 1, "تحية": 1, "مفيد": 1, "نعم": 1,
}

LEXIQUE_NEGATIF = {
    # français
    "honte": 2, "scandale": 2, "scandaleux": 2, "mensonge": 2, "menteur": 2,
    "catastrophe": 2, "désastre": 2, "échec": 2, "ridicule": 2, "inacceptable": 2,
    "dangereux": 1, "trahison": 2, "décevant": 2, "faux": 1, "problème": 1,
    "mépris": 2, "insupportable": 2, "marre": 2, "colère": 2, "grave": 1,
    "pire": 2, "jamais": 1, "rien": 1, "contre": 1, "refuse": 1, "refusons": 1,
    "ignorants": 2, "stupide": 2, "imbécile": 2, "débile": 2, "nul": 2,
    "envahisseurs": 2, "parasites": 2, "dégagent": 2, "dégagez": 2, "expulser": 2,
    # arabe
    "عار": 2, "كذب": 2, "كذاب": 2, "فضيحة": 2, "فشل": 2, "خيانة": 2,
    "مرفوض": 2, "خطير": 1, "سيء": 2, "غبي": 2, "حمار": 2, "كفي": 2,
    "اطردوهم": 2, "غزاة": 2,
}

MOTS_NEGATION = {"pas", "ne", "n", "plus", "jamais", "aucun", "aucune", "sans", "ni",
                 "لا", "ما", "ليس", "لم", "لن", "غير"}
MOTS_INTENSIFICATION = {"très", "trop", "vraiment", "totalement", "complètement",
                        "absolument", "extrêmement", "جدا", "كثيرا", "تماما"}

PORTEE_NEGATION = 3
SEUIL_DECISION = 1.0


def classer_texte(jetons: list[str]) -> tuple[str, float, float]:
    """Classe un message. Retourne (catégorie, score net, confiance indicative).

    Point d'extension unique du module : remplacer cette fonction suffit à
    brancher un autre classifieur.
    """
    if not jetons:
        return NEUTRE, 0.0, 0.0

    score = 0.0
    marques = 0
    for position, jeton in enumerate(jetons):
        poids_positif = LEXIQUE_POSITIF.get(jeton, 0)
        poids_negatif = LEXIQUE_NEGATIF.get(jeton, 0)
        if not poids_positif and not poids_negatif:
            continue
        marques += 1
        valeur = float(poids_positif) if poids_positif else -float(poids_negatif)

        contexte = jetons[max(0, position - PORTEE_NEGATION) : position]
        if any(mot in MOTS_NEGATION for mot in contexte):
            valeur = -valeur * 0.8
        if any(mot in MOTS_INTENSIFICATION for mot in contexte):
            valeur *= 1.4
        score += valeur

    if abs(score) < SEUIL_DECISION:
        categorie = NEUTRE
    else:
        categorie = POSITIF if score > 0 else NEGATIF

    # Confiance indicative : intensité du score rapportée au nombre de marques.
    confiance = 0.0 if not marques else min(1.0, abs(score) / (2.0 * marques))
    return categorie, round(score, 3), round(confiance, 3)


def analyser_sentiment(cadre: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes de sentiment au tableau d'interactions."""
    cadre = cadre.copy()
    resultats = [classer_texte(jetons) for jetons in cadre["jetons"]]
    cadre["sentiment"] = [resultat[0] for resultat in resultats]
    cadre["sentiment_score"] = [resultat[1] for resultat in resultats]
    cadre["sentiment_confiance"] = [resultat[2] for resultat in resultats]
    # Un message sans texte exploitable n'est pas classé.
    cadre.loc[~cadre["a_du_texte"], "sentiment"] = NEUTRE
    cadre.loc[~cadre["a_du_texte"], "sentiment_confiance"] = 0.0
    return cadre
