"""Classification indicative « colère » / « soutien » / « autre ou neutre ».

Objectif : comparer les communautés selon la proportion de messages classés
comme exprimant de la colère ou du soutien.

Ces catégories décrivent le **contenu d'un message**, jamais l'état
psychologique d'une personne. Il s'agit d'une « classification automatique
indicative du contenu ».

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import re

import pandas as pd

COLERE = "Colère"
SOUTIEN = "Soutien / approbation"
AUTRE = "Autre / neutre"
CATEGORIES = [COLERE, SOUTIEN, AUTRE]

METHODE = {
    "nom": "Classification lexicale indicative colère/soutien (implémentation du projet)",
    "version": "0.1",
    "langues": ["français", "arabe", "texte mixte français/arabe"],
    "type": "heuristique lexicale + marqueurs typographiques",
    "performance_evaluee": False,
    "avertissement": (
        "Classification automatique indicative du contenu. Elle ne décrit pas l'état "
        "émotionnel réel d'une personne et ne doit pas être interprétée comme tel."
    ),
    "limites": [
        "Aucune évaluation sur corpus annoté : aucune performance ne peut être annoncée.",
        "La colère implicite, l'ironie et le second degré ne sont pas détectés.",
        "Les marqueurs typographiques (majuscules, points d'exclamation) sont des indices "
        "faibles et culturellement variables.",
    ],
}

LEXIQUE_COLERE = {
    "honte": 2, "scandale": 2, "scandaleux": 2, "marre": 3, "suffit": 3,
    "assez": 2, "insupportable": 2, "colère": 3, "rage": 3, "dégoût": 2,
    "inadmissible": 2, "inacceptable": 2, "mépris": 2, "trahison": 2,
    "moquent": 2, "moque": 2, "réveillez": 2, "cirque": 2, "mensonges": 2,
    "ment": 2, "mentent": 2, "trop": 1, "dehors": 2, "dégagez": 3,
    "كفي": 3, "عار": 3, "فضيحة": 2, "غاضب": 3, "اطردوهم": 3,
}

LEXIQUE_SOUTIEN = {
    "soutien": 3, "soutiens": 3, "soutenons": 3, "bravo": 3, "merci": 2,
    "accord": 3, "exactement": 2, "félicitations": 3, "respect": 2,
    "courage": 2, "continuez": 2, "défendre": 1, "partage": 1, "excellent": 2,
    "excellente": 2, "raison": 2, "lâchez": 2, "nombreux": 1,
    "شكرا": 2, "نؤيد": 3, "بارك": 3, "احسنت": 3, "أحسنت": 3, "تحية": 2, "ممتاز": 2,
}

MOTIF_EXCLAMATIONS = re.compile(r"!{2,}")
MOTIF_MAJUSCULES = re.compile(r"\b[A-ZÀ-Ö]{4,}\b")

SEUIL_DECISION = 2.0


def classer_texte(jetons: list[str], texte_brut: str) -> tuple[str, float, float]:
    """Retourne (catégorie, score dominant, confiance indicative)."""
    if not jetons:
        return AUTRE, 0.0, 0.0

    score_colere = sum(LEXIQUE_COLERE.get(jeton, 0) for jeton in jetons)
    score_soutien = sum(LEXIQUE_SOUTIEN.get(jeton, 0) for jeton in jetons)

    # Marqueurs typographiques : indices faibles, pondérés faiblement.
    if MOTIF_EXCLAMATIONS.search(texte_brut):
        score_colere += 1
    if len(MOTIF_MAJUSCULES.findall(texte_brut)) >= 2:
        score_colere += 1
    if "😡" in texte_brut or "🤬" in texte_brut:
        score_colere += 1
    if "👏" in texte_brut or "💯" in texte_brut or "🙏" in texte_brut:
        score_soutien += 1

    if max(score_colere, score_soutien) < SEUIL_DECISION or score_colere == score_soutien:
        return AUTRE, 0.0, 0.0

    if score_colere > score_soutien:
        categorie, dominant, oppose = COLERE, score_colere, score_soutien
    else:
        categorie, dominant, oppose = SOUTIEN, score_soutien, score_colere

    confiance = min(1.0, (dominant - oppose) / (dominant + oppose + 2.0))
    return categorie, float(dominant), round(confiance, 3)


def analyser_emotions(cadre: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes colère/soutien au tableau d'interactions."""
    cadre = cadre.copy()
    resultats = [
        classer_texte(jetons, texte)
        for jetons, texte in zip(cadre["jetons"], cadre["raw_text"])
    ]
    cadre["emotion"] = [resultat[0] for resultat in resultats]
    cadre["emotion_score"] = [resultat[1] for resultat in resultats]
    cadre["emotion_confiance"] = [resultat[2] for resultat in resultats]
    cadre.loc[~cadre["a_du_texte"], "emotion"] = AUTRE
    cadre.loc[~cadre["a_du_texte"], "emotion_confiance"] = 0.0
    return cadre
