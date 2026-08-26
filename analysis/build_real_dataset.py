"""Construction du jeu de données empirique ``data/real_interactions.csv``.

Le fichier produit ne contient **que** des interactions réellement collectées :
provenance ``official_api``, ``public_page`` ou ``manual_verified``. Toute ligne
de provenance ``synthetic_demo`` est refusée.

Sources agrégées :

* ``data/manual_verified_interactions.csv`` — saisies manuelles vérifiées ;
* ``data/collected/*.csv`` — sorties éventuelles d'une collecte automatisée
  autorisée (API officielle ou page publique).

Utilisation :

    python analysis/build_real_dataset.py

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import load_data  # noqa: E402
import provenance as prov  # noqa: E402
import quality_checks  # noqa: E402

FICHIER_SOURCES = RACINE / "data" / "sources.json"
FICHIER_MANUEL = RACINE / "data" / "manual_verified_interactions.csv"
REPERTOIRE_COLLECTE = RACINE / "data" / "collected"
REPERTOIRE_SCRAPECREATORS = RACINE / "data" / "scrapecreators"
RAPPORT_SCRAPECREATORS = REPERTOIRE_SCRAPECREATORS / "collection_report.json"
FICHIER_SORTIE = RACINE / "data" / "real_interactions.csv"

#: Correspondance entre le schéma des CSV ScrapeCreators et le format normalisé
#: du pipeline. Les colonnes de métriques (like_count, reaction_count,
#: reply_count) ne sont pas analysées : elles restent dans les CSV d'origine.
CORRESPONDANCE_SCRAPECREATORS = {
    "source_url": "url",
    "parent_interaction_id": "parent_id",
}

COLONNES = load_data.COLONNES_REQUISES + prov.COLONNES_PROVENANCE


def _affichable(chemin: Path) -> str:
    """Chemin relatif à la racine du projet lorsque c'est possible."""
    try:
        return str(chemin.relative_to(RACINE))
    except ValueError:
        return str(chemin)


def _sources_declarees(chemin: Path) -> set[str]:
    if not chemin.exists():
        return set()
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    return {str(s["source_id"]).strip() for s in donnees.get("sources", [])}


def _lire(chemin: Path) -> pd.DataFrame:
    cadre = pd.read_csv(chemin, dtype=str, keep_default_na=False, na_values=[])
    manquantes = [c for c in COLONNES if c not in cadre.columns]
    if manquantes:
        raise SystemExit(
            f"ERREUR : {chemin.name} — colonnes manquantes : {', '.join(manquantes)}.\n"
            f"Colonnes attendues : {', '.join(COLONNES)}"
        )
    return cadre.loc[:, COLONNES]


def _fichiers_sources() -> list[Path]:
    fichiers = [FICHIER_MANUEL] if FICHIER_MANUEL.exists() else []
    if REPERTOIRE_COLLECTE.exists():
        fichiers += sorted(
            c for c in REPERTOIRE_COLLECTE.iterdir()
            if c.suffix.lower() == ".csv" and not c.name.startswith(".")
        )
    return fichiers


def _horodatage_collecte() -> str:
    """Date de la collecte ScrapeCreators, lue dans son rapport."""
    if RAPPORT_SCRAPECREATORS.exists():
        try:
            return str(
                json.loads(RAPPORT_SCRAPECREATORS.read_text(encoding="utf-8")).get(
                    "genere_le", ""
                )
            )
        except json.JSONDecodeError:
            pass
    return ""


def _fichiers_scrapecreators() -> list[Path]:
    if not REPERTOIRE_SCRAPECREATORS.exists():
        return []
    return sorted(
        chemin
        for chemin in REPERTOIRE_SCRAPECREATORS.iterdir()
        if chemin.suffix.lower() == ".csv" and not chemin.name.startswith(".")
    )


def _lire_scrapecreators(chemin: Path, collecte_le: str) -> pd.DataFrame:
    """Convertit un CSV ScrapeCreators vers le format normalisé du pipeline."""
    cadre = pd.read_csv(chemin, dtype=str, keep_default_na=False, na_values=[])
    if cadre.empty:
        return pd.DataFrame(columns=COLONNES)
    cadre = cadre.rename(columns=CORRESPONDANCE_SCRAPECREATORS)
    if "collected_at" not in cadre.columns:
        cadre["collected_at"] = collecte_le
    for colonne in COLONNES:
        if colonne not in cadre.columns:
            cadre[colonne] = ""
    return cadre.loc[:, COLONNES]


