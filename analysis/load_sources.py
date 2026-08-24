"""Chargement des sources de l'étude et détermination de leur statut de collecte.

Le statut d'une source n'est jamais déclaré arbitrairement : il est déduit de ce
qui a réellement été récupéré (rapport de collecte) et de ce qui a réellement
été importé (jeu de données analysé).

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PLATEFORMES_CONNUES = {"facebook", "x", "instagram"}

STATUT_DISPONIBLE = "Données disponibles"
STATUT_PARTIEL = "Accès partiel"
STATUT_IMPORT_MANUEL = "Import manuel requis"
STATUT_DEMONSTRATION = "Données de démonstration"

CHAMPS_OBLIGATOIRES = ("source_id", "platform", "url")


class ErreurSources(Exception):
    """Erreur de lecture ou de validation du fichier des sources."""


def charger_sources(chemin: Path) -> list[dict[str, Any]]:
    """Lit et valide ``data/sources.json``."""
    if not chemin.exists():
        raise ErreurSources(
            f"Fichier des sources introuvable : {chemin}. "
            "Créez data/sources.json à partir de la documentation (docs/DONNEES.md)."
        )
    try:
        brut = json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        raise ErreurSources(f"Fichier des sources illisible (JSON invalide) : {erreur}") from erreur

    sources = brut.get("sources") if isinstance(brut, dict) else brut
    if not isinstance(sources, list) or not sources:
        raise ErreurSources(
            "Le fichier des sources ne contient aucune source exploitable "
            "(liste « sources » vide ou absente)."
        )

    identifiants: set[str] = set()
    validees: list[dict[str, Any]] = []
    for position, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise ErreurSources(f"Source n°{position} : format inattendu (objet JSON attendu).")
        manquants = [champ for champ in CHAMPS_OBLIGATOIRES if not source.get(champ)]
        if manquants:
            raise ErreurSources(
                f"Source n°{position} : champs obligatoires manquants : {', '.join(manquants)}."
            )
        identifiant = str(source["source_id"]).strip()
        if identifiant in identifiants:
            raise ErreurSources(f"Identifiant de source dupliqué : {identifiant}.")
        identifiants.add(identifiant)
        plateforme = str(source["platform"]).strip().lower()
        validees.append(
            {
                "source_id": identifiant,
                "platform": plateforme,
                "plateforme_connue": plateforme in PLATEFORMES_CONNUES,
                "url": str(source["url"]).strip(),
                "type_contenu": source.get("type_contenu", ""),
                "thematique_declaree": source.get("thematique_declaree", ""),
            }
        )
    return validees


def charger_rapport_collecte(chemin: Path) -> dict[str, dict[str, Any]]:
    """Lit ``data/collection_report.json`` s'il existe. Absent = collecte non tentée."""
    if not chemin.exists():
        return {}
    try:
        rapport = json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {
        resultat["source_id"]: resultat
        for resultat in rapport.get("resultats", [])
        if isinstance(resultat, dict) and resultat.get("source_id")
    }


def statut_source(
    source: dict[str, Any],
    collecte: dict[str, Any] | None,
    interactions_importees: int,
    jeu_synthetique: bool,
) -> tuple[str, str]:
    """Détermine le statut d'une source et la méthode d'acquisition associée.

    Retourne le couple (statut, méthode d'acquisition).
    """
    if interactions_importees > 0 and jeu_synthetique:
        return (
            STATUT_DEMONSTRATION,
            "Jeu de données synthétique de démonstration (aucune donnée réelle collectée)",
        )
    if interactions_importees > 0:
        return STATUT_DISPONIBLE, "Import manuel / export au format normalisé"
    if collecte and collecte.get("accessible"):
        return (
            STATUT_PARTIEL,
            "Métadonnées publiques uniquement (aucune interaction récupérée)",
        )
    if collecte:
        return STATUT_IMPORT_MANUEL, "Collecte automatique impossible — import manuel nécessaire"
    return STATUT_IMPORT_MANUEL, "Collecte non tentée — import manuel nécessaire"


def construire_etat_sources(
    sources: list[dict[str, Any]],
    rapport_collecte: dict[str, dict[str, Any]],
    compte_interactions: dict[str, int],
    compte_publications: dict[str, int],
    jeu_synthetique: bool,
) -> list[dict[str, Any]]:
    """Assemble l'état complet de chaque source pour le tableau de bord."""
    etat: list[dict[str, Any]] = []
    for source in sources:
        collecte = rapport_collecte.get(source["source_id"])
        interactions = int(compte_interactions.get(source["source_id"], 0))
        statut, methode = statut_source(source, collecte, interactions, jeu_synthetique)
        limites = list(collecte.get("limites", [])) if collecte else [
            "Aucune tentative de collecte automatique n'a été enregistrée pour cette source."
        ]
        etat.append(
            {
                "source_id": source["source_id"],
                "plateforme": source["platform"],
                "url": source["url"],
                "type_contenu": source["type_contenu"],
                "statut": statut,
                "methode_acquisition": methode,
                "interactions": interactions,
                "publications": int(compte_publications.get(source["source_id"], 0)),
                "collecte_tentee": collecte is not None,
                "http_status": collecte.get("http_status") if collecte else None,
                "robots_txt": collecte.get("robots_txt", "") if collecte else "",
                "mur_authentification_detecte": bool(
                    collecte.get("mur_authentification_detecte") if collecte else False
                ),
                "metadonnees_publiques": collecte.get("metadonnees_publiques", {})
                if collecte
                else {},
                "voies_evaluees": list(collecte.get("voies_evaluees", [])) if collecte else [],
                "donnees_recuperees": list(collecte.get("donnees_recuperees", []))
                if collecte
                else [],
                "donnees_manquantes": list(collecte.get("donnees_manquantes", []))
                if collecte
                else [],
                "import_manuel_requis": bool(collecte.get("import_manuel_requis", True))
                if collecte
                else True,
                "limites": limites,
            }
        )
    return etat
