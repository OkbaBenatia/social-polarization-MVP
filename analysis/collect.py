"""Collecte des données réelles des publications étudiées.

Pour chaque source de ``data/sources.json``, trois voies sont tentées **dans
cet ordre** :

A. **API officielle** — Meta Graph API (Facebook et Instagram) et API X.
   Ces API exigent des identifiants ; ils sont lus dans l'environnement et ne
   sont jamais inscrits dans le dépôt. Sans identifiant, la voie est déclarée
   indisponible, jamais contournée.
B. **Page publique** — lecture des métadonnées publiques, conditionnée au
   ``robots.txt`` du domaine sollicité. Un refus est enregistré comme résultat
   de l'étude et n'est jamais contourné.
C. **Import manuel vérifié** — lorsque le contenu est visible publiquement mais
   non récupérable automatiquement, la source est orientée vers
   ``data/manual_verified_interactions.csv``.

Aucune donnée n'est inventée. Une interaction n'est comptée que si elle a été
réellement obtenue.

Utilisation :

    python analysis/collect.py

Variables d'environnement facultatives (voie A) :

    META_GRAPH_TOKEN   jeton d'application Meta approuvé
    X_BEARER_TOKEN     jeton porteur de l'API X

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import provenance as prov  # noqa: E402

FICHIER_SOURCES = RACINE / "data" / "sources.json"
FICHIER_RAPPORT = RACINE / "data" / "collection_report.json"
FICHIER_MANUEL = RACINE / "data" / "manual_verified_interactions.csv"

AGENT_UTILISATEUR = (
    "social-polarization-MVP/0.2 (recherche academique ; collecte de donnees publiques)"
)
DELAI_ENTRE_SOURCES = 2.0
DELAI_EXPIRATION = 20

ROBOTS_AUTORISE = "autorisé"
ROBOTS_INTERDIT = "interdit"
ROBOTS_ILLISIBLE = "illisible"

VARIABLE_JETON_META = "META_GRAPH_TOKEN"
VARIABLE_JETON_X = "X_BEARER_TOKEN"

DONNEES_ATTENDUES = [
    "texte de la publication",
    "date de publication",
    "commentaires",
    "réponses aux commentaires",
    "mentions",
    "citations",
    "partages / reposts",
    "relations entre utilisateurs",
]

INDICES_MUR_CONNEXION = [
    "login", "connexion", "se connecter", "sign up", "inscription",
    "log in to", "connectez-vous",
]

MOTIF_CONTENU = re.compile(r'content=["\'](.*?)["\']', re.IGNORECASE | re.DOTALL)
MOTIF_CLE = re.compile(r'(?:property|name)=["\'](.*?)["\']', re.IGNORECASE)
MOTIF_TITRE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


# --------------------------------------------------------------------------
# Outils réseau
# --------------------------------------------------------------------------


def _horodatage() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _verdict_robots(url: str) -> tuple[str, str]:
    """Confronte une URL au robots.txt de son domaine. Illisible = refus."""
    parse = urllib.parse.urlparse(url)
    racine = f"{parse.scheme}://{parse.netloc}/robots.txt"
    lecteur = urllib.robotparser.RobotFileParser()
    lecteur.set_url(racine)
    try:
        lecteur.read()
    except Exception as erreur:
        return ROBOTS_ILLISIBLE, (
            f"{racine} illisible ({type(erreur).__name__}) — aucune requête émise, par précaution."
        )
    try:
        autorise = lecteur.can_fetch(AGENT_UTILISATEUR, url)
    except Exception:
        return ROBOTS_ILLISIBLE, f"{racine} non interprétable — aucune requête émise."
    if not autorise:
        return ROBOTS_INTERDIT, (
            f"{racine} interdit cet accès aux agents automatisés — refus respecté."
        )
    return ROBOTS_AUTORISE, f"{racine} autorise la lecture de cette URL."


def _requete(url: str, entetes: dict[str, str] | None = None) -> tuple[int | None, str, str]:
    """Requête publique unique. Retourne (statut, corps, message d'erreur)."""
    base = {
        "User-Agent": AGENT_UTILISATEUR,
        "Accept": "application/json,text/html,application/xhtml+xml",
        "Accept-Language": "fr,ar;q=0.8,en;q=0.5",
    }
    base.update(entetes or {})
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=base), timeout=DELAI_EXPIRATION
        ) as reponse:
            return reponse.status, reponse.read(400_000).decode("utf-8", "replace"), ""
    except urllib.error.HTTPError as erreur:
        detail = erreur.read(400).decode("utf-8", "replace").replace("\n", " ")[:200]
        return erreur.code, "", f"HTTP {erreur.code} — {detail}"
    except Exception as erreur:
        return None, "", f"{type(erreur).__name__} : {erreur}"


