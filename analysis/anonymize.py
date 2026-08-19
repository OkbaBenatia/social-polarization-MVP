"""Pseudonymisation des identifiants d'utilisateurs.

Aucun identifiant brut, nom, adresse ou coordonnée ne doit apparaître dans
``public/``. Chaque utilisateur reçoit :

* un pseudonyme technique stable (``HMAC-SHA256`` tronqué) ;
* une étiquette d'affichage neutre : « Utilisateur 001 », « Utilisateur 002 »…

La table de correspondance n'est écrite que localement, dans ``data/private/``
(répertoire exclu du dépôt), et n'est jamais publiée.

Aucun attribut sensible (religion, origine, ethnie, orientation politique,
opinion) n'est inféré : seuls des identifiants sont transformés.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

import pandas as pd

VARIABLE_SEL = "ANONYMIZATION_SALT"
NOM_FICHIER_SEL = "sel_anonymisation.txt"
NOM_FICHIER_TABLE = "table_anonymisation.json"

COLONNES_UTILISATEUR = ("source_user", "target_user")


def obtenir_sel(repertoire_prive: Path) -> str:
    """Retourne le sel de pseudonymisation, en le créant si nécessaire.

    Priorité à la variable d'environnement ``ANONYMIZATION_SALT`` afin de
    permettre des exécutions reproductibles et un déploiement contrôlé.
    """
    sel_environnement = os.environ.get(VARIABLE_SEL, "").strip()
    if sel_environnement:
        return sel_environnement

    repertoire_prive.mkdir(parents=True, exist_ok=True)
    fichier_sel = repertoire_prive / NOM_FICHIER_SEL
    if fichier_sel.exists():
        sel = fichier_sel.read_text(encoding="utf-8").strip()
        if sel:
            return sel
    sel = secrets.token_hex(16)
    fichier_sel.write_text(sel + "\n", encoding="utf-8")
    return sel


def pseudonymiser_identifiant(identifiant: str, sel: str) -> str:
    """Pseudonyme technique irréversible sans le sel."""
    empreinte = hmac.new(sel.encode("utf-8"), identifiant.encode("utf-8"), hashlib.sha256)
    return "usr_" + empreinte.hexdigest()[:12]


def anonymiser(
    cadre: pd.DataFrame, repertoire_prive: Path, ecrire_table: bool = True
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Remplace les identifiants d'utilisateurs par des pseudonymes stables.

    Retourne le tableau anonymisé et le dictionnaire
    ``pseudonyme -> étiquette d'affichage``.
    """
    sel = obtenir_sel(repertoire_prive)
    cadre = cadre.copy()

    identifiants_bruts = sorted(
        {
            valeur
            for colonne in COLONNES_UTILISATEUR
            for valeur in cadre[colonne].tolist()
            if valeur
        }
    )
    correspondance = {brut: pseudonymiser_identifiant(brut, sel) for brut in identifiants_bruts}

    for colonne in COLONNES_UTILISATEUR:
        cadre[colonne] = cadre[colonne].map(lambda valeur: correspondance.get(valeur, ""))

    # Étiquettes d'affichage neutres, attribuées de façon déterministe.
    pseudonymes_ordonnes = sorted(set(correspondance.values()))
    etiquettes = {
        pseudonyme: f"Utilisateur {index:03d}"
        for index, pseudonyme in enumerate(pseudonymes_ordonnes, start=1)
    }

    if ecrire_table:
        repertoire_prive.mkdir(parents=True, exist_ok=True)
        (repertoire_prive / NOM_FICHIER_TABLE).write_text(
            json.dumps(
                {
                    "avertissement": (
                        "Table de correspondance locale — ne jamais publier, ne jamais "
                        "versionner, ne jamais exposer dans public/."
                    ),
                    "correspondance": {
                        brut: {"pseudonyme": pseudo, "etiquette": etiquettes[pseudo]}
                        for brut, pseudo in correspondance.items()
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    return cadre, etiquettes
