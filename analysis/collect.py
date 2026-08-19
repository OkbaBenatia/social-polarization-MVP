"""Tentative de collecte publique des sources de l'étude.

Ce module tente de récupérer **uniquement** les métadonnées publiquement
accessibles des URLs listées dans ``data/sources.json`` (balises Open Graph
présentes dans le HTML servi sans authentification).

Règles strictement appliquées :

* aucune authentification, aucun cookie personnel, aucune session privée ;
* aucun contournement de CAPTCHA, de protection anti-bot ou de limitation d'API ;
* respect du fichier ``robots.txt`` de chaque plateforme ;
* une seule requête par URL, avec délai entre les requêtes (pas de scraping
  agressif) ;
* aucune donnée privée n'est recherchée ni conservée.

Lorsque la plateforme ne renvoie pas de contenu public exploitable, la source
est marquée comme nécessitant un import manuel. Le rapport produit
(``data/collection_report.json``) documente précisément ce qui a pu — ou non —
être récupéré ; il est ensuite lu par le pipeline d'analyse.

Utilisation :

    python analysis/collect.py

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

RACINE = Path(__file__).resolve().parent.parent
FICHIER_SOURCES = RACINE / "data" / "sources.json"
FICHIER_RAPPORT = RACINE / "data" / "collection_report.json"

AGENT_UTILISATEUR = (
    "social-polarization-MVP/0.1 (recherche academique ; collecte de metadonnees publiques)"
)
DELAI_ENTRE_REQUETES = 2.0
DELAI_EXPIRATION = 20

# Indices d'un mur d'authentification ou d'une protection anti-bot. Leur
# présence n'est jamais contournée : elle est uniquement documentée.
INDICES_MUR_CONNEXION = [
    "login",
    "connexion",
    "se connecter",
    "sign up",
    "inscription",
    "log in to",
    "connectez-vous",
]

MOTIF_CONTENU = re.compile(r'content=["\'](.*?)["\']', re.IGNORECASE | re.DOTALL)
MOTIF_CLE = re.compile(r'(?:property|name)=["\'](.*?)["\']', re.IGNORECASE)
MOTIF_TITRE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _robots_autorise(url: str) -> tuple[bool, str]:
    """Vérifie ``robots.txt``. En cas d'échec de lecture, on reste prudent."""
    parse = urlparse(url)
    racine_robots = f"{parse.scheme}://{parse.netloc}/robots.txt"
    lecteur = urllib.robotparser.RobotFileParser()
    lecteur.set_url(racine_robots)
    try:
        lecteur.read()
    except Exception as erreur:  # réseau indisponible, blocage réseau, 403, etc.
        return False, (
            f"robots.txt illisible ({type(erreur).__name__} : {erreur}) — collecte non tentée. "
            "Cause possible : accès sortant vers cette plateforme refusé par l'environnement "
            "d'exécution, ou plateforme refusant les agents automatisés."
        )
    try:
        autorise = lecteur.can_fetch(AGENT_UTILISATEUR, url)
    except Exception:
        return False, "robots.txt non interprétable — collecte non tentée"
    if not autorise:
        return False, "robots.txt interdit l'accès à cette URL pour un agent automatisé"
    return True, "robots.txt autorise la lecture de cette URL"


def _extraire_metadonnees(html: str) -> dict[str, str]:
    metadonnees: dict[str, str] = {}
    for balise in re.findall(r"<meta[^>]*>", html, flags=re.IGNORECASE):
        cle = MOTIF_CLE.search(balise)
        contenu = MOTIF_CONTENU.search(balise)
        if not cle or not contenu:
            continue
        nom = cle.group(1).strip().lower()
        if nom in {"og:title", "og:description", "og:type", "og:url", "description", "title"}:
            valeur = contenu.group(1).strip()
            if valeur:
                metadonnees.setdefault(nom, valeur[:500])
    titre = MOTIF_TITRE.search(html)
    if titre:
        metadonnees.setdefault("html:title", titre.group(1).strip()[:300])
    return metadonnees