def _metadonnees(html: str) -> dict[str, str]:
    trouvees: dict[str, str] = {}
    for balise in re.findall(r"<meta[^>]*>", html, flags=re.IGNORECASE):
        cle = MOTIF_CLE.search(balise)
        contenu = MOTIF_CONTENU.search(balise)
        if not cle or not contenu:
            continue
        nom = cle.group(1).strip().lower()
        if nom in {"og:title", "og:description", "og:type", "og:url", "description", "title"}:
            valeur = contenu.group(1).strip()
            if valeur:
                trouvees.setdefault(nom, valeur[:500])
    titre = MOTIF_TITRE.search(html)
    if titre:
        trouvees.setdefault("html:title", titre.group(1).strip()[:300])
    return trouvees


# --------------------------------------------------------------------------
# Voie A — API officielles
# --------------------------------------------------------------------------


def _api_officielle(source: dict[str, Any]) -> dict[str, Any]:
    """Tente l'API officielle de la plateforme. Sans jeton : indisponible."""
    plateforme = str(source.get("platform", "")).lower()
    url = source["url"]
    encodee = urllib.parse.quote(url, safe="")

    tentative: dict[str, Any] = {
        "ordre": "A",
        "voie": "API officielle",
        "methode": prov.OFFICIAL_API,
        "disponible": False,
        "http_status": None,
        "identifiant_requis": True,
        "identifiant_fourni": False,
        "interactions_recuperees": 0,
        "donnees_obtenues": [],
        "detail": "",
    }

    if plateforme in {"facebook", "instagram"}:
        jeton = os.environ.get(VARIABLE_JETON_META, "").strip()
        point = "oembed_post" if plateforme == "facebook" else "instagram_oembed"
        tentative["api"] = f"Meta Graph API — {point}"
        tentative["identifiant_fourni"] = bool(jeton)
        cible = f"https://graph.facebook.com/v18.0/{point}?url={encodee}"
        if jeton:
            cible += f"&access_token={urllib.parse.quote(jeton)}"
    elif plateforme == "x":
        jeton = os.environ.get(VARIABLE_JETON_X, "").strip()
        tentative["api"] = "X API v2 — /2/tweets"
        tentative["identifiant_fourni"] = bool(jeton)
        identifiant = url.rstrip("/").split("/")[-1].split("?")[0]
        cible = (
            f"https://api.twitter.com/2/tweets/{identifiant}"
            "?tweet.fields=text,created_at,public_metrics,conversation_id"
        )
    else:
        tentative["detail"] = "Aucune API officielle connue pour cette plateforme."
        return tentative

    tentative["url_appelee"] = cible.split("&access_token=")[0]

    if not tentative["identifiant_fourni"]:
        variable = VARIABLE_JETON_META if plateforme != "x" else VARIABLE_JETON_X
        tentative["detail"] = (
            f"{tentative['api']} exige un jeton approuvé. La variable d'environnement "
            f"{variable} n'est pas définie : la voie est déclarée indisponible et "
            "n'est pas contournée."
        )
        return tentative

    entetes = {}
    if plateforme == "x":
        entetes["Authorization"] = f"Bearer {jeton}"
    statut, corps, erreur = _requete(cible, entetes)
    tentative["http_status"] = statut
    if erreur or not corps.strip():
        tentative["detail"] = erreur or f"Réponse HTTP {statut} vide."
        return tentative

    try:
        charge = json.loads(corps)
    except json.JSONDecodeError:
        tentative["detail"] = "Réponse non exploitable (JSON invalide)."
        return tentative

    if isinstance(charge, dict) and charge.get("error"):
        tentative["detail"] = f"Erreur d'API : {charge['error'].get('message', 'inconnue')}"
        return tentative

    obtenues = []
    if plateforme == "x":
        bloc = charge.get("data") or {}
        if bloc.get("text"):
            obtenues.append("texte de la publication")
        if bloc.get("created_at"):
            obtenues.append("date de publication")
    else:
        if charge.get("author_name"):
            obtenues.append("auteur de la publication")
        if charge.get("title") or charge.get("html"):
            obtenues.append("texte de la publication")

    tentative["disponible"] = bool(obtenues)
    tentative["donnees_obtenues"] = obtenues
    tentative["detail"] = (
        f"Réponse HTTP {statut} exploitable." if obtenues
        else f"Réponse HTTP {statut} sans donnée de contenu exploitable."
    )
    # Les points d'accès d'intégration n'exposent aucune interaction entre
    # utilisateurs : le compteur reste à zéro tant qu'aucune n'est obtenue.
    return tentative


