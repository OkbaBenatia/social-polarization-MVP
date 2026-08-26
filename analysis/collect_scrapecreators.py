"""Collecte des commentaires publics via l'API ScrapeCreators.

Endpoints utilisés (vérifiés sur la spec OpenAPI publique de ScrapeCreators,
https://docs.scrapecreators.com/openapi.json) :

* ``/v1/facebook/post``                    — détail de la publication
* ``/v1/facebook/post/comments``           — commentaires (pagination ``cursor``)
* ``/v1/facebook/post/comment/replies``    — réponses (``feedback_id`` + ``expansion_token``)
* ``/v1/instagram/post``                   — détail du post/reel
* ``/v2/instagram/post/comments``          — commentaires (pagination ``cursor``)
* ``/v1/instagram/post/comment/replies``   — réponses (``comment_id``)
* ``/v1/twitter/tweet``                    — détail du tweet

Aucun endpoint ScrapeCreators ne permet actuellement de récupérer les réponses
d'une publication X : la spec ne propose que ``profile``, ``tweet``,
``tweet/transcript``, ``user-tweets``, ``community`` et ``community/tweets``.
Pour cette plateforme, seul le post réel est enregistré et le rapport porte
``replies_supported = false``. Rien n'est fabriqué pour compenser.

La clé d'API est lue dans ``SCRAPECREATORS_API_KEY`` et n'est jamais écrite dans
le code, les CSV, les JSON, les journaux ni la documentation.

Utilisation :

    export SCRAPECREATORS_API_KEY="..."
    python analysis/collect_scrapecreators.py

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import provenance as prov  # noqa: E402

BASE_URL = "https://api.scrapecreators.com"
VARIABLE_CLE = "SCRAPECREATORS_API_KEY"

FICHIER_SOURCES = RACINE / "data" / "sources.json"
REPERTOIRE_CSV = RACINE / "data" / "scrapecreators"
REPERTOIRE_BRUT = RACINE / "data" / "raw" / "scrapecreators"
REPERTOIRE_PRIVE = RACINE / "data" / "private"
FICHIER_RAPPORT = REPERTOIRE_CSV / "collection_report.json"
FICHIER_PSEUDONYMES = REPERTOIRE_PRIVE / "scrapecreators_users.json"
#: Nom du fichier de curseurs de reprise, écrit après chaque page : une collecte
#: interrompue reprend là où elle s'est arrêtée au lieu de repartir de la page 1.
NOM_CHECKPOINT = "_checkpoints.json"

PROVENANCE = prov.SCRAPECREATORS_PUBLIC
METHODE = "scrapecreators_api"

COLONNES = [
    "platform", "source_id", "source_url", "post_id", "interaction_id",
    "parent_interaction_id", "source_user", "target_user", "interaction_type",
    "text", "timestamp", "like_count", "reaction_count", "reply_count",
    "provenance", "collection_method",
]

DELAI_ENTRE_APPELS = 0.7
DELAI_EXPIRATION = 60
#: Garde-fou contre une pagination qui ne se terminerait pas ; largement au-dessus
#: du volume attendu pour une publication. Toute troncature est signalée.
PAGES_MAX = 200


def fichier_checkpoint() -> Path:
    """Chemin du fichier de reprise, résolu à l'appel.

    La résolution tardive garantit qu'un test redirigeant ``REPERTOIRE_BRUT``
    n'écrit jamais dans le répertoire de données réelles.
    """
    return REPERTOIRE_BRUT / NOM_CHECKPOINT


def charger_checkpoints(chemin: Path | None = None) -> dict:
    """Curseurs de reprise enregistrés lors des exécutions précédentes."""
    chemin = chemin or fichier_checkpoint()
    if not chemin.exists():
        return {}
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def enregistrer_checkpoint(cle: str, valeur: dict, chemin: Path | None = None) -> None:
    """Enregistre l'état de pagination d'une source, immédiatement après la page."""
    chemin = chemin or fichier_checkpoint()
    donnees = charger_checkpoints(chemin)
    donnees[cle] = valeur
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(
        json.dumps(donnees, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


class ErreurCollecte(Exception):
    """Erreur bloquante de collecte, formulée pour l'utilisateur."""


class CleAbsente(ErreurCollecte):
    """La variable d'environnement contenant la clé d'API n'est pas définie."""


