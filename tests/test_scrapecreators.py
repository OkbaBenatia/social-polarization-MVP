"""Tests de la collecte ScrapeCreators.

Aucun appel réseau : un client factice rejoue des réponses conformes aux
exemples de la spec OpenAPI publique de ScrapeCreators. Les règles vérifiées
sont celles qui conditionnent la validité scientifique : pagination menée
jusqu'au bout, contenu jamais filtré, rien de fabriqué, pseudonymisation stable.
"""

from __future__ import annotations

import os

import pytest

import collect_scrapecreators as sc
import provenance as prov


class ClientFactice:
    """Rejoue des réponses préenregistrées et note les appels effectués."""

    def __init__(self, reponses: dict[str, list[dict]]) -> None:
        self._reponses = {chemin: list(pages) for chemin, pages in reponses.items()}
        self.appels: list[tuple[str, dict]] = []
        self.credits = 0

    def get(self, chemin: str, parametres: dict) -> dict:
        self.appels.append((chemin, dict(parametres)))
        pages = self._reponses.get(chemin)
        if not pages:
            return {"success": True}
        charge = pages.pop(0)
        self.credits += int(charge.get("credits_charged") or 0)
        return charge


@pytest.fixture
def pseudo(tmp_path):
    return sc.Pseudonymiseur(tmp_path / "users.json")


@pytest.fixture
def journal():
    return {
        "source_id": "facebook_001", "platform": "facebook",
        "post_retrieved": False, "comments_count": 0, "replies_count": 0,
        "pages_fetched": 0, "total_rows": 0,
    }


@pytest.fixture(autouse=True)
def _brut_temporaire(tmp_path, monkeypatch):
    """Aucun test n'écrit dans les répertoires de données réelles."""
    monkeypatch.setattr(sc, "REPERTOIRE_BRUT", tmp_path / "raw")


@pytest.fixture(autouse=True)
def _pas_d_ecriture_dans_les_donnees_reelles(tmp_path, monkeypatch):
    monkeypatch.setattr(sc, "REPERTOIRE_CSV", tmp_path / "csv")
    monkeypatch.setattr(sc, "FICHIER_PSEUDONYMES", tmp_path / "users.json")


SOURCE_FB = {
    "source_id": "facebook_001",
    "platform": "facebook",
    "url": "https://www.facebook.com/share/v/18hGjKiFVK/",
}


def _commentaire(identifiant, texte, reponses=0, feedback=None, jeton=None):
    bloc = {
        "id": identifiant, "text": texte, "created_at": "2026-08-13T10:00:00.000Z",
        "reply_count": reponses, "reaction_count": 5,
        "author": {"id": f"auteur_{identifiant}", "name": f"Nom {identifiant}"},
    }
    if feedback:
        bloc["feedback_id"] = feedback
    if jeton:
        bloc["expansion_token"] = jeton
    return bloc


# --------------------------------------------------------------------------
# Clé d'API
# --------------------------------------------------------------------------


def test_cle_absente_donne_la_commande_exacte(monkeypatch):
    monkeypatch.delenv(sc.VARIABLE_CLE, raising=False)
    with pytest.raises(sc.CleAbsente) as erreur:
        sc.obtenir_cle()
    message = str(erreur.value)
    assert 'export SCRAPECREATORS_API_KEY="ma_cle"' in message
    assert "python analysis/collect_scrapecreators.py" in message


def test_cle_jamais_dans_l_url_journalisable():
    client = sc.ClientScrapeCreators("cle_ultra_secrete")
    trace = client.url_masquee("/v1/facebook/post/comments", {"url": "https://x", "cursor": "c"})
    assert "cle_ultra_secrete" not in trace
    assert "x-api-key" not in trace


# --------------------------------------------------------------------------
# Pagination
# --------------------------------------------------------------------------