# --------------------------------------------------------------------------
# Voie B — page publique
# --------------------------------------------------------------------------


def _page_publique(source: dict[str, Any]) -> dict[str, Any]:
    """Lecture de la page publique, strictement conditionnée au robots.txt."""
    url = source["url"]
    verdict, explication = _verdict_robots(url)
    tentative: dict[str, Any] = {
        "ordre": "B",
        "voie": "Page publique",
        "methode": prov.PUBLIC_PAGE,
        "outil": "lecture HTTP directe (équivalent Scrapy/Playwright)",
        "robots_txt": verdict,
        "robots_detail": explication,
        "requete_effectuee": False,
        "http_status": None,
        "disponible": False,
        "mur_authentification_detecte": False,
        "interactions_recuperees": 0,
        "donnees_obtenues": [],
        "metadonnees_publiques": {},
        "detail": "",
    }

    if verdict != ROBOTS_AUTORISE:
        tentative["detail"] = (
            "Aucune requête émise : le protocole d'exclusion du domaine ne l'autorise pas. "
            "Un moteur de collecte (Scrapy, Playwright) serait soumis à la même règle ; "
            "la contourner reviendrait à ignorer une restriction d'accès explicite."
        )
        return tentative

    statut, corps, erreur = _requete(url)
    tentative["requete_effectuee"] = True
    tentative["http_status"] = statut
    if erreur or not corps.strip():
        tentative["detail"] = erreur or f"Réponse HTTP {statut} vide."
        return tentative

    minuscule = corps[:200_000].lower()
    if any(indice in minuscule for indice in INDICES_MUR_CONNEXION):
        tentative["mur_authentification_detecte"] = True
        tentative["detail"] = (
            "Un mur d'authentification a été détecté ; il n'est pas franchi. "
        )

    metadonnees = _metadonnees(corps)
    tentative["metadonnees_publiques"] = metadonnees
    if metadonnees:
        tentative["disponible"] = True
        tentative["donnees_obtenues"] = ["métadonnées publiques de la publication"]
    tentative["detail"] += (
        f"Réponse HTTP {statut} obtenue."
        if metadonnees
        else f"Réponse HTTP {statut} sans métadonnée publique exploitable."
    )
    return tentative


# --------------------------------------------------------------------------
# Voie C — import manuel vérifié
# --------------------------------------------------------------------------


def _import_manuel(source: dict[str, Any], lignes_manuelles: dict[str, dict[str, int]]) -> dict:
    """Comptabilise les interactions déjà saisies manuellement pour la source."""
    compte = lignes_manuelles.get(source["source_id"], {})
    total = compte.get("total", 0)
    tentative = {
        "ordre": "C",
        "voie": "Import manuel vérifié",
        "methode": prov.MANUAL_VERIFIED,
        "fichier": str(FICHIER_MANUEL.relative_to(RACINE)),
        "disponible": total > 0,
        "interactions_recuperees": total,
        "commentaires": compte.get("comment", 0),
        "reponses": compte.get("reply", 0),
        "detail": (
            f"{total} interactions réelles saisies et vérifiées pour cette source."
            if total
            else "Aucune interaction saisie à ce jour pour cette source dans "
            f"{FICHIER_MANUEL.name}."
        ),
    }
    return tentative


# --------------------------------------------------------------------------
# Assemblage par source
# --------------------------------------------------------------------------


