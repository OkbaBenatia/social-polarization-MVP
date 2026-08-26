"""Tests de la collecte des données réelles.

Aucun test ne sollicite le réseau : les verdicts ``robots.txt`` et les réponses
HTTP sont simulés. Les règles vérifiées sont celles qui protègent la validité
scientifique : l'ordre des trois voies, l'absence de requête vers une voie
interdite, et le fait qu'aucune interaction ne soit comptée sans avoir été
réellement obtenue.
"""

from __future__ import annotations

import json

import pytest

import collect
import provenance as prov


@pytest.fixture
def source_x() -> dict:
    return {
        "source_id": "x_001",
        "platform": "x",
        "url": "https://x.com/i/status/2087872720012796385",
    }


@pytest.fixture(autouse=True)
def _sans_attente(monkeypatch):
    monkeypatch.setattr(collect.time, "sleep", lambda _: None)
    monkeypatch.setattr(collect, "DELAI_ENTRE_SOURCES", 0)


def test_trois_voies_tentees_dans_l_ordre(monkeypatch, source_x):
    """Les voies A, B puis C sont évaluées, dans cet ordre."""
    monkeypatch.setattr(collect, "_verdict_robots", lambda url: (collect.ROBOTS_INTERDIT, "refus"))
    monkeypatch.delenv(collect.VARIABLE_JETON_X, raising=False)

    resultat = collect.tenter_collecte(source_x)
    ordres = [t["ordre"] for t in resultat["methodes_tentees"]]
    assert ordres == ["A", "B", "C"]
    assert resultat["methodes_tentees"][0]["methode"] == prov.OFFICIAL_API
    assert resultat["methodes_tentees"][1]["methode"] == prov.PUBLIC_PAGE
    assert resultat["methodes_tentees"][2]["methode"] == prov.MANUAL_VERIFIED


def test_api_sans_jeton_declaree_indisponible(monkeypatch, source_x):
    """Sans identifiant, l'API officielle est déclarée indisponible, jamais forcée."""
    monkeypatch.delenv(collect.VARIABLE_JETON_X, raising=False)
    monkeypatch.setattr(
        collect, "_requete", lambda *a, **k: pytest.fail("aucune requête d'API sans jeton")
    )
    monkeypatch.setattr(collect, "_verdict_robots", lambda url: (collect.ROBOTS_INTERDIT, "refus"))

    resultat = collect.tenter_collecte(source_x)
    api = resultat["methodes_tentees"][0]
    assert api["disponible"] is False
    assert api["identifiant_fourni"] is False
    assert resultat["api_disponible"] is False


def test_aucune_requete_de_page_si_robots_interdit(monkeypatch, source_x):
    """Règle non négociable : un refus robots.txt n'est jamais contourné."""
    monkeypatch.delenv(collect.VARIABLE_JETON_X, raising=False)
    monkeypatch.setattr(collect, "_verdict_robots", lambda url: (collect.ROBOTS_INTERDIT, "refus"))
    monkeypatch.setattr(
        collect, "_requete", lambda *a, **k: pytest.fail("aucune requête vers une voie interdite")
    )

    resultat = collect.tenter_collecte(source_x)
    page = resultat["methodes_tentees"][1]
    assert page["requete_effectuee"] is False
    assert page["disponible"] is False
    assert resultat["statut"] == prov.MANUAL_IMPORT_REQUIRED


def test_robots_illisible_vaut_refus(monkeypatch, source_x):
    """Un robots.txt illisible ne vaut jamais autorisation implicite."""
    monkeypatch.delenv(collect.VARIABLE_JETON_X, raising=False)
    monkeypatch.setattr(
        collect, "_verdict_robots", lambda url: (collect.ROBOTS_ILLISIBLE, "illisible")
    )
    monkeypatch.setattr(
        collect, "_requete", lambda *a, **k: pytest.fail("aucune requête ne doit être émise")
    )
    resultat = collect.tenter_collecte(source_x)
    assert resultat["import_manuel_requis"] is True


def test_metadonnees_publiques_ne_valent_pas_interactions(monkeypatch, source_x):
    """Obtenir des métadonnées ne crée aucune interaction : le compteur reste nul."""
    monkeypatch.delenv(collect.VARIABLE_JETON_X, raising=False)
    monkeypatch.setattr(collect, "_verdict_robots", lambda url: (collect.ROBOTS_AUTORISE, "ok"))
    html = '<html><meta property="og:title" content="Titre public"><title>T</title></html>'
    monkeypatch.setattr(collect, "_requete", lambda *a, **k: (200, html, ""))

    resultat = collect.tenter_collecte(source_x)
    assert resultat["metadonnees_publiques"]["og:title"] == "Titre public"
    assert resultat["interactions_reelles"] == 0
    assert resultat["commentaires_reels"] == 0
    assert resultat["statut"] == prov.PARTIAL_REAL_DATA
    assert resultat["import_manuel_requis"] is True