def test_pagination_suit_le_cursor_jusqu_au_bout(pseudo, journal):
    """La collecte ne s'arrête pas à la première page tant qu'un cursor existe."""
    client = ClientFactice(
        {
            "/v1/facebook/post": [{"post": {"id": "p1", "message": "Publication", "feedback_id": "fb1"}}],
            "/v1/facebook/post/comments": [
                {"comments": [_commentaire("c1", "un")], "cursor": "CUR2", "has_next_page": True},
                {"comments": [_commentaire("c2", "deux")], "cursor": "CUR3", "has_next_page": True},
                {"comments": [_commentaire("c3", "trois")], "cursor": None, "has_next_page": False},
            ],
        }
    )
    lignes = sc.collecter_facebook(client, SOURCE_FB, pseudo, journal)

    appels = [p for c, p in client.appels if c == "/v1/facebook/post/comments"]
    assert len(appels) == 3, "les trois pages doivent être demandées"
    assert appels[1]["cursor"] == "CUR2"
    assert appels[2]["cursor"] == "CUR3"
    assert journal["comments_count"] == 3
    assert journal["comments_truncated"] is False
    assert len(lignes) == 4  # 1 post + 3 commentaires


def test_troncature_signalee_si_cursor_restant(pseudo, journal, monkeypatch):
    """Si la pagination est coupée par le garde-fou, la troncature est signalée."""
    monkeypatch.setattr(sc, "PAGES_MAX", 2)
    client = ClientFactice(
        {
            "/v1/facebook/post": [{"post": {"id": "p1", "feedback_id": "fb1"}}],
            "/v1/facebook/post/comments": [
                {"comments": [_commentaire("c1", "un")], "cursor": "A", "has_next_page": True},
                {"comments": [_commentaire("c2", "deux")], "cursor": "B", "has_next_page": True},
            ],
        }
    )
    sc.collecter_facebook(client, SOURCE_FB, pseudo, journal)
    assert journal["comments_truncated"] is True
    assert sc._statut({**journal, "total_rows": 3}) == "partial"


def test_replies_paginees_et_rattachees_au_parent(pseudo, journal):
    client = ClientFactice(
        {
            "/v1/facebook/post": [{"post": {"id": "p1", "feedback_id": "fb1"}}],
            "/v1/facebook/post/comments": [
                {
                    "comments": [_commentaire("c1", "parent", reponses=2, feedback="fbc1", jeton="tok1")],
                    "cursor": None, "has_next_page": False,
                }
            ],
            "/v1/facebook/post/comment/replies": [
                {"replies": [{"id": "r1", "text": "réponse une", "author": {"id": "a1", "name": "A"}}],
                 "cursor": "R2", "has_next_page": True},
                {"replies": [{"id": "r2", "text": "réponse deux", "author": {"id": "a2", "name": "B"}}],
                 "cursor": None, "has_next_page": False},
            ],
        }
    )
    lignes = sc.collecter_facebook(client, SOURCE_FB, pseudo, journal)
    reponses = [l for l in lignes if l["interaction_type"] == "reply"]
    assert journal["replies_count"] == 2
    assert {l["parent_interaction_id"] for l in reponses} == {"c1"}
    appels = [p for c, p in client.appels if c.endswith("/comment/replies")]
    assert appels[0]["feedback_id"] == "fbc1" and appels[0]["expansion_token"] == "tok1"


def test_replies_non_recuperables_signalees_sans_invention(pseudo, journal):
    """Sans feedback_id/expansion_token, aucune réponse n'est inventée."""
    client = ClientFactice(
        {
            "/v1/facebook/post": [{"post": {"id": "p1", "feedback_id": "fb1"}}],
            "/v1/facebook/post/comments": [
                {"comments": [_commentaire("c1", "parent", reponses=7)],
                 "cursor": None, "has_next_page": False}
            ],
        }
    )
    lignes = sc.collecter_facebook(client, SOURCE_FB, pseudo, journal)
    assert journal["replies_count"] == 0
    assert journal["replies_non_recuperables"] == 7
    assert not [l for l in lignes if l["interaction_type"] == "reply"]


