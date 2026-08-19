"""Estimation indicative de la toxicité et du discours potentiellement haineux.

Trois catégories mutuellement exclusives sont distinguées :

* ``Non haineux`` ;
* ``Toxique / offensant`` : insulte, mépris, disqualification d'un interlocuteur ;
* ``Potentiellement haineux`` : contenu qui **cible un groupe** et l'associe à
  une formulation d'exclusion, de déshumanisation ou de rejet collectif.

La distinction repose sur une règle de **co-occurrence** (mention d'un groupe ×
formulation d'exclusion), volontairement conservatrice afin de limiter les faux
positifs sur des messages simplement critiques.

Précautions terminologiques imposées au projet :

* on ne parle jamais d'« utilisateur haineux » mais de « contenu classifié comme
  potentiellement haineux » ;
* sentiment négatif ≠ colère ≠ toxicité ≠ discours haineux ≠ polarisation ;
* aucune performance (précision, rappel, F1) n'est annoncée : aucune évaluation
  sur corpus annoté n'a été réalisée.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import pandas as pd

NON_HAINEUX = "Non haineux"
TOXIQUE = "Toxique / offensant"
POTENTIELLEMENT_HAINEUX = "Potentiellement haineux"
CATEGORIES = [NON_HAINEUX, TOXIQUE, POTENTIELLEMENT_HAINEUX]

METHODE = {
    "nom": "Détection lexicale indicative de toxicité et de discours haineux "
    "(implémentation du projet)",
    "version": "0.1",
    "langues": ["français", "arabe", "texte mixte français/arabe"],
    "type": "heuristique lexicale ; règle de co-occurrence groupe × exclusion",
    "performance_evaluee": False,
    "avertissement": (
        "Estimation indicative portant sur des contenus, jamais sur des personnes. "
        "Un contenu classé « potentiellement haineux » signale un signal lexical à "
        "vérifier manuellement, non une qualification juridique."
    ),
    "limites": [
        "Aucune évaluation sur corpus annoté : aucune performance ne peut être annoncée.",
        "Les formulations implicites, codées ou ironiques échappent à la détection.",
        "Une citation ou une dénonciation d'un propos haineux peut être classée à tort.",
        "Les dictionnaires sont courts, non exhaustifs, et biaisés vers le français.",
        "La darija en caractères latins n'est couverte que partiellement.",
    ],
}

# Termes disqualifiant un interlocuteur (registre offensant).
LEXIQUE_TOXIQUE = {
    "idiot", "idiote", "imbécile", "imbeciles", "imbéciles", "stupide", "stupides",
    "débile", "ignorant", "ignorants", "ignorante", "menteur", "menteuse",
    "ridicule", "nul", "nulle", "crétin", "abruti", "tais", "taire",
    "غبي", "حمار", "كذاب", "احمق", "أحمق",
}

# Désignations collectives susceptibles d'être ciblées. Leur seule présence
# n'entraîne AUCUNE classification : elles doivent co-occurrer avec un terme
# d'exclusion ou de déshumanisation.
DESIGNATIONS_COLLECTIVES = {
    "immigrés", "immigres", "immigrants", "étrangers", "etrangers", "migrants",
    "musulmans", "chrétiens", "chretiens", "juifs", "arabes", "berbères", "berberes",
    "eux", "gens", "ceux",
    "المهاجرين", "الاجانب", "الأجانب", "المسلمين", "العرب",
}

# Formulations d'exclusion, de rejet collectif ou de déshumanisation.
LEXIQUE_EXCLUSION = {
    "dégagez", "degagez", "dégagent", "dehors", "expulser", "expulsion", "chasser",
    "renvoyer", "renvoyez", "partir", "envahisseurs", "invasion", "parasites",
    "vermine", "virus", "éliminer", "eliminer", "place",
    "اطردوهم", "غزاة", "يخرجوا",
}

SEUIL_TOXICITE = 1


def classer_texte(jetons: list[str]) -> tuple[str, float, list[str]]:
    """Retourne (catégorie, confiance indicative, signaux détectés)."""
    if not jetons:
        return NON_HAINEUX, 0.0, []

    ensemble = set(jetons)
    signaux_toxiques = sorted(ensemble & LEXIQUE_TOXIQUE)
    designations = sorted(ensemble & DESIGNATIONS_COLLECTIVES)
    exclusions = sorted(ensemble & LEXIQUE_EXCLUSION)

    if designations and exclusions:
        # Co-occurrence groupe × exclusion : signal le plus fort du dispositif.
        force = len(designations) + len(exclusions)
        confiance = min(0.9, 0.45 + 0.12 * force)
        return (
            POTENTIELLEMENT_HAINEUX,
            round(confiance, 3),
            [f"groupe:{terme}" for terme in designations]
            + [f"exclusion:{terme}" for terme in exclusions],
        )

    if len(signaux_toxiques) >= SEUIL_TOXICITE:
        confiance = min(0.85, 0.35 + 0.15 * len(signaux_toxiques))
        return TOXIQUE, round(confiance, 3), [f"offense:{terme}" for terme in signaux_toxiques]

    return NON_HAINEUX, 0.0, []


def analyser_discours_haineux(cadre: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes de classification toxicité/haine au tableau."""
    cadre = cadre.copy()
    resultats = [classer_texte(jetons) for jetons in cadre["jetons"]]
    cadre["haine_label"] = [resultat[0] for resultat in resultats]
    cadre["haine_confiance"] = [resultat[1] for resultat in resultats]
    cadre["haine_signaux"] = [resultat[2] for resultat in resultats]
    cadre.loc[~cadre["a_du_texte"], "haine_label"] = NON_HAINEUX
    cadre.loc[~cadre["a_du_texte"], "haine_confiance"] = 0.0
    return cadre
