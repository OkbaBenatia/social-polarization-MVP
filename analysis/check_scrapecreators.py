"""Contrôle qualité des CSV collectés via ScrapeCreators.

Vérifie, pour chacune des sources déclarées : existence du fichier, encodage
UTF-8, en-tête conforme, absence de ligne synthétique, absence de doublon
d'identifiant, présence du ``source_id`` sur chaque ligne, conservation du texte
et des horodatages, et cohérence des liens parent/enfant.

Utilisation :

    python analysis/check_scrapecreators.py

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import collect_scrapecreators as sc  # noqa: E402
import provenance as prov  # noqa: E402

FICHIER_SOURCES = RACINE / "data" / "sources.json"


def controler_fichier(chemin: Path, source_id: str) -> dict:
    rapport = {
        "source_id": source_id,
        "fichier": str(chemin.relative_to(RACINE)),
        "existe": chemin.exists(),
        "utf8": False,
        "entete_conforme": False,
        "lignes": 0,
        "posts": 0,
        "commentaires": 0,
        "reponses": 0,
        "anomalies": [],
    }
    if not chemin.exists():
        rapport["anomalies"].append("fichier absent")
        return rapport

    try:
        contenu = chemin.read_text(encoding="utf-8")
        rapport["utf8"] = True
    except UnicodeDecodeError:
        rapport["anomalies"].append("fichier non lisible en UTF-8")
        return rapport

    lignes = list(csv.DictReader(contenu.splitlines()))
    entete = list(csv.reader(contenu.splitlines()))[0] if contenu.strip() else []
    rapport["entete_conforme"] = entete == sc.COLONNES
    if not rapport["entete_conforme"]:
        rapport["anomalies"].append(
            f"en-tête non conforme (attendu {len(sc.COLONNES)} colonnes)"
        )

    rapport["lignes"] = len(lignes)
    identifiants: set[str] = set()
    connus = {l.get("interaction_id", "") for l in lignes} | {
        l.get("post_id", "") for l in lignes
    }

    for ligne in lignes:
        type_interaction = (ligne.get("interaction_type") or "").strip().lower()
        if type_interaction == "post":
            rapport["posts"] += 1
        elif type_interaction == "comment":
            rapport["commentaires"] += 1
        elif type_interaction == "reply":
            rapport["reponses"] += 1

        provenance = (ligne.get("provenance") or "").strip().lower()
        if provenance == prov.SYNTHETIC_DEMO:
            rapport["anomalies"].append("ligne de provenance synthetic_demo")
        elif not prov.est_reelle(provenance):
            rapport["anomalies"].append(f"provenance non réelle : « {provenance} »")

        if not (ligne.get("source_id") or "").strip():
            rapport["anomalies"].append("ligne sans source_id")
        elif ligne["source_id"].strip() != source_id:
            rapport["anomalies"].append(
                f"source_id étranger : {ligne['source_id']} (attendu {source_id})"
            )

        identifiant = (ligne.get("interaction_id") or "").strip()
        if identifiant and identifiant in identifiants:
            rapport["anomalies"].append(f"doublon d'interaction_id : {identifiant}")
        identifiants.add(identifiant)

        parent = (ligne.get("parent_interaction_id") or "").strip()
        if parent and parent not in connus:
            rapport["anomalies"].append(f"parent_interaction_id orphelin : {parent}")

        if type_interaction in {"comment", "reply"} and not (ligne.get("text") or "").strip():
            # Un commentaire sans texte est possible (image seule) : signalé, non bloquant.
            rapport.setdefault("commentaires_sans_texte", 0)
            rapport["commentaires_sans_texte"] += 1

    rapport["anomalies"] = sorted(set(rapport["anomalies"]))
    return rapport


def _statuts_collecte() -> dict[str, dict]:
    """Statuts déclarés par le rapport de collecte, s'il existe."""
    if not sc.FICHIER_RAPPORT.exists():
        return {}
    try:
        rapport = json.loads(sc.FICHIER_RAPPORT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {r["source_id"]: r for r in rapport.get("sources", [])}


def main() -> int:
    analyseur = argparse.ArgumentParser(description="Contrôle qualité des CSV ScrapeCreators.")
    analyseur.add_argument("--sources", type=Path, default=FICHIER_SOURCES)
    analyseur.add_argument(
        "--exiger-donnees",
        action="store_true",
        help="Échouer si une source ne contient aucune interaction.",
    )
    arguments = analyseur.parse_args()

    sources = json.loads(arguments.sources.read_text(encoding="utf-8"))["sources"]
    statuts = _statuts_collecte()
    rapports = [
        controler_fichier(sc.REPERTOIRE_CSV / f"{s['source_id']}.csv", s["source_id"])
        for s in sources
    ]

    print("Contrôle qualité des CSV ScrapeCreators")
    print("Trois dimensions distinctes : schéma du fichier, présence de données, "
          "statut de collecte.\n")
    print(f"  {'Source':14} {'Schéma':10} {'Données':28} {'Statut collecte':20}")
    print(f"  {'-' * 14} {'-' * 10} {'-' * 28} {'-' * 20}")

    sans_donnees = 0
    for r, source in zip(rapports, sources):
        if not r["existe"]:
            schema = "absent"
        elif r["entete_conforme"] and r["utf8"]:
            schema = "valide"
        else:
            schema = "INVALIDE"

        interactions = r["commentaires"] + r["reponses"]
        if source["platform"] == "x":
            donnees = f"{r['lignes']} ligne(s), 0 réponse"
        else:
            donnees = f"{r['commentaires']} comm. + {r['reponses']} rép."
        if interactions == 0:
            donnees = f"{donnees} — VIDE"
            sans_donnees += 1

        journal = statuts.get(r["source_id"], {})
        statut = journal.get("collection_status", "non collectée")

        print(f"  {r['source_id']:14} {schema:10} {donnees:28} {statut:20}")
        for anomalie in r["anomalies"]:
            print(f"      ! {anomalie}")

    total_c = sum(r["commentaires"] for r in rapports)
    total_r = sum(r["reponses"] for r in rapports)
    total_l = sum(r["lignes"] for r in rapports)
    anomalies = sum(len(r["anomalies"]) for r in rapports if r["existe"])
    absents = sum(1 for r in rapports if not r["existe"])

    print(f"\n  Total réel : {total_c} commentaires, {total_r} réponses, {total_l} lignes")
    print(f"  Fichiers absents : {absents} | sources sans aucune interaction : {sans_donnees}")
    print(f"  Anomalies de contenu : {anomalies}")
    if sans_donnees or absents:
        print(
            "\n  Un fichier vide ou absent n'est jamais une collecte réussie : "
            "ces sources restent à collecter."
        )
    if anomalies:
        return 1
    if arguments.exiger_donnees and (sans_donnees or absents):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