# --------------------------------------------------------------------------
# Intégrité du contenu
# --------------------------------------------------------------------------


def test_contenu_sensible_integralement_preserve(pseudo, journal):
    """Insultes, arabe, darija, fautes et emojis sont conservés tels quels."""
    textes = [
        "ce truc est nul, vraiment débile 😡",
        "متضامن مع الفنانة ضد الحملة المسعورة",
        "wach hadi? makanch m3a hadchi 🤷",
        "jsuis pas dacor du tt!!!",
    ]
    client = ClientFactice(
        {
            "/v1/facebook/post": [{"post": {"id": "p1", "feedback_id": "fb1"}}],
            "/v1/facebook/post/comments": [
                {"comments": [_commentaire(f"c{i}", t) for i, t in enumerate(textes)],
                 "cursor": None, "has_next_page": False}
            ],
        }
    )
    lignes = sc.collecter_facebook(client, SOURCE_FB, pseudo, journal)
    collectes = [l["text"] for l in lignes if l["interaction_type"] == "comment"]
    assert collectes == textes


def test_deduplication_ne_retire_que_les_doublons_exacts():
    lignes = [
        {"interaction_id": "c1", "text": "identique"},
        {"interaction_id": "c1", "text": "identique"},
        {"interaction_id": "c2", "text": "identique"},
    ]
    retenues, doublons = sc._dedupliquer(lignes)
    assert doublons == 1
    assert [l["interaction_id"] for l in retenues] == ["c1", "c2"]


def test_pseudonymisation_stable_et_relation_conservee(pseudo, journal):
    client = ClientFactice(
        {
            "/v1/facebook/post": [
                {"post": {"id": "p1", "feedback_id": "fb1", "author": {"id": "auteur_post", "name": "Auteur"}}}
            ],
            "/v1/facebook/post/comments": [
                {"comments": [_commentaire("c1", "un"), _commentaire("c1bis", "deux")],
                 "cursor": None, "has_next_page": False}
            ],
        }
    )
    lignes = sc.collecter_facebook(client, SOURCE_FB, pseudo, journal)
    commentaires = [l for l in lignes if l["interaction_type"] == "comment"]
    # Chaque commentaire vise l'auteur du post : la relation reste reconstructible.
    auteur_post = lignes[0]["source_user"]
    assert all(l["target_user"] == auteur_post for l in commentaires)
    assert all(l["source_user"].startswith("Utilisateur_") for l in lignes)
    # Le même compte réel garde le même pseudonyme.
    assert pseudo.pseudonyme("auteur_post") == auteur_post


# --------------------------------------------------------------------------
# X / Twitter
# --------------------------------------------------------------------------


def test_x_sans_endpoint_de_replies_ne_fabrique_rien(pseudo):
    source = {"source_id": "x_001", "platform": "x",
              "url": "https://x.com/i/status/2087872720012796385"}
    journal = {"source_id": "x_001", "platform": "x", "post_retrieved": False,
               "comments_count": 0, "replies_count": 0, "pages_fetched": 0, "total_rows": 0}
    client = ClientFactice(
        {"/v1/twitter/tweet": [{"id": "2087872720012796385", "text": "texte réel",
                                "created_at": "2026-08-13T00:00:00Z",
                                "author": {"id": "u1", "screen_name": "compte"}}]}
    )
    lignes = sc.collecter_x(client, source, pseudo, journal)

    assert journal["replies_supported"] is False
    assert len(lignes) == 1 and lignes[0]["interaction_type"] == "post"
    assert lignes[0]["text"] == "texte réel"
    assert journal["replies_count"] == 0
    # Aucun endpoint de réponses n'est appelé : il n'en existe pas.
    assert [c for c, _ in client.appels] == ["/v1/twitter/tweet"]
    assert sc._statut({**journal, "total_rows": 1}) == "unsupported"


# --------------------------------------------------------------------------
# Schéma CSV
# --------------------------------------------------------------------------