def tenter_collecte(source: dict[str, Any]) -> dict[str, Any]:
    """Tente une lecture publique unique de l'URL d'une source."""
    url = source["url"]
    resultat: dict[str, Any] = {
        "source_id": source["source_id"],
        "platform": source["platform"],
        "url": url,
        "tentative_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "methode": "requête HTTP publique unique, sans authentification",
        "robots_txt": "",
        "http_status": None,
        "metadonnees_publiques": {},
        "interactions_recuperees": 0,
        "mur_authentification_detecte": False,
        "accessible": False,
        "limites": [],
    }

    autorise, message_robots = _robots_autorise(url)
    resultat["robots_txt"] = message_robots
    if not autorise:
        resultat["limites"].append(message_robots)
        resultat["limites"].append(
            "Aucune requête de contenu n'a été effectuée : le protocole d'exclusion est respecté."
        )
        return resultat

    requete = urllib.request.Request(
        url,
        headers={
            "User-Agent": AGENT_UTILISATEUR,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "fr,ar;q=0.8,en;q=0.5",
        },
    )
    try:
        with urllib.request.urlopen(requete, timeout=DELAI_EXPIRATION) as reponse:
            resultat["http_status"] = reponse.status
            brut = reponse.read(400_000)
        html = brut.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as erreur:
        resultat["http_status"] = erreur.code
        resultat["limites"].append(
            f"La plateforme a répondu HTTP {erreur.code} à une requête publique non authentifiée."
        )
        return resultat
    except Exception as erreur:
        resultat["limites"].append(
            f"Requête impossible depuis cet environnement ({type(erreur).__name__} : {erreur})."
        )
        return resultat

    metadonnees = _extraire_metadonnees(html)
    resultat["metadonnees_publiques"] = metadonnees
    minuscule = html[:200_000].lower()
    if any(indice in minuscule for indice in INDICES_MUR_CONNEXION):
        resultat["mur_authentification_detecte"] = True
        resultat["limites"].append(
            "Un mur d'authentification ou une invitation à se connecter a été détecté ; "
            "il n'est pas contourné."
        )
    if metadonnees:
        resultat["accessible"] = True
    else:
        resultat["limites"].append(
            "Aucune métadonnée publique exploitable n'a été trouvée dans la réponse."
        )
    resultat["limites"].append(
        "Les commentaires, réponses, mentions et partages ne sont pas exposés publiquement "
        "sur cette plateforme sans API autorisée : ils doivent être importés manuellement."
    )
    return resultat


def collecter(fichier_sources: Path = FICHIER_SOURCES, fichier_rapport: Path = FICHIER_RAPPORT) -> dict:
    donnees = json.loads(fichier_sources.read_text(encoding="utf-8"))
    sources = donnees["sources"]
    resultats = []
    for index, source in enumerate(sources):
        if index:
            time.sleep(DELAI_ENTRE_REQUETES)
        print(f"  → tentative : {source['source_id']} ({source['platform']})")
        resultats.append(tenter_collecte(source))

    rapport = {
        "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agent_utilisateur": AGENT_UTILISATEUR,
        "environnement": (
            "Le rapport reflète ce qui a été réellement obtenu depuis l'environnement "
            "d'exécution utilisé. Un accès sortant refusé (politique réseau, pare-feu, "
            "mandataire) est documenté comme une limite technique et n'est jamais contourné."
        ),
        "regles": [
            "Aucune authentification, aucun cookie personnel, aucune session privée.",
            "Aucun contournement de CAPTCHA, de protection anti-bot ou de limitation d'API.",
            "Respect du fichier robots.txt de chaque plateforme.",
            "Une seule requête par URL, avec délai entre les requêtes.",
            "Aucune donnée privée n'est recherchée ni conservée.",
        ],
        "resultats": resultats,
    }
    fichier_rapport.parent.mkdir(parents=True, exist_ok=True)
    fichier_rapport.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return rapport


def main() -> None:
    analyseur = argparse.ArgumentParser(
        description="Tentative de collecte publique des sources de l'étude."
    )
    analyseur.add_argument(
        "--sources", type=Path, default=FICHIER_SOURCES, help="Fichier des sources (JSON)."
    )
    analyseur.add_argument(
        "--rapport", type=Path, default=FICHIER_RAPPORT, help="Fichier de rapport à écrire."
    )
    arguments = analyseur.parse_args()

    print("Collecte publique des sources (métadonnées uniquement)")
    rapport = collecter(arguments.sources, arguments.rapport)
    accessibles = sum(1 for r in rapport["resultats"] if r["accessible"])
    interactions = sum(r["interactions_recuperees"] for r in rapport["resultats"])
    print(f"\nRapport écrit : {arguments.rapport}")
    print(f"  sources avec métadonnées publiques : {accessibles}/{len(rapport['resultats'])}")
    print(f"  interactions réellement récupérées : {interactions}")
    if interactions == 0:
        print(
            "  → Aucune interaction n'a pu être récupérée automatiquement.\n"
            "    Utilisez data/import_template.csv pour l'import manuel "
            "(voir docs/COLLECTE_DES_DONNEES.md)."
        )


if __name__ == "__main__":
    main()
