"""Chargement et validation du jeu de données d'interactions.

Format normalisé attendu (CSV ou JSON) :

    platform,source_id,post_id,interaction_id,source_user,target_user,
    interaction_type,text,timestamp,parent_id,url

Le pipeline analyse exactement les mêmes données qu'elles proviennent d'une
collecte publique, d'un export de plateforme, d'un CSV manuel ou d'un JSON.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

COLONNES_REQUISES = [
    "platform",
    "source_id",
    "post_id",
    "interaction_id",
    "source_user",
    "target_user",
    "interaction_type",
    "text",
    "timestamp",
    "parent_id",
    "url",
]

TYPES_INTERACTION = {
    "post",
    "comment",
    "reply",
    "mention",
    "share",
    "repost",
    "quote",
}

# Types produisant un lien orienté entre deux utilisateurs dans le réseau.
TYPES_RELATIONNELS = {"comment", "reply", "mention", "share", "repost", "quote"}


class ErreurDonnees(Exception):
    """Erreur de lecture ou de validation du jeu de données."""


def _lire_fichier(chemin: Path) -> pd.DataFrame:
    suffixe = chemin.suffix.lower()
    try:
        if suffixe == ".csv":
            cadre = pd.read_csv(chemin, dtype=str, keep_default_na=False, na_values=[])
        elif suffixe == ".json":
            contenu = json.loads(chemin.read_text(encoding="utf-8"))
            if isinstance(contenu, dict):
                contenu = contenu.get("interactions", contenu.get("data", []))
            if not isinstance(contenu, list):
                raise ErreurDonnees(
                    f"{chemin.name} : le JSON doit contenir une liste d'interactions "
                    "(ou une clé « interactions »)."
                )
            cadre = pd.DataFrame(contenu, dtype=str)
        else:
            raise ErreurDonnees(
                f"{chemin.name} : extension non prise en charge ({suffixe}). "
                "Formats acceptés : .csv, .json."
            )
    except pd.errors.EmptyDataError as erreur:
        raise ErreurDonnees(f"{chemin.name} : fichier vide (aucune donnée lisible).") from erreur
    except pd.errors.ParserError as erreur:
        raise ErreurDonnees(f"{chemin.name} : CSV invalide — {erreur}") from erreur
    except json.JSONDecodeError as erreur:
        raise ErreurDonnees(f"{chemin.name} : JSON invalide — {erreur}") from erreur
    return cadre


def valider_colonnes(cadre: pd.DataFrame, nom_fichier: str = "jeu de données") -> None:
    """Vérifie la présence des colonnes du format normalisé."""
    manquantes = [colonne for colonne in COLONNES_REQUISES if colonne not in cadre.columns]
    if manquantes:
        raise ErreurDonnees(
            f"{nom_fichier} : colonnes manquantes — {', '.join(manquantes)}. "
            f"Colonnes attendues : {', '.join(COLONNES_REQUISES)}. "
            "Voir data/import_template.csv."
        )


def normaliser(cadre: pd.DataFrame, nom_fichier: str = "jeu de données") -> pd.DataFrame:
    """Valide et normalise un tableau d'interactions."""
    valider_colonnes(cadre, nom_fichier)
    if cadre.empty:
        raise ErreurDonnees(f"{nom_fichier} : aucune interaction (jeu de données vide).")

    cadre = cadre.loc[:, COLONNES_REQUISES].copy()
    for colonne in COLONNES_REQUISES:
        cadre[colonne] = cadre[colonne].fillna("").astype(str).str.strip()

    cadre["platform"] = cadre["platform"].str.lower()
    cadre["interaction_type"] = cadre["interaction_type"].str.lower()

    # Une interaction sans identifiant ni auteur n'est pas exploitable.
    avant = len(cadre)
    cadre = cadre[(cadre["interaction_id"] != "") & (cadre["source_user"] != "")]
    lignes_ignorees = avant - len(cadre)
    if cadre.empty:
        raise ErreurDonnees(
            f"{nom_fichier} : aucune interaction exploitable "
            "(colonnes « interaction_id » et « source_user » vides)."
        )

    doublons = cadre.duplicated(subset=["interaction_id"], keep="first")
    cadre = cadre[~doublons]

    types_inconnus = sorted(set(cadre["interaction_type"]) - TYPES_INTERACTION)
    cadre["type_reconnu"] = cadre["interaction_type"].isin(TYPES_INTERACTION)

    cadre["horodatage"] = pd.to_datetime(
        cadre["timestamp"], errors="coerce", format="mixed", utc=False
    )

    cadre.attrs["lignes_ignorees"] = int(lignes_ignorees)
    cadre.attrs["doublons_supprimes"] = int(doublons.sum())
    cadre.attrs["types_inconnus"] = types_inconnus
    cadre.attrs["horodatages_invalides"] = int(cadre["horodatage"].isna().sum())
    return cadre.reset_index(drop=True)


def charger_jeu_de_donnees(
    chemins_reels: list[Path], chemin_demonstration: Path | None
) -> tuple[pd.DataFrame, dict]:
    """Charge les données réelles si elles existent, sinon le jeu de démonstration.

    Les données réelles et synthétiques ne sont jamais mélangées silencieusement :
    si des fichiers réels sont présents, le jeu de démonstration est ignoré.
    """
    fichiers_reels = [chemin for chemin in chemins_reels if chemin.exists()]
    if fichiers_reels:
        cadres = []
        for chemin in fichiers_reels:
            cadre = _lire_fichier(chemin)
            valider_colonnes(cadre, chemin.name)
            cadres.append(cadre)
        fusion = pd.concat(cadres, ignore_index=True)
        cadre = normaliser(fusion, "données importées")
        meta = {
            "type": "reel",
            "synthetique": False,
            "fichiers": [str(chemin.name) for chemin in fichiers_reels],
            "avertissement": "",
        }
    else:
        if chemin_demonstration is None or not chemin_demonstration.exists():
            raise ErreurDonnees(
                "Aucun jeu de données trouvé. Placez un fichier au format normalisé dans "
                "data/imported/ (voir data/import_template.csv), ou générez le jeu de "
                "démonstration avec : python data/generer_donnees_demo.py"
            )
        cadre = normaliser(_lire_fichier(chemin_demonstration), chemin_demonstration.name)
        meta = {
            "type": "synthetique",
            "synthetique": True,
            "fichiers": [chemin_demonstration.name],
            "avertissement": (
                "Données de démonstration synthétiques — les résultats ne constituent pas "
                "des résultats empiriques."
            ),
        }

    meta.update(
        {
            "interactions": int(len(cadre)),
            "lignes_ignorees": cadre.attrs.get("lignes_ignorees", 0),
            "doublons_supprimes": cadre.attrs.get("doublons_supprimes", 0),
            "types_inconnus": cadre.attrs.get("types_inconnus", []),
            "horodatages_invalides": cadre.attrs.get("horodatages_invalides", 0),
        }
    )
    return cadre, meta