def test_schema_csv_conforme_et_provenance_reelle():
    assert sc.COLONNES[:6] == [
        "platform", "source_id", "source_url", "post_id",
        "interaction_id", "parent_interaction_id",
    ]
    assert sc.PROVENANCE == "scrapecreators_public"
    assert sc.METHODE == "scrapecreators_api"
    assert prov.est_reelle(sc.PROVENANCE)
    assert sc.PROVENANCE != prov.SYNTHETIC_DEMO


def test_ligne_porte_toujours_la_provenance():
    ligne = sc._ligne(platform="facebook", source_id="facebook_001")
    assert ligne["provenance"] == "scrapecreators_public"
    assert ligne["collection_method"] == "scrapecreators_api"
    assert set(ligne) == set(sc.COLONNES)


# --------------------------------------------------------------------------
# Fusion vers le jeu empirique
# --------------------------------------------------------------------------


def test_csv_scrapecreators_fusionne_vers_le_format_pipeline(tmp_path, monkeypatch):
    """Le CSV ScrapeCreators est converti vers le schéma normalisé du pipeline."""
    import csv as _csv
    import json as _json

    import build_real_dataset as build
    import load_data

    repertoire = tmp_path / "scrapecreators"
    repertoire.mkdir()
    chemin = repertoire / "facebook_001.csv"
    with chemin.open("w", encoding="utf-8", newline="") as flux:
        writer = _csv.DictWriter(flux, fieldnames=sc.COLONNES)
        writer.writeheader()
        writer.writerow(
            sc._ligne(
                platform="facebook", source_id="facebook_001",
                source_url="https://www.facebook.com/share/v/18hGjKiFVK/",
                post_id="p1", interaction_id="p1", source_user="Utilisateur_0001",
                interaction_type="post", text="Publication réelle",
                timestamp="2026-08-13T10:00:00.000Z",
            )
        )
        writer.writerow(
            sc._ligne(
                platform="facebook", source_id="facebook_001",
                source_url="https://www.facebook.com/share/v/18hGjKiFVK/",
                post_id="p1", interaction_id="c1", parent_interaction_id="p1",
                source_user="Utilisateur_0002", target_user="Utilisateur_0001",
                interaction_type="comment", text="Commentaire réel 😡",
                timestamp="2026-08-13T10:12:00.000Z",
            )
        )
    (repertoire / "collection_report.json").write_text(
        _json.dumps({"genere_le": "2026-08-25T18:00:00+00:00"}), encoding="utf-8"
    )

    monkeypatch.setattr(build, "REPERTOIRE_SCRAPECREATORS", repertoire)
    monkeypatch.setattr(build, "RAPPORT_SCRAPECREATORS", repertoire / "collection_report.json")
    monkeypatch.setattr(build, "FICHIER_MANUEL", tmp_path / "absent.csv")
    monkeypatch.setattr(build, "REPERTOIRE_COLLECTE", tmp_path / "vide")

    sortie = tmp_path / "real_interactions.csv"
    cadre, resume = build.construire(sortie)

    assert resume["interactions"] == 2
    assert resume["commentaires"] == 1
    assert resume["publications"] == 1
    assert resume["provenances"] == {"scrapecreators_public": 2}
    # Les colonnes sont bien renommées vers le format normalisé du pipeline.
    assert set(load_data.COLONNES_REQUISES).issubset(set(cadre.columns))
    assert cadre.loc[1, "parent_id"] == "p1"
    assert cadre.loc[1, "url"].startswith("https://www.facebook.com/")
    assert cadre.loc[1, "collected_at"] == "2026-08-25T18:00:00+00:00"
    # Le contenu est intact, emoji compris.
    assert cadre.loc[1, "text"] == "Commentaire réel 😡"

    # Le fichier produit est chargeable par le pipeline en mode empirique.
    charge, meta = load_data.charger_fichier_empirique(sortie)
    assert meta["synthetique"] is False
    assert meta["provenances"] == {"scrapecreators_public": 2}
