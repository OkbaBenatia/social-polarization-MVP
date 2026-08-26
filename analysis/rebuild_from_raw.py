"""Reconstruction des CSV ScrapeCreators depuis le cache local.

Ce script **n'émet aucun appel réseau** : il relit uniquement les réponses
brutes déjà enregistrées dans ``data/raw/scrapecreators/`` et en reconstitue les
CSV de ``data/scrapecreators/``. Il permet de récupérer les données d'une
collecte interrompue sans consommer un seul crédit supplémentaire.

Règles appliquées :

* seules les données réellement présentes dans le cache sont écrites ;
* seuls les doublons exacts d'identifiant d'interaction sont supprimés ;
* texte, horodatages et relations parent/enfant sont conservés tels quels ;
* la pseudonymisation réutilise la table existante : un compte conserve le même
  pseudonyme d'une exécution à l'autre ;
* le statut d'une source est déduit du cache — ``partial`` dès qu'une page
  restait à récupérer, jamais ``failed`` si des données existent.

Utilisation :

    .venv/bin/python analysis/rebuild_from_raw.py

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import collect_scrapecreators as sc  # noqa: E402

FICHIER_SOURCES = RACINE / "data" / "sources.json"

MOTIF_COMMENTS = re.compile(r"^(?P<source>.+)_comments_page_(?P<page>\d+)\.json$")
MOTIF_REPLIES = re.compile(r"^(?P<source>.+)_reply_(?P<cle>.+)_page_(?P<page>\d+)\.json$")
MOTIF_POST = re.compile(r"^(?P<source>.+)_(?:post|tweet)\.json$")


def _charger(chemin: Path) -> dict:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _fichiers_par_source(repertoire: Path) -> dict[str, dict[str, list[Path]]]:
    """Range les fichiers du cache par source et par type."""
    index: dict[str, dict[str, list[Path]]] = {}
    for chemin in sorted(repertoire.glob("*.json")):
        for motif, categorie in (
            (MOTIF_COMMENTS, "comments"),
            (MOTIF_REPLIES, "replies"),
            (MOTIF_POST, "post"),
        ):
            trouve = motif.match(chemin.name)
            if trouve:
                bloc = index.setdefault(trouve.group("source"), {})
                bloc.setdefault(categorie, []).append(chemin)
                break
    return index


def reconstruire_facebook(source: dict, fichiers: dict, pseudo: sc.Pseudonymiseur) -> tuple[list[dict], dict]:
    identifiant = source["source_id"]
    url = source["url"]
    lignes: list[dict] = []
    journal = {
        "source_id": identifiant, "platform": "facebook", "source_url": url,
        "post_retrieved": False, "comments_count": 0, "replies_count": 0,
        "pages_fetched": 0, "comments_truncated": False,
        "replies_attendues": 0, "replies_manquantes": 0, "replies_parent_inconnu": 0,
    }

    # --- publication ---
    post_id = f"{identifiant}_post"
    auteur_pseudo = ""
    for chemin in fichiers.get("post", []):
        charge = _charger(chemin)
        journal["pages_fetched"] += 1
        bloc = charge.get("post") if isinstance(charge.get("post"), dict) else charge
        post_id = str(sc._premier(bloc, "post_id", "id", "postId") or post_id)
        auteur = bloc.get("author") if isinstance(bloc.get("author"), dict) else {}
        auteur_pseudo = pseudo.pseudonyme(auteur.get("id"), auteur.get("name"))
        journal["post_retrieved"] = True
        lignes.append(
            sc._ligne(
                platform="facebook", source_id=identifiant, source_url=url, post_id=post_id,
                interaction_id=post_id, source_user=auteur_pseudo, interaction_type="post",
                # Le détail de post Facebook expose « description » et « creation_time ».
                text=sc._premier(bloc, "description", "message", "text", "caption"),
                timestamp=sc._premier(bloc, "creation_time", "created_at", "time"),
                like_count=sc._premier(bloc, "like_count"),
                reaction_count=sc._premier(bloc, "reaction_count", "reactions_count"),
                reply_count=sc._premier(bloc, "comment_count", "comments_count"),
            )
        )

    # --- commentaires ---
    parents: dict[str, str] = {}
    for chemin in sorted(fichiers.get("comments", [])):
        charge = _charger(chemin)
        journal["pages_fetched"] += 1
        for commentaire in charge.get("comments") or []:
            auteur = commentaire.get("author") if isinstance(commentaire.get("author"), dict) else {}
            pseudo_c = pseudo.pseudonyme(auteur.get("id"), auteur.get("name"))
            parents[str(commentaire.get("id"))] = pseudo_c
            lignes.append(
                sc._ligne(
                    platform="facebook", source_id=identifiant, source_url=url, post_id=post_id,
                    interaction_id=commentaire.get("id"), parent_interaction_id=post_id,
                    source_user=pseudo_c, target_user=auteur_pseudo, interaction_type="comment",
                    text=commentaire.get("text"), timestamp=commentaire.get("created_at"),
                    reaction_count=commentaire.get("reaction_count"),
                    reply_count=commentaire.get("reply_count"),
                )
            )
            journal["comments_count"] += 1
            journal["replies_attendues"] += int(commentaire.get("reply_count") or 0)
        # Une page annonçant une suite non présente dans le cache = collecte partielle.
        if charge.get("has_next_page") and chemin == sorted(fichiers.get("comments", []))[-1]:
            journal["comments_truncated"] = True

    # --- réponses ---
    for chemin in sorted(fichiers.get("replies", [])):
        charge = _charger(chemin)
        journal["pages_fetched"] += 1
        for reponse in charge.get("replies") or charge.get("comments") or []:
            auteur = reponse.get("author") if isinstance(reponse.get("author"), dict) else {}
            parent = str(sc._premier(reponse, "parent_comment_id", "parent_id") or "")
            if parent in parents:
                cible = parents[parent]
            else:
                # Le cache ne porte pas le rattachement explicite. L'appartenance au
                # fil de la publication est certaine ; le commentaire parent précis
                # ne l'est pas. On rattache donc à la publication et on laisse la
                # cible vide plutôt que d'affirmer une relation non vérifiée.
                parent = post_id
                cible = ""
                journal["replies_parent_inconnu"] = journal.get("replies_parent_inconnu", 0) + 1
            lignes.append(
                sc._ligne(
                    platform="facebook", source_id=identifiant, source_url=url, post_id=post_id,
                    interaction_id=reponse.get("id"), parent_interaction_id=parent,
                    source_user=pseudo.pseudonyme(auteur.get("id"), auteur.get("name")),
                    target_user=cible, interaction_type="reply",
                    text=reponse.get("text"), timestamp=reponse.get("created_at"),
                    reaction_count=reponse.get("reaction_count"),
                    reply_count=reponse.get("reply_count"),
                )
            )
            journal["replies_count"] += 1

    journal["replies_manquantes"] = max(
        0, journal["replies_attendues"] - journal["replies_count"]
    )
    return lignes, journal


def _statut_depuis_cache(journal: dict) -> str:
    """Statut déduit du cache. Jamais « failed » si des données existent."""
    lignes_utiles = journal["comments_count"] + journal["replies_count"]
    if lignes_utiles == 0:
        return "no_comments_returned" if journal["post_retrieved"] else "failed"
    if journal.get("comments_truncated") or journal.get("replies_manquantes"):
        return "partial"
    return "complete"


def reconstruire(repertoire_brut: Path, sources: list[dict]) -> dict:
    index = _fichiers_par_source(repertoire_brut)
    pseudo = sc.Pseudonymiseur(sc.FICHIER_PSEUDONYMES)
    rapports: list[dict] = []
    fichiers_analyses = sum(len(v) for bloc in index.values() for v in bloc.values())

    for source in sources:
        identifiant = source["source_id"]
        fichiers = index.get(identifiant)
        if not fichiers:
            print(f"  {identifiant:15} : aucun fichier en cache — ignoré")
            continue

        plateforme = str(source.get("platform", "")).lower()
        if plateforme != "facebook":
            print(f"  {identifiant:15} : plateforme {plateforme} non reconstruite ici")
            continue

        lignes, journal = reconstruire_facebook(source, fichiers, pseudo)
        lignes, doublons = sc._dedupliquer(lignes)
        journal["duplicates_removed"] = doublons
        journal["total_rows"] = len(lignes)
        journal["credits_used"] = 0
        journal["collection_status"] = _statut_depuis_cache(journal)
        journal["source_of_truth"] = "cache local data/raw/scrapecreators (aucun appel API)"
        journal["error_if_any"] = ""
        if journal["comments_truncated"]:
            journal["error_if_any"] = (
                "Pagination des commentaires interrompue : la dernière page en cache "
                "annonçait une page suivante."
            )
        if journal.get("replies_parent_inconnu"):
            journal["error_if_any"] = (
                journal["error_if_any"] + " " if journal["error_if_any"] else ""
            ) + (
                f"{journal['replies_parent_inconnu']} réponses rattachées à la publication : "
                "le commentaire parent exact n'est pas récupérable depuis le cache."
            )
        if journal["replies_manquantes"]:
            journal["error_if_any"] = (
                journal["error_if_any"] + " " if journal["error_if_any"] else ""
            ) + (
                f"{journal['replies_manquantes']} réponses annoncées par les commentaires "
                "ne figurent pas dans le cache."
            )

        sc._ecrire_csv(sc.REPERTOIRE_CSV / f"{identifiant}.csv", lignes)
        rapports.append(journal)
        print(
            f"  {identifiant:15} : {journal['comments_count']} commentaires + "
            f"{journal['replies_count']} réponses → {journal['total_rows']} lignes "
            f"({journal['collection_status']})"
        )

    pseudo.enregistrer()

    rapport = {
        "genere_le": sc._horodatage(),
        "api": "ScrapeCreators",
        "mode": "reconstruction depuis le cache local — aucun appel API, 0 crédit",
        "fichiers_raw_analyses": fichiers_analyses,
        "endpoints_utilises": {
            "facebook": [
                "/v1/facebook/post",
                "/v1/facebook/post/comments",
                "/v1/facebook/post/comment/replies",
            ]
        },
        "regles": [
            "Aucun appel réseau : seules les réponses déjà en cache sont relues.",
            "Aucune donnée fabriquée : seules les interactions présentes sont écrites.",
            "Seuls les doublons exacts d'identifiant d'interaction sont supprimés.",
            "Texte, horodatages et relations parent/enfant conservés tels quels.",
        ],
        "synthese": {
            "sources": len(rapports),
            "comments_total": sum(r["comments_count"] for r in rapports),
            "replies_total": sum(r["replies_count"] for r in rapports),
            "rows_total": sum(r["total_rows"] for r in rapports),
            "pages_total": sum(r["pages_fetched"] for r in rapports),
            "credits_total": 0,
            "utilisateurs_pseudonymises": len(pseudo),
        },
        "sources": rapports,
    }
    return rapport


def _fusionner_rapport(nouveau: dict) -> dict:
    """Conserve les sources déjà décrites qui ne sont pas reconstruites ici."""
    if not sc.FICHIER_RAPPORT.exists():
        return nouveau
    try:
        ancien = json.loads(sc.FICHIER_RAPPORT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return nouveau
    reconstruites = {r["source_id"] for r in nouveau["sources"]}
    conservees = [r for r in ancien.get("sources", []) if r["source_id"] not in reconstruites]
    nouveau["sources"] = nouveau["sources"] + conservees
    return nouveau


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Reconstruit les CSV ScrapeCreators depuis le cache local (aucun appel API)."
    )
    analyseur.add_argument("--sources", type=Path, default=FICHIER_SOURCES)
    analyseur.add_argument("--brut", type=Path, default=sc.REPERTOIRE_BRUT)
    arguments = analyseur.parse_args()

    if not arguments.brut.exists():
        print(f"ERREUR : cache introuvable — {arguments.brut}", file=sys.stderr)
        return 1

    sources = json.loads(arguments.sources.read_text(encoding="utf-8"))["sources"]
    fichiers = sorted(arguments.brut.glob("*.json"))
    print(f"Reconstruction depuis le cache local — {len(fichiers)} fichiers, aucun appel API\n")

    rapport = _fusionner_rapport(reconstruire(arguments.brut, sources))
    sc.FICHIER_RAPPORT.parent.mkdir(parents=True, exist_ok=True)
    sc.FICHIER_RAPPORT.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    s = rapport["synthese"]
    print(f"\n  Commentaires réels : {s['comments_total']}")
    print(f"  Réponses réelles   : {s['replies_total']}")
    print(f"  Lignes totales     : {s['rows_total']}")
    print(f"  Crédits consommés  : {s['credits_total']}")
    print(f"  Rapport : {sc.FICHIER_RAPPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