def _lire_manuel(chemin: Path) -> dict[str, dict[str, int]]:
    """Compte, par source, les interactions réellement saisies manuellement."""
    if not chemin.exists():
        return {}
    import csv

    comptes: dict[str, dict[str, int]] = {}
    with chemin.open(encoding="utf-8", newline="") as flux:
        for ligne in csv.DictReader(flux):
            source_id = (ligne.get("source_id") or "").strip()
            identifiant = (ligne.get("interaction_id") or "").strip()
            if not source_id or not identifiant:
                continue
            provenance = (ligne.get("provenance") or "").strip().lower()
            if not prov.est_reelle(provenance):
                continue
            type_interaction = (ligne.get("interaction_type") or "").strip().lower()
            bloc = comptes.setdefault(source_id, {"total": 0})
            bloc["total"] += 1
            bloc[type_interaction] = bloc.get(type_interaction, 0) + 1
    return comptes


def tenter_collecte(source: dict[str, Any], lignes_manuelles: dict | None = None) -> dict[str, Any]:
    """Applique les trois voies dans l'ordre et détermine le statut de la source."""
    lignes_manuelles = lignes_manuelles or {}
    tentatives = [
        _api_officielle(source),
        _page_publique(source),
        _import_manuel(source, lignes_manuelles),
    ]

    manuel = tentatives[2]
    commentaires = int(manuel.get("commentaires", 0))
    reponses = int(manuel.get("reponses", 0))
    interactions = sum(int(t.get("interactions_recuperees", 0)) for t in tentatives)

    donnees_obtenues: list[str] = []
    for tentative in tentatives:
        for donnee in tentative.get("donnees_obtenues", []):
            if donnee not in donnees_obtenues:
                donnees_obtenues.append(donnee)

    api_disponible = bool(tentatives[0].get("disponible"))
    publication_recuperee = any(
        "texte de la publication" in t.get("donnees_obtenues", []) for t in tentatives
    )

    if interactions > 0:
        statut = prov.REAL_DATA_COLLECTED
        raison = ""
    elif donnees_obtenues:
        statut = prov.PARTIAL_REAL_DATA
        raison = (
            "Des données publiques de la publication ont été obtenues, mais aucune "
            "interaction entre utilisateurs n'est exposée par la plateforme."
        )
    else:
        statut = prov.MANUAL_IMPORT_REQUIRED
        raison = (
            "Aucune voie automatisée n'est ouverte : "
            + tentatives[0]["detail"]
            + " "
            + tentatives[1]["detail"]
        ).strip()

    # Compatibilité avec le tableau de bord existant (public/data/sources.json).
    manquantes = [d for d in DONNEES_ATTENDUES if d not in donnees_obtenues]

    return {
        "source_id": source["source_id"],
        "platform": str(source.get("platform", "")).lower(),
        "plateforme": str(source.get("platform", "")).lower(),
        "url": source["url"],
        "tentative_le": _horodatage(),
        "methodes_tentees": tentatives,
        "api_disponible": api_disponible,
        "publication_recuperee": publication_recuperee,
        "commentaires_reels": commentaires,
        "reponses_reelles": reponses,
        "interactions_reelles": interactions,
        "statut": statut,
        "statut_libelle": prov.LIBELLES_STATUT[statut],
        "raison_echec": raison,
        # --- clés conservées pour le tableau de bord ---
        "methode": "trois voies ordonnées : API officielle, page publique, import manuel",
        "robots_txt": tentatives[1]["robots_detail"],
        "http_status": tentatives[0].get("http_status") or tentatives[1].get("http_status"),
        "metadonnees_publiques": tentatives[1].get("metadonnees_publiques", {}),
        "interactions_recuperees": interactions,
        "mur_authentification_detecte": bool(tentatives[1].get("mur_authentification_detecte")),
        "accessible": bool(donnees_obtenues),
        "voies_evaluees": [
            {
                "voie": f"{t['ordre']}. {t['voie']}",
                "url": t.get("url_appelee", t.get("fichier", source["url"])),
                "robots_txt": t.get("robots_txt", "sans objet"),
                "robots_detail": t.get("robots_detail", ""),
                "requete_effectuee": bool(t.get("requete_effectuee", False)),
                "http_status": t.get("http_status"),
                "contenu_obtenu": bool(t.get("disponible")),
                "remarque": t.get("api", t.get("outil", "")),
                "resultat": t["detail"],
            }
            for t in tentatives
        ],
        "donnees_recuperees": donnees_obtenues,
        "donnees_manquantes": manquantes,
        "import_manuel_requis": interactions == 0,
        "limites": [f"{t['ordre']}. {t['voie']} — {t['detail']}" for t in tentatives],
    }


