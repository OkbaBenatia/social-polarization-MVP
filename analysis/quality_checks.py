"""Contrôles de qualité et de provenance du jeu de données empirique.

Ces invariants protègent la validité scientifique des résultats. Ils sont
appliqués à la construction de ``data/real_interactions.csv`` et vérifiés par
la suite de tests.

Invariants :

1. aucune interaction sans ``provenance`` renseignée et reconnue ;
2. aucune ligne de provenance ``synthetic_demo`` dans un jeu empirique ;
3. aucun ``interaction_id`` dupliqué ;
4. aucune interaction sans ``source_id`` rattaché aux sources déclarées ;
5. aucune réponse dont le ``parent_id`` ne désigne aucune ligne connue ;
6. aucune statistique empirique calculée sur des données synthétiques.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import provenance as prov  # noqa: E402


class ErreurQualite(Exception):
    """Violation d'un invariant de qualité ou de provenance."""


def _colonne(cadre: pd.DataFrame, nom: str) -> pd.Series:
    if nom not in cadre.columns:
        raise ErreurQualite(f"Colonne « {nom} » absente du jeu de données.")
    return cadre[nom].fillna("").astype(str).str.strip()


def verifier_provenance_renseignee(cadre: pd.DataFrame) -> list[str]:
    """Invariant 1 — chaque ligne déclare une provenance reconnue."""
    anomalies = []
    valeurs = _colonne(cadre, "provenance").str.lower()
    vides = cadre.loc[valeurs == ""]
    if len(vides):
        anomalies.append(
            f"{len(vides)} interaction(s) sans provenance renseignée "
            f"(ex. {', '.join(vides['interaction_id'].astype(str).head(3))})."
        )
    inconnues = sorted(set(valeurs) - set(prov.PROVENANCES) - {""})
    if inconnues:
        anomalies.append(
            f"Provenance(s) inconnue(s) : {', '.join(inconnues)}. "
            f"Valeurs admises : {', '.join(prov.PROVENANCES)}."
        )
    return anomalies


def verifier_absence_de_synthetique(cadre: pd.DataFrame) -> list[str]:
    """Invariant 2 — aucune ligne synthétique dans un jeu empirique."""
    valeurs = _colonne(cadre, "provenance").str.lower()
    synthetiques = cadre.loc[valeurs == prov.SYNTHETIC_DEMO]
    if len(synthetiques):
        return [
            f"{len(synthetiques)} ligne(s) de provenance « {prov.SYNTHETIC_DEMO} » "
            "présentes dans un jeu de données empirique. Les données synthétiques ne "
            "doivent jamais être mélangées aux résultats empiriques."
        ]
    return []


def verifier_doublons(cadre: pd.DataFrame) -> list[str]:
    """Invariant 3 — aucun identifiant d'interaction dupliqué."""
    identifiants = _colonne(cadre, "interaction_id")
    doublons = identifiants[identifiants.duplicated(keep=False) & (identifiants != "")]
    if len(doublons):
        uniques = sorted(set(doublons))
        return [
            f"{len(uniques)} identifiant(s) d'interaction dupliqué(s) : "
            f"{', '.join(uniques[:5])}."
        ]
    return []


def verifier_sources(cadre: pd.DataFrame, sources_declarees: set[str]) -> list[str]:
    """Invariant 4 — chaque interaction est rattachée à une source déclarée."""
    anomalies = []
    valeurs = _colonne(cadre, "source_id")
    vides = int((valeurs == "").sum())
    if vides:
        anomalies.append(f"{vides} interaction(s) sans source_id.")
    if sources_declarees:
        inconnues = sorted(set(valeurs) - sources_declarees - {""})
        if inconnues:
            anomalies.append(
                f"source_id absent(s) de data/sources.json : {', '.join(inconnues)}."
            )
    return anomalies


def verifier_filiation(cadre: pd.DataFrame) -> list[str]:
    """Invariant 5 — tout parent_id renseigné désigne une ligne connue."""
    identifiants = set(_colonne(cadre, "interaction_id")) | set(_colonne(cadre, "post_id"))
    parents = _colonne(cadre, "parent_id")
    orphelins = sorted({p for p in parents if p and p not in identifiants})
    if orphelins:
        return [
            f"{len(orphelins)} parent_id ne correspond à aucune interaction du jeu : "
            f"{', '.join(orphelins[:5])}."
        ]
    return []


def controler(cadre: pd.DataFrame, sources_declarees: set[str] | None = None) -> list[str]:
    """Applique tous les invariants et retourne la liste des anomalies."""
    anomalies: list[str] = []
    anomalies += verifier_provenance_renseignee(cadre)
    anomalies += verifier_absence_de_synthetique(cadre)
    anomalies += verifier_doublons(cadre)
    anomalies += verifier_sources(cadre, sources_declarees or set())
    anomalies += verifier_filiation(cadre)
    return anomalies


def controler_ou_echouer(cadre: pd.DataFrame, sources_declarees: set[str] | None = None) -> None:
    anomalies = controler(cadre, sources_declarees)
    if anomalies:
        raise ErreurQualite(
            "Contrôle de qualité échoué :\n  - " + "\n  - ".join(anomalies)
        )