# --------------------------------------------------------------------------
# Client HTTP
# --------------------------------------------------------------------------


class ClientScrapeCreators:
    """Client minimal. La clé transite uniquement par l'en-tête ``x-api-key``."""

    def __init__(self, cle: str) -> None:
        self._cle = cle
        self.appels = 0
        self.credits = 0

    def get(self, chemin: str, parametres: dict[str, Any]) -> dict:
        propres = {c: v for c, v in parametres.items() if v not in (None, "", False)}
        url = f"{BASE_URL}{chemin}?{urllib.parse.urlencode(propres)}"
        requete = urllib.request.Request(
            url,
            headers={
                "x-api-key": self._cle,
                "Accept": "application/json",
                "User-Agent": "social-polarization-MVP/0.3 (recherche academique)",
            },
        )
        self.appels += 1
        try:
            with urllib.request.urlopen(requete, timeout=DELAI_EXPIRATION) as reponse:
                charge = json.loads(reponse.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as erreur:
            detail = erreur.read(500).decode("utf-8", "replace").replace("\n", " ")[:300]
            raise ErreurCollecte(f"HTTP {erreur.code} sur {chemin} — {detail}") from erreur
        except Exception as erreur:
            raise ErreurCollecte(f"{type(erreur).__name__} sur {chemin} : {erreur}") from erreur

        self.credits += int(charge.get("credits_charged") or 0)
        time.sleep(DELAI_ENTRE_APPELS)
        return charge

    def url_masquee(self, chemin: str, parametres: dict[str, Any]) -> str:
        """URL journalisable : ne contient jamais la clé (transmise par en-tête)."""
        propres = {c: v for c, v in parametres.items() if v not in (None, "", False)}
        return f"{chemin}?{urllib.parse.urlencode(propres)}"


# --------------------------------------------------------------------------
# Pseudonymisation stable
# --------------------------------------------------------------------------


class Pseudonymiseur:
    """Attribue « Utilisateur_0001 »… de façon stable entre exécutions."""

    def __init__(self, chemin: Path) -> None:
        self._chemin = chemin
        self._correspondance: dict[str, str] = {}
        if chemin.exists():
            donnees = json.loads(chemin.read_text(encoding="utf-8"))
            self._correspondance = dict(donnees.get("correspondance", {}))

    def pseudonyme(self, identifiant: str | None, nom: str | None = None) -> str:
        cle = (identifiant or nom or "").strip()
        if not cle:
            return ""
        if cle not in self._correspondance:
            self._correspondance[cle] = f"Utilisateur_{len(self._correspondance) + 1:04d}"
        return self._correspondance[cle]

    def enregistrer(self) -> None:
        self._chemin.parent.mkdir(parents=True, exist_ok=True)
        self._chemin.write_text(
            json.dumps(
                {
                    "avertissement": (
                        "Correspondance locale entre comptes publics réels et pseudonymes. "
                        "Ne jamais publier, ne jamais versionner, ne jamais exposer dans public/."
                    ),
                    "correspondance": self._correspondance,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def __len__(self) -> int:
        return len(self._correspondance)


# --------------------------------------------------------------------------
# Utilitaires
# --------------------------------------------------------------------------


def _horodatage() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cle_fichier(identifiant: str) -> str:
    """Clé courte mais **unique** pour nommer les fichiers bruts d'un commentaire.

    Les identifiants Facebook partagent un long préfixe commun (base64 de
    « comment:<post_id>_… ») : les tronquer faisait collisionner tous les
    fichiers de réponses d'une même publication, qui s'écrasaient les uns les
    autres. Une empreinte de l'identifiant complet supprime ce risque.
    """
    return hashlib.sha1(str(identifiant).encode("utf-8")).hexdigest()[:16]


def _sauver_brut(nom: str, charge: dict) -> None:
    REPERTOIRE_BRUT.mkdir(parents=True, exist_ok=True)
    (REPERTOIRE_BRUT / nom).write_text(
        json.dumps(charge, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def _premier(charge: dict, *cles: str) -> Any:
    for cle in cles:
        if isinstance(charge, dict) and charge.get(cle) not in (None, ""):
            return charge[cle]
    return None


def _cursor_suivant(charge: dict) -> str | None:
    """Cursor de la page suivante, ou None si la pagination est terminée."""
    cursor = _premier(charge, "cursor", "next_cursor", "end_cursor")
    encore = charge.get("has_next_page")
    if encore is None:
        encore = charge.get("has_more")
    if encore is False:
        return None
    return str(cursor) if cursor else None


def _ligne(**valeurs: Any) -> dict[str, str]:
    ligne = {colonne: "" for colonne in COLONNES}
    ligne["provenance"] = PROVENANCE
    ligne["collection_method"] = METHODE
    for cle, valeur in valeurs.items():
        if valeur is None:
            continue
        ligne[cle] = str(valeur)
    return ligne


# --------------------------------------------------------------------------
# Facebook
# --------------------------------------------------------------------------


def collecter_facebook(
    client: ClientScrapeCreators,
    source: dict,
    pseudo: Pseudonymiseur,
    journal: dict,
    lignes: list[dict] | None = None,
) -> list[dict]:
    identifiant = source["source_id"]
    url = source["url"]
    lignes = lignes if lignes is not None else []

    detail = client.get("/v1/facebook/post", {"url": url})
    _sauver_brut(f"{identifiant}_post.json", detail)
    journal["pages_fetched"] += 1

    bloc = detail.get("post") if isinstance(detail.get("post"), dict) else detail
    feedback_id = _premier(bloc, "feedback_id", "feedbackId")
    post_id = str(_premier(bloc, "post_id", "id", "postId") or f"{identifiant}_post")
    auteur = bloc.get("author") if isinstance(bloc.get("author"), dict) else {}
    # Le détail de post Facebook expose « description » et « creation_time ».
    texte_post = _premier(bloc, "description", "message", "text", "caption") or ""
    date_post = _premier(bloc, "creation_time", "created_at", "createdAt", "time") or ""
    journal["post_retrieved"] = bool(texte_post or post_id)

    auteur_pseudo = pseudo.pseudonyme(auteur.get("id"), auteur.get("name"))
    lignes.append(
        _ligne(
            platform="facebook", source_id=identifiant, source_url=url, post_id=post_id,
            interaction_id=post_id, source_user=auteur_pseudo, interaction_type="post",
            text=texte_post, timestamp=date_post,
            like_count=_premier(bloc, "like_count"),
            reaction_count=_premier(bloc, "reaction_count", "reactions_count"),
            reply_count=_premier(bloc, "comment_count", "comments_count"),
        )
    )

    # --- commentaires, paginés jusqu'à épuisement, avec reprise ---
    cle_reprise = f"{identifiant}:comments"
    reprise = charger_checkpoints().get(cle_reprise) or {}
    cursor = reprise.get("cursor") if not reprise.get("done") else None
    page = int(reprise.get("page") or 0) if cursor else 0
    if cursor:
        journal["reprise_page"] = page + 1
        print(f"     reprise à la page {page + 1} (curseur enregistré)")
    parametres_base = {"feedback_id": feedback_id} if feedback_id else {"url": url}
    while page < PAGES_MAX:
        page += 1
        charge = client.get("/v1/facebook/post/comments", {**parametres_base, "cursor": cursor})
        # Sauvegarde immédiate : la page est acquise même si la suite échoue.
        _sauver_brut(f"{identifiant}_comments_page_{page:03d}.json", charge)
        journal["pages_fetched"] += 1
        commentaires = charge.get("comments") or []
        for commentaire in commentaires:
            auteur_c = commentaire.get("author") if isinstance(commentaire.get("author"), dict) else {}
            pseudo_c = pseudo.pseudonyme(auteur_c.get("id"), auteur_c.get("name"))
            lignes.append(
                _ligne(
                    platform="facebook", source_id=identifiant, source_url=url, post_id=post_id,
                    interaction_id=commentaire.get("id"), parent_interaction_id=post_id,
                    source_user=pseudo_c, target_user=auteur_pseudo, interaction_type="comment",
                    text=commentaire.get("text"), timestamp=commentaire.get("created_at"),
                    reaction_count=commentaire.get("reaction_count"),
                    reply_count=commentaire.get("reply_count"),
                )
            )
            journal["comments_count"] += 1

            # --- réponses de ce commentaire ---
            nombre_reponses = int(commentaire.get("reply_count") or 0)
            jeton = _premier(commentaire, "expansion_token", "expansionToken")
            feedback_commentaire = _premier(commentaire, "feedback_id", "feedbackId")
            if nombre_reponses <= 0:
                continue
            if not (jeton and feedback_commentaire):
                journal.setdefault("replies_non_recuperables", 0)
                journal["replies_non_recuperables"] += nombre_reponses
                continue
            lignes += _reponses_facebook(
                client, source, pseudo, journal, post_id, commentaire,
                feedback_commentaire, jeton, pseudo_c,
            )

        cursor = _cursor_suivant(charge)
        # Checkpoint écrit après chaque page : une interruption ne fait pas
        # recommencer depuis la page 1.
        enregistrer_checkpoint(
            cle_reprise, {"cursor": cursor, "page": page, "done": not bool(cursor)}
        )
        if not cursor or not commentaires:
            break
    journal["comments_truncated"] = bool(cursor)
    return lignes


def _reponses_facebook(
    client, source, pseudo, journal, post_id, commentaire, feedback_id, jeton, pseudo_parent
) -> list[dict]:
    identifiant = source["source_id"]
    lignes: list[dict] = []
    cursor, page = None, 0
    court = _cle_fichier(commentaire.get("id"))
    while page < PAGES_MAX:
        page += 1
        try:
            charge = client.get(
                "/v1/facebook/post/comment/replies",
                {"feedback_id": feedback_id, "expansion_token": jeton, "cursor": cursor},
            )
        except ErreurCollecte as erreur:
            journal.setdefault("erreurs_replies", []).append(str(erreur)[:200])
            break
        _sauver_brut(f"{identifiant}_reply_{court}_page_{page:03d}.json", charge)
        journal["pages_fetched"] += 1
        reponses = charge.get("replies") or charge.get("comments") or []
        for reponse in reponses:
            auteur_r = reponse.get("author") if isinstance(reponse.get("author"), dict) else {}
            lignes.append(
                _ligne(
                    platform="facebook", source_id=identifiant, source_url=source["url"],
                    post_id=post_id, interaction_id=reponse.get("id"),
                    parent_interaction_id=commentaire.get("id"),
                    source_user=pseudo.pseudonyme(auteur_r.get("id"), auteur_r.get("name")),
                    target_user=pseudo_parent, interaction_type="reply",
                    text=reponse.get("text"), timestamp=reponse.get("created_at"),
                    reaction_count=reponse.get("reaction_count"),
                    reply_count=reponse.get("reply_count"),
                )
            )
            journal["replies_count"] += 1
        cursor = _cursor_suivant(charge)
        if not cursor or not reponses:
            break
    return lignes


# --------------------------------------------------------------------------
# Instagram
# --------------------------------------------------------------------------


def collecter_instagram(
    client: ClientScrapeCreators,
    source: dict,
    pseudo: Pseudonymiseur,
    journal: dict,
    lignes: list[dict] | None = None,
) -> list[dict]:
    identifiant = source["source_id"]
    url = source["url"]
    lignes = lignes if lignes is not None else []

    detail = client.get("/v1/instagram/post", {"url": url})
    _sauver_brut(f"{identifiant}_post.json", detail)
    journal["pages_fetched"] += 1

    bloc = detail.get("data") if isinstance(detail.get("data"), dict) else detail
    for cle in ("xdt_shortcode_media", "shortcode_media", "post", "item"):
        if isinstance(bloc.get(cle), dict):
            bloc = bloc[cle]
            break
    post_id = str(_premier(bloc, "id", "pk", "shortcode") or f"{identifiant}_post")
    proprietaire = bloc.get("owner") or bloc.get("user") or {}
    auteur_pseudo = pseudo.pseudonyme(
        proprietaire.get("id") or proprietaire.get("pk"), proprietaire.get("username")
    )
    legende = _premier(bloc, "caption", "edge_media_to_caption", "text")
    if isinstance(legende, dict):
        legende = _premier(legende, "text") or ""
    texte_post = legende if isinstance(legende, str) else ""
    journal["post_retrieved"] = bool(post_id)

    lignes.append(
        _ligne(
            platform="instagram", source_id=identifiant, source_url=url, post_id=post_id,
            interaction_id=post_id, source_user=auteur_pseudo, interaction_type="post",
            text=texte_post, timestamp=_premier(bloc, "taken_at", "created_at", "taken_at_timestamp"),
            like_count=_premier(bloc, "like_count", "edge_media_preview_like"),
            reply_count=_premier(bloc, "comment_count", "comment_count_total"),
        )
    )

    # --- commentaires ; include_replies volontairement non utilisé (15 crédits/appel) ---
    cursor, page = None, 0
    while page < PAGES_MAX:
        page += 1
        charge = client.get("/v2/instagram/post/comments", {"url": url, "cursor": cursor})
        _sauver_brut(f"{identifiant}_comments_page_{page:03d}.json", charge)
        journal["pages_fetched"] += 1
        commentaires = charge.get("comments") or []
        for commentaire in commentaires:
            utilisateur = commentaire.get("user") or {}
            pseudo_c = pseudo.pseudonyme(
                utilisateur.get("id") or utilisateur.get("pk"), utilisateur.get("username")
            )
            lignes.append(
                _ligne(
                    platform="instagram", source_id=identifiant, source_url=url, post_id=post_id,
                    interaction_id=commentaire.get("id"), parent_interaction_id=post_id,
                    source_user=pseudo_c, target_user=auteur_pseudo, interaction_type="comment",
                    text=commentaire.get("text"), timestamp=commentaire.get("created_at"),
                    like_count=commentaire.get("comment_like_count"),
                    reply_count=commentaire.get("child_comment_count"),
                )
            )
            journal["comments_count"] += 1

            if int(commentaire.get("child_comment_count") or 0) > 0:
                lignes += _reponses_instagram(
                    client, source, pseudo, journal, post_id, commentaire, pseudo_c
                )

        cursor = _cursor_suivant(charge)
        if not cursor or not commentaires:
            break
    journal["comments_truncated"] = bool(cursor)
    return lignes


def _reponses_instagram(
    client, source, pseudo, journal, post_id, commentaire, pseudo_parent
) -> list[dict]:
    identifiant = source["source_id"]
    lignes: list[dict] = []
    cursor, page = None, 0
    court = _cle_fichier(commentaire.get("id"))
    while page < PAGES_MAX:
        page += 1
        try:
            charge = client.get(
                "/v1/instagram/post/comment/replies",
                {"url": source["url"], "comment_id": commentaire.get("id"), "cursor": cursor},
            )
        except ErreurCollecte as erreur:
            journal.setdefault("erreurs_replies", []).append(str(erreur)[:200])
            break
        _sauver_brut(f"{identifiant}_reply_{court}_page_{page:03d}.json", charge)
        journal["pages_fetched"] += 1
        reponses = charge.get("comments") or charge.get("replies") or []
        for reponse in reponses:
            utilisateur = reponse.get("user") or {}
            lignes.append(
                _ligne(
                    platform="instagram", source_id=identifiant, source_url=source["url"],
                    post_id=post_id, interaction_id=reponse.get("id"),
                    parent_interaction_id=reponse.get("parent_comment_id") or commentaire.get("id"),
                    source_user=pseudo.pseudonyme(
                        utilisateur.get("id") or utilisateur.get("pk"), utilisateur.get("username")
                    ),
                    target_user=pseudo_parent, interaction_type="reply",
                    text=reponse.get("text"), timestamp=reponse.get("created_at"),
                    like_count=reponse.get("comment_like_count"),
                    reply_count=reponse.get("child_comment_count"),
                )
            )
            journal["replies_count"] += 1
        cursor = _cursor_suivant(charge)
        if not cursor or not reponses:
            break
    return lignes


# --------------------------------------------------------------------------
# X / Twitter — aucun endpoint de réponses disponible
# --------------------------------------------------------------------------


def collecter_x(
    client: ClientScrapeCreators,
    source: dict,
    pseudo: Pseudonymiseur,
    journal: dict,
    lignes: list[dict] | None = None,
) -> list[dict]:
    identifiant = source["source_id"]
    url = source["url"]
    lignes = lignes if lignes is not None else []

    detail = client.get("/v1/twitter/tweet", {"url": url})
    _sauver_brut(f"{identifiant}_tweet.json", detail)
    journal["pages_fetched"] += 1
    journal["replies_supported"] = False
    journal["replies_note"] = (
        "La spec OpenAPI publique de ScrapeCreators ne propose aucun endpoint de réponses "
        "ou de fil de conversation pour X : seuls /v1/twitter/{profile, tweet, "
        "tweet/transcript, user-tweets, community, community/tweets} existent. "
        "Seul le post réel est enregistré ; aucune réponse n'est fabriquée."
    )

    bloc = detail.get("tweet") if isinstance(detail.get("tweet"), dict) else detail
    for cle in ("data", "legacy", "result"):
        if isinstance(bloc.get(cle), dict) and not bloc.get("text"):
            bloc = bloc[cle]
    auteur = bloc.get("author") or bloc.get("user") or {}
    post_id = str(_premier(bloc, "id", "id_str", "rest_id") or f"{identifiant}_post")
    texte = _premier(bloc, "text", "full_text", "legacy_full_text") or ""
    journal["post_retrieved"] = bool(texte or post_id)

    lignes.append(
        _ligne(
            platform="x", source_id=identifiant, source_url=url, post_id=post_id,
            interaction_id=post_id,
            source_user=pseudo.pseudonyme(
                auteur.get("id") or auteur.get("id_str"),
                auteur.get("screen_name") or auteur.get("username") or auteur.get("name"),
            ),
            interaction_type="post", text=texte,
            timestamp=_premier(bloc, "created_at", "createdAt"),
            like_count=_premier(bloc, "favorite_count", "like_count"),
            reply_count=_premier(bloc, "reply_count", "replyCount"),
        )
    )
    return lignes


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

COLLECTEURS = {
    "facebook": collecter_facebook,
    "instagram": collecter_instagram,
    "x": collecter_x,
}


def _dedupliquer(lignes: list[dict]) -> tuple[list[dict], int]:
    """Retire uniquement les doublons exacts d'identifiant d'interaction."""
    vus: set[str] = set()
    retenues: list[dict] = []
    doublons = 0
    for ligne in lignes:
        cle = ligne.get("interaction_id", "")
        if cle and cle in vus:
            doublons += 1
            continue
        if cle:
            vus.add(cle)
        retenues.append(ligne)
    return retenues, doublons


def _ecrire_csv(chemin: Path, lignes: list[dict]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8", newline="") as flux:
        writer = csv.DictWriter(flux, fieldnames=COLONNES, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(lignes)


def _statut(journal: dict) -> str:
    """Statut d'une source.

    Règle non négociable : une source ayant réellement fourni des données n'est
    jamais déclarée « failed ». Une erreur survenue après des données acquises
    donne « partial », de même qu'une pagination laissée inachevée.
    """
    donnees = journal.get("comments_count", 0) + journal.get("replies_count", 0)

    if journal.get("platform") == "x" and journal.get("replies_supported") is False:
        if journal.get("error_if_any") and journal.get("total_rows", 0) == 0:
            return "failed"
        return "unsupported" if journal.get("total_rows", 0) <= 1 else "partial"

    if journal.get("error_if_any") or journal.get("interrompue"):
        return "partial" if donnees > 0 else "failed"
    if journal.get("comments_truncated"):
        return "partial"
    if donnees == 0:
        return "no_comments_returned" if journal.get("post_retrieved") else "failed"
    return "complete"


def collecter(cle: str, sources: list[dict]) -> dict:
    client = ClientScrapeCreators(cle)
    pseudo = Pseudonymiseur(FICHIER_PSEUDONYMES)
    rapports = []

    for source in sources:
        identifiant = source["source_id"]
        plateforme = str(source.get("platform", "")).lower()
        journal = {
            "source_id": identifiant,
            "platform": plateforme,
            "source_url": source["url"],
            "post_retrieved": False,
            "comments_count": 0,
            "replies_count": 0,
            "total_rows": 0,
            "pages_fetched": 0,
            "credits_used": 0,
            "collection_status": "failed",
            "error_if_any": "",
        }
        credits_avant = client.credits
        print(f"  → {identifiant} ({plateforme})")

        collecteur = COLLECTEURS.get(plateforme)
        # La liste appartient à l'orchestrateur : ce qui a déjà été collecté
        # survit à une erreur réseau survenue en cours de pagination.
        lignes: list[dict] = []
        if collecteur is None:
            journal["error_if_any"] = f"Plateforme non prise en charge : {plateforme}"
        else:
            try:
                collecteur(client, source, pseudo, journal, lignes)
            except ErreurCollecte as erreur:
                journal["error_if_any"] = str(erreur)
                journal["interrompue"] = True
                print(f"     interruption : {erreur}")
                print(f"     {len(lignes)} lignes déjà collectées sont conservées")

        lignes, doublons = _dedupliquer(lignes)
        journal["duplicates_removed"] = doublons
        journal["total_rows"] = len(lignes)
        journal["credits_used"] = client.credits - credits_avant
        journal["collection_status"] = _statut(journal)

        _ecrire_csv(REPERTOIRE_CSV / f"{identifiant}.csv", lignes)
        rapports.append(journal)
        print(
            f"     {journal['comments_count']} commentaires, {journal['replies_count']} réponses, "
            f"{journal['pages_fetched']} pages, statut « {journal['collection_status']} »"
        )

    pseudo.enregistrer()

    rapport = {
        "genere_le": _horodatage(),
        "api": "ScrapeCreators",
        "base_url": BASE_URL,
        "endpoints_utilises": {
            "facebook": [
                "/v1/facebook/post",
                "/v1/facebook/post/comments",
                "/v1/facebook/post/comment/replies",
            ],
            "instagram": [
                "/v1/instagram/post",
                "/v2/instagram/post/comments",
                "/v1/instagram/post/comment/replies",
            ],
            "x": ["/v1/twitter/tweet"],
        },
        "regles": [
            "La clé d'API transite uniquement par l'en-tête x-api-key et n'est jamais "
            "écrite dans le code, les CSV, les JSON, les journaux ni la documentation.",
            "Aucune donnée n'est fabriquée : un CSV peut ne contenir que le post réel.",
            "Seuls les doublons exacts d'identifiant d'interaction sont supprimés ; "
            "aucun contenu n'est filtré sur son ton, sa langue ou sa qualité.",
            "include_replies n'est jamais activé sur Instagram (15 crédits par appel) : "
            "l'endpoint de réponses dédié est utilisé à la place.",
        ],
        "synthese": {
            "sources": len(rapports),
            "comments_total": sum(r["comments_count"] for r in rapports),
            "replies_total": sum(r["replies_count"] for r in rapports),
            "rows_total": sum(r["total_rows"] for r in rapports),
            "pages_total": sum(r["pages_fetched"] for r in rapports),
            "credits_total": client.credits,
            "appels_api": client.appels,
            "utilisateurs_pseudonymises": len(pseudo),
        },
        "sources": rapports,
    }
    FICHIER_RAPPORT.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_RAPPORT.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return rapport


def obtenir_cle() -> str:
    cle = os.environ.get(VARIABLE_CLE, "").strip()
    if not cle:
        raise CleAbsente(
            f"La variable d'environnement {VARIABLE_CLE} n'est pas définie.\n\n"
            "  Définissez-la puis relancez :\n\n"
            '    export SCRAPECREATORS_API_KEY="ma_cle"\n'
            "    python analysis/collect_scrapecreators.py\n"
        )
    return cle


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Collecte des commentaires publics via l'API ScrapeCreators."
    )
    analyseur.add_argument("--sources", type=Path, default=FICHIER_SOURCES)
    arguments = analyseur.parse_args()

    try:
        cle = obtenir_cle()
    except CleAbsente as erreur:
        print(f"\nCOLLECTE INTERROMPUE : {erreur}", file=sys.stderr)
        return 2

    sources = json.loads(arguments.sources.read_text(encoding="utf-8"))["sources"]
    print(f"Collecte ScrapeCreators — {len(sources)} sources")
    rapport = collecter(cle, sources)
    s = rapport["synthese"]

    print("\nRésultats par source :")
    for journal in rapport["sources"]:
        print(
            f"  {journal['source_id']:15} : {journal['comments_count']:>4} commentaires "
            f"+ {journal['replies_count']:>4} réponses  "
            f"({journal['pages_fetched']} pages, {journal['collection_status']})"
        )
    print(f"\n  Commentaires réels : {s['comments_total']}")
    print(f"  Réponses réelles   : {s['replies_total']}")
    print(f"  Lignes totales     : {s['rows_total']}")
    print(f"  Crédits consommés  : {s['credits_total']} ({s['appels_api']} appels)")
    print(f"  Rapport : {FICHIER_RAPPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