def collecter(
    fichier_sources: Path = FICHIER_SOURCES,
    fichier_rapport: Path = FICHIER_RAPPORT,
    fichier_manuel: Path = FICHIER_MANUEL,
) -> dict:
    sources = json.loads(fichier_sources.read_text(encoding="utf-8"))["sources"]
    lignes_manuelles = _lire_manuel(fichier_manuel)

    resultats = []
    for index, source in enumerate(sources):
        if index:
            time.sleep(DELAI_ENTRE_SOURCES)
        print(f"  → {source['source_id']} ({source['platform']})")
        resultats.append(tenter_collecte(source, lignes_manuelles))

    rapport = {
        "genere_le": _horodatage(),
        "agent_utilisateur": AGENT_UTILISATEUR,
        "ordre_de_collecte": [
            "A. API officielle de la plateforme (identifiants requis, jamais contournés).",
            "B. Page publique, strictement conditionnée au robots.txt du domaine.",
            "C. Import manuel vérifié depuis les publications réellement consultées.",
        ],
        "regles": [
            "Aucune authentification, aucun cookie personnel, aucune session privée.",
            "Aucun contournement de CAPTCHA, de protection anti-bot ou de limitation d'API.",
            "Respect du fichier robots.txt de chaque domaine sollicité.",
            "Aucune donnée n'est inventée : une interaction n'est comptée que si elle a "
            "été réellement obtenue.",
            "Aucune donnée privée n'est recherchée ni conservée.",
        ],
        "donnees_attendues": DONNEES_ATTENDUES,
        "statuts_possibles": list(prov.STATUTS_COLLECTE),
        "synthese": {
            "sources": len(resultats),
            "sources_reelles": sum(1 for r in resultats if r["interactions_reelles"] > 0),
            "commentaires_reels": sum(r["commentaires_reels"] for r in resultats),
            "reponses_reelles": sum(r["reponses_reelles"] for r in resultats),
            "interactions_reelles": sum(r["interactions_reelles"] for r in resultats),
            "sources_import_manuel": sum(
                1 for r in resultats if r["statut"] == prov.MANUAL_IMPORT_REQUIRED
            ),
        },
        "resultats": resultats,
    }
    fichier_rapport.parent.mkdir(parents=True, exist_ok=True)
    fichier_rapport.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return rapport


def main() -> int:
    analyseur = argparse.ArgumentParser(description="Collecte des données réelles des sources.")
    analyseur.add_argument("--sources", type=Path, default=FICHIER_SOURCES)
    analyseur.add_argument("--rapport", type=Path, default=FICHIER_RAPPORT)
    analyseur.add_argument("--manuel", type=Path, default=FICHIER_MANUEL)
    arguments = analyseur.parse_args()

    print("Collecte des données réelles — trois voies ordonnées")
    rapport = collecter(arguments.sources, arguments.rapport, arguments.manuel)
    s = rapport["synthese"]

    print(f"\nRapport écrit : {arguments.rapport}")
    print(f"  Sources déclarées                 : {s['sources']}")
    print(f"  Sources avec données réelles      : {s['sources_reelles']}")
    print(f"  Commentaires réels                : {s['commentaires_reels']}")
    print(f"  Réponses réelles                  : {s['reponses_reelles']}")
    print(f"  Interactions réelles              : {s['interactions_reelles']}")
    print(f"  Sources en import manuel requis   : {s['sources_import_manuel']}")

    print("\n  Statut par source :")
    for resultat in rapport["resultats"]:
        print(f"    {resultat['source_id']:15} {resultat['statut']:24} "
              f"{resultat['interactions_reelles']:>4} interactions")

    if s["interactions_reelles"] == 0:
        print(
            f"\n  → Aucune interaction réelle n'a pu être collectée automatiquement.\n"
            f"    Saisissez les interactions réellement observées dans "
            f"{arguments.manuel.relative_to(RACINE)},\n"
            "    puis relancez : python analysis/build_real_dataset.py"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
