"""Tests de la collecte publique.

Aucun test ne sollicite le réseau : les verdicts ``robots.txt`` et les réponses
HTTP sont simulés. L'objectif est de vérifier la règle centrale du module —
**aucune requête n'est émise vers une voie interdite par le protocole
d'exclusion** — ainsi que la structure du rapport produit.
"""

from __future__ import annotations

import json

import pytest

import collect


@pytest.fixture
def source_x() -> dict:
    return {
        "source_id": "x_001",
        "platform": "x",
        "url": "https://x.com/i/status/2087872720012796385",
    }


def test_voies_evaluees_page_et_oembed(monkeypatch, source_x):
    """Chaque source d'une plateforme connue est évaluée sur deux voies."""
    monkeypatch.setattr(collect, "_lecteur_robots", lambda url: (collect.ROBOTS_INTERDIT, "refus"))
    monkeypatch.setattr(collect, "DELAI_ENTRE_REQUETES", 0)
    monkeypatch.setattr(collect.time, "sleep", lambda _: None)

    resultat = collect.tenter_collecte(source_x)

    voies = resultat["voies_evaluees"]
    assert len(voies) == 2
    assert voies[0]["url"] == source_x["url"]
    assert "oembed" in voies[1]["url"].lower()


def test_aucune_requete_si_robots_interdit(monkeypatch, source_x):
    """Règle non négociable : un refus robots.txt n'est jamais contourné."""
    monkeypatch.setattr(collect, "_lecteur_robots", lambda url: (collect.ROBOTS_INTERDIT, "refus"))
    monkeypatch.setattr(collect.time, "sleep", lambda _: None)

    appels: list[str] = []

    def _requete_interdite(url: str):
        appels.append(url)
        raise AssertionError("aucune requête ne doit être émise vers une voie interdite")

    monkeypatch.setattr(collect, "_requete", _requete_interdite)

    resultat = collect.tenter_collecte(source_x)

    assert appels == []
    assert all(not voie["requete_effectuee"] for voie in resultat["voies_evaluees"])
    assert resultat["accessible"] is False
    assert resultat["import_manuel_requis"] is True


def test_robots_illisible_traite_comme_un_refus(monkeypatch, source_x):
    """Un robots.txt illisible ne vaut jamais autorisation implicite."""
    monkeypatch.setattr(
        collect, "_lecteur_robots", lambda url: (collect.ROBOTS_ILLISIBLE, "illisible")
    )
    monkeypatch.setattr(collect.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        collect,
        "_requete",
        lambda url: pytest.fail("aucune requête ne doit être émise"),
    )

    resultat = collect.tenter_collecte(source_x)
    assert resultat["import_manuel_requis"] is True


def test_metadonnees_extraites_si_voie_autorisee(monkeypatch, source_x):
    """Lorsque la voie est autorisée, les métadonnées publiques sont extraites."""
    monkeypatch.setattr(collect, "_lecteur_robots", lambda url: (collect.ROBOTS_AUTORISE, "ok"))
    monkeypatch.setattr(collect.time, "sleep", lambda _: None)
    html = '<html><meta property="og:title" content="Titre public"><title>T</title></html>'
    monkeypatch.setattr(collect, "_requete", lambda url: (200, html, ""))

    resultat = collect.tenter_collecte(source_x)

    assert resultat["accessible"] is True
    assert resultat["metadonnees_publiques"]["og:title"] == "Titre public"
    # Des métadonnées ne sont pas des interactions : l'import manuel reste requis.
    assert resultat["interactions_recuperees"] == 0
    assert resultat["import_manuel_requis"] is True
    assert "commentaires" in resultat["donnees_manquantes"]


def test_rapport_complet_ecrit(monkeypatch, tmp_path):
    """Le rapport écrit contient une entrée exploitable par source."""
    monkeypatch.setattr(collect, "_lecteur_robots", lambda url: (collect.ROBOTS_INTERDIT, "refus"))
    monkeypatch.setattr(collect, "DELAI_ENTRE_REQUETES", 0)
    monkeypatch.setattr(collect.time, "sleep", lambda _: None)

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
    fichier_rapport = tmp_path / "rapport.json"

    rapport = collect.collecter(fichier_sources, fichier_rapport)

    assert fichier_rapport.exists()
    relu = json.loads(fichier_rapport.read_text(encoding="utf-8"))
    assert len(relu["resultats"]) == 2
    assert relu["donnees_attendues"] == collect.DONNEES_ATTENDUES
    for resultat in rapport["resultats"]:
        assert resultat["interactions_recuperees"] == 0
        assert resultat["import_manuel_requis"] is True
        assert resultat["voies_evaluees"]


def test_rapport_reel_du_projet_documente_chaque_source():
    """Le rapport versionné doit couvrir les 7 sources réelles de l'étude."""
    chemin = collect.FICHIER_RAPPORT
    if not chemin.exists():
        pytest.skip("aucune collecte n'a encore été exécutée")
    rapport = json.loads(chemin.read_text(encoding="utf-8"))
    resultats = rapport["resultats"]
    assert len(resultats) == 7
    for resultat in resultats:
        assert resultat["voies_evaluees"], resultat["source_id"]
        assert isinstance(resultat["donnees_recuperees"], list)
        assert isinstance(resultat["donnees_manquantes"], list)
        assert isinstance(resultat["import_manuel_requis"], bool)
        # Aucune interaction ne peut être déclarée sans avoir été réellement obtenue.
        if resultat["interactions_recuperees"] == 0:
            assert resultat["import_manuel_requis"] is True
