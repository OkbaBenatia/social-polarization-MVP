"""Analyse simple de la propagation (cascades d'interactions).

Les cascades sont reconstruites à partir de ``parent_id`` : une publication
constitue la racine, les commentaires, réponses, partages, reposts et citations
en constituent les branches.

Aucun modèle de diffusion (SIR, Hawkes, etc.) n'est implémenté : l'analyse reste
descriptive.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import pandas as pd

NOMBRE_CASCADES_DETAILLEES = 12
NOEUDS_MAX_PAR_ARBRE = 120


def _proportion(valeurs: pd.Series, cible: str) -> float:
    if valeurs.empty:
        return 0.0
    return round(float((valeurs == cible).mean()), 4)


def construire_cascades(cadre: pd.DataFrame, noms_communautes: dict[int, str]) -> dict:
    """Reconstruit les cascades et calcule leurs indicateurs descriptifs."""
    if cadre.empty:
        return {
            "nombre_cascades": 0,
            "cascades": [],
            "statistiques": {},
            "message": "Aucune interaction disponible pour l'analyse de propagation.",
        }

    par_identifiant = {
        ligne.interaction_id: ligne for ligne in cadre.itertuples(index=False)
    }

    # Profondeur : distance à la racine en remontant parent_id.
    profondeurs: dict[str, int] = {}

    def profondeur(identifiant: str, vus: set[str] | None = None) -> int:
        if identifiant in profondeurs:
            return profondeurs[identifiant]
        vus = vus or set()
        if identifiant in vus:  # protection contre un cycle dans les données
            return 0
        vus.add(identifiant)
        ligne = par_identifiant.get(identifiant)
        if ligne is None:
            return 0
        parent = ligne.parent_id
        if not parent or parent == identifiant or parent not in par_identifiant:
            valeur = 0
        else:
            valeur = profondeur(parent, vus) + 1
        profondeurs[identifiant] = valeur
        return valeur

    cadre = cadre.copy()
    cadre["profondeur"] = [profondeur(identifiant) for identifiant in cadre["interaction_id"]]

    cascades = []
    for post_id, groupe in cadre.groupby("post_id", sort=False):
        if not post_id:
            continue
        racines = groupe[groupe["interaction_type"] == "post"]
        horodatages = groupe["horodatage"].dropna()
        duree_minutes = None
        if len(horodatages) >= 2:
            duree_minutes = round(
                (horodatages.max() - horodatages.min()).total_seconds() / 60.0, 1
            )
        communautes = sorted(
            {
                int(identifiant)
                for identifiant in groupe["communaute_id"].dropna().tolist()
                if int(identifiant) > 0
            }
        )
        avec_texte = groupe[groupe["a_du_texte"]]

        cascades.append(
            {
                "cascade_id": str(post_id),
                "source_id": str(groupe["source_id"].iloc[0]),
                "plateforme": str(groupe["platform"].iloc[0]),
                "url": str(groupe["url"].iloc[0]),
                "auteur_racine": str(racines["auteur_etiquette"].iloc[0])
                if not racines.empty
                else "",
                "taille": int(len(groupe)),
                "profondeur": int(groupe["profondeur"].max()),
                "participants": int(
                    len((set(groupe["source_user"]) | set(groupe["target_user"])) - {""})
                ),
                "duree_minutes": duree_minutes,
                "communautes_atteintes": [
                    noms_communautes.get(identifiant, f"Communauté {identifiant}")
                    for identifiant in communautes
                ],
                "nombre_communautes_atteintes": len(communautes),
                "debut": horodatages.min().isoformat() if not horodatages.empty else None,
                "fin": horodatages.max().isoformat() if not horodatages.empty else None,
                "taux_negatif": _proportion(avec_texte["sentiment"], "Négatif"),
                "taux_colere": _proportion(avec_texte["emotion"], "Colère"),
                "taux_soutien": _proportion(avec_texte["emotion"], "Soutien / approbation"),
                "taux_potentiellement_haineux": _proportion(
                    avec_texte["haine_label"], "Potentiellement haineux"
                ),
                "taux_toxique": _proportion(avec_texte["haine_label"], "Toxique / offensant"),
                "repartition_types": {
                    str(type_interaction): int(nombre)
                    for type_interaction, nombre in groupe["interaction_type"]
                    .value_counts()
                    .items()
                },
            }
        )

    cascades.sort(key=lambda cascade: (-cascade["taille"], cascade["cascade_id"]))

    # Arbres détaillés pour les principales cascades (visualisation).
    identifiants_detailles = {
        cascade["cascade_id"] for cascade in cascades[:NOMBRE_CASCADES_DETAILLEES]
    }
    arbres: dict[str, list[dict]] = {}
    for post_id in identifiants_detailles:
        groupe = cadre[cadre["post_id"] == post_id].sort_values("profondeur")
        noeuds = []
        for ligne in groupe.head(NOEUDS_MAX_PAR_ARBRE).itertuples(index=False):
            identifiant_communaute = int(ligne.communaute_id) if ligne.communaute_id else 0
            noeuds.append(
                {
                    "id": str(ligne.interaction_id),
                    "parent": str(ligne.parent_id)
                    if ligne.parent_id and ligne.parent_id != ligne.interaction_id
                    else None,
                    "type": str(ligne.interaction_type),
                    "profondeur": int(ligne.profondeur),
                    "auteur": str(ligne.auteur_etiquette),
                    "communaute": noms_communautes.get(
                        identifiant_communaute, "Non affecté"
                    ),
                    "communaute_id": identifiant_communaute,
                    "sentiment": str(ligne.sentiment),
                    "emotion": str(ligne.emotion),
                    "haine_label": str(ligne.haine_label),
                    "horodatage": ligne.horodatage.isoformat()
                    if pd.notna(ligne.horodatage)
                    else None,
                }
            )
        arbres[str(post_id)] = noeuds

    tailles = [cascade["taille"] for cascade in cascades]
    profondeurs_max = [cascade["profondeur"] for cascade in cascades]
    durees = [
        cascade["duree_minutes"] for cascade in cascades if cascade["duree_minutes"] is not None
    ]

    statistiques = {
        "nombre_cascades": len(cascades),
        "taille_moyenne": round(sum(tailles) / len(tailles), 2) if tailles else 0,
        "taille_maximale": max(tailles) if tailles else 0,
        "profondeur_moyenne": round(sum(profondeurs_max) / len(profondeurs_max), 2)
        if profondeurs_max
        else 0,
        "profondeur_maximale": max(profondeurs_max) if profondeurs_max else 0,
        "duree_moyenne_minutes": round(sum(durees) / len(durees), 1) if durees else None,
        "cascades_multi_communautes": sum(
            1 for cascade in cascades if cascade["nombre_communautes_atteintes"] > 1
        ),
    }

    return {
        "nombre_cascades": len(cascades),
        "cascades": cascades,
        "arbres": arbres,
        "noeuds_max_par_arbre": NOEUDS_MAX_PAR_ARBRE,
        "statistiques": statistiques,
        "methode": (
            "Reconstruction descriptive des cascades à partir du champ parent_id "
            "(publication → commentaire → réponse → partage/repost/citation). "
            "Aucun modèle de diffusion n'est estimé."
        ),
        "message": "",
    }