def test_interactions_manuelles_comptees_et_statut_reel(monkeypatch, source_x):
    """Des saisies manuelles vérifiées font passer la source en données réelles."""
    monkeypatch.delenv(collect.VARIABLE_JETON_X, raising=False)
    monkeypatch.setattr(collect, "_verdict_robots", lambda url: (collect.ROBOTS_INTERDIT, "refus"))

    manuelles = {"x_001": {"total": 5, "comment": 3, "reply": 1, "post": 1}}
    resultat = collect.tenter_collecte(source_x, manuelles)

    assert resultat["interactions_reelles"] == 5
    assert resultat["commentaires_reels"] == 3
    assert resultat["reponses_reelles"] == 1
    assert resultat["statut"] == prov.REAL_DATA_COLLECTED
    assert resultat["import_manuel_requis"] is False


def test_lecture_manuelle_ignore_les_lignes_synthetiques(tmp_path):
    """Une ligne synthétique glissée dans l'import manuel n'est jamais comptée."""
    chemin = tmp_path / "manuel.csv"
    entete = ",".join(
        [
            "platform", "source_id", "post_id", "interaction_id", "source_user",
            "target_user", "interaction_type", "text", "timestamp", "parent_id",
            "url", "provenance", "collection_method", "collected_at",
        ]
    )
    chemin.write_text(
        entete
        + "\nx,x_001,p1,i1,u1,,comment,bonjour,,p1,https://x.com/1,manual_verified,saisie,2026-08-25"
        + "\nx,x_001,p1,i2,u2,,comment,inventé,,p1,https://x.com/1,synthetic_demo,demo,2026-08-25\n",
        encoding="utf-8",
    )
    comptes = collect._lire_manuel(chemin)
    assert comptes["x_001"]["total"] == 1
    assert comptes["x_001"]["comment"] == 1


def test_rapport_contient_synthese_et_statuts(monkeypatch, tmp_path):
    """Le rapport agrège les compteurs réels et n'invente aucune valeur."""
    monkeypatch.setattr(collect, "_verdict_robots", lambda url: (collect.ROBOTS_INTERDIT, "refus"))
    monkeypatch.delenv(collect.VARIABLE_JETON_META, raising=False)

    fichier_sources = tmp_path / "sources.json"
    fichier_sources.write_text(
        json.dumps(
            {
                "sources": [
                    {"source_id": "a", "platform": "facebook", "url": "https://exemple.org/a"},
                    {"source_id": "b", "platform": "instagram", "url": "https://exemple.org/b"},
                ]
            }
        ),
        encoding="utf-8",
    )
    rapport_chemin = tmp_path / "rapport.json"
    manuel = tmp_path / "manuel.csv"

    rapport = collect.collecter(fichier_sources, rapport_chemin, manuel)

    assert rapport_chemin.exists()
    synthese = rapport["synthese"]
    assert synthese["sources"] == 2
    assert synthese["interactions_reelles"] == 0
    assert synthese["sources_reelles"] == 0
    assert synthese["sources_import_manuel"] == 2
    for resultat in rapport["resultats"]:
        assert resultat["statut"] in prov.STATUTS_COLLECTE
        assert resultat["interactions_reelles"] == 0
        assert len(resultat["methodes_tentees"]) == 3


def test_rapport_reel_du_projet_couvre_les_sept_sources():
    """Le rapport versionné doit documenter les 7 sources réelles de l'étude."""
    chemin = collect.FICHIER_RAPPORT
    if not chemin.exists():
        pytest.skip("aucune collecte n'a encore été exécutée")
    rapport = json.loads(chemin.read_text(encoding="utf-8"))
    resultats = rapport["resultats"]
    assert len(resultats) == 7
    for resultat in resultats:
        assert resultat["statut"] in prov.STATUTS_COLLECTE
        assert len(resultat["methodes_tentees"]) == 3
        # Aucune interaction ne peut être déclarée sans avoir été réellement obtenue.
        if resultat["interactions_reelles"] == 0:
            assert resultat["import_manuel_requis"] is True
    synthese = rapport["synthese"]
    assert synthese["interactions_reelles"] == sum(
        r["interactions_reelles"] for r in resultats
    )