def construire(sortie: Path = FICHIER_SORTIE) -> tuple[pd.DataFrame, dict]:
    fichiers = _fichiers_sources()
    if not fichiers and not _fichiers_scrapecreators():
        raise SystemExit(
            f"ERREUR : aucun fichier source. Créez {_affichable(FICHIER_MANUEL)} "
            "(voir data/README_IMPORT_MANUEL.md)."
        )

    cadres = [_lire(chemin) for chemin in fichiers]
    collecte_le = _horodatage_collecte()
    fichiers_sc = _fichiers_scrapecreators()
    for chemin in fichiers_sc:
        cadres.append(_lire_scrapecreators(chemin, collecte_le))
    fichiers = fichiers + fichiers_sc
    cadre = pd.concat(cadres, ignore_index=True) if cadres else pd.DataFrame(columns=COLONNES)

    for colonne in COLONNES:
        cadre[colonne] = cadre[colonne].fillna("").astype(str).str.strip()

    # Seules les provenances réelles sont retenues ; le synthétique est écarté ici,
    # et son éventuelle présence est signalée par le contrôle de qualité ensuite.
    avant = len(cadre)
    provenances = cadre["provenance"].str.lower()
    cadre = cadre[provenances.isin(prov.PROVENANCES_REELLES)].reset_index(drop=True)
    ecartees = avant - len(cadre)

    quality_checks.controler_ou_echouer(cadre, _sources_declarees(FICHIER_SOURCES))

    sortie.parent.mkdir(parents=True, exist_ok=True)
    cadre.to_csv(sortie, index=False, encoding="utf-8")

    types = cadre["interaction_type"].str.lower() if len(cadre) else pd.Series(dtype=str)
    resume = {
        "fichiers_lus": [_affichable(c) for c in fichiers],
        "lignes_ecartees_non_reelles": int(ecartees),
        "sources_reelles": int(cadre["source_id"].nunique()) if len(cadre) else 0,
        "publications": int((types == "post").sum()) if len(cadre) else 0,
        "commentaires": int((types == "comment").sum()) if len(cadre) else 0,
        "reponses": int((types == "reply").sum()) if len(cadre) else 0,
        "interactions": int(len(cadre)),
        "utilisateurs": int(
            pd.concat([cadre["source_user"], cadre["target_user"]]).replace("", pd.NA).nunique()
        )
        if len(cadre)
        else 0,
        "provenances": (
            cadre["provenance"].str.lower().value_counts().to_dict() if len(cadre) else {}
        ),
    }
    return cadre, resume


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Assemble le jeu de données empirique à partir des données réelles."
    )
    analyseur.add_argument("--sortie", type=Path, default=FICHIER_SORTIE)
    arguments = analyseur.parse_args()

    print("Construction du jeu de données empirique")
    cadre, resume = construire(arguments.sortie)

    print(f"  fichiers lus : {', '.join(resume['fichiers_lus'])}")
    if resume["lignes_ecartees_non_reelles"]:
        print(
            f"  lignes écartées (provenance non réelle) : "
            f"{resume['lignes_ecartees_non_reelles']}"
        )
    print()
    print(f"  Nombre de sources réelles          : {resume['sources_reelles']}")
    print(f"  Nombre de commentaires réels       : {resume['commentaires']}")
    print(f"  Nombre de réponses réelles         : {resume['reponses']}")
    print(f"  Nombre total d'interactions réelles: {resume['interactions']}")
    if resume["provenances"]:
        detail = ", ".join(f"{k} : {v}" for k, v in resume["provenances"].items())
        print(f"  Répartition par provenance         : {detail}")
    print(f"\n  Fichier écrit : {arguments.sortie}")

    if resume["interactions"] == 0:
        print(
            "\n  → Le jeu empirique est vide : aucune interaction réelle n'a encore été "
            "collectée.\n"
            "    Saisissez les interactions réellement observées dans "
            "data/manual_verified_interactions.csv\n"
            "    (voir data/README_IMPORT_MANUEL.md), puis relancez ce script.\n"
            "    L'analyse empirique ne peut pas être lancée sur un jeu vide : le pipeline "
            "refusera de produire\n    des résultats sans données."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
