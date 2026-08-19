"""Tests de chargement des sources et de détermination des statuts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import load_sources

RACINE = Path(__file__).resolve().parent.parent


def test_sources_reelles_du_projet_chargees():
    sources = load_sources.charger_sources(RACINE / "data" / "sources.json")
    assert len(sources) == 7
    plateformes = [source["platform"] for source in sources]
    assert plateformes.count("facebook") == 5
    assert plateformes.count("x") == 1
    assert plateformes.count("instagram") == 1
    assert all(source["plateforme_connue"] for source in sources)
    assert all(source["url"].startswith("https://") for source in sources)


def test_fichier_absent_message_explicite(tmp_path):
    with pytest.raises(load_sources.ErreurSources) as erreur:
        load_sources.charger_sources(tmp_path / "absent.json")
    assert "introuvable" in str(erreur.value)


def test_json_invalide_message_explicite(tmp_path):
    chemin = tmp_path / "sources.json"
    chemin.write_text("{ pas du json", encoding="utf-8")
    with pytest.raises(load_sources.ErreurSources) as erreur:
        load_sources.charger_sources(chemin)
    assert "JSON invalide" in str(erreur.value)


def test_champ_obligatoire_manquant(tmp_path):
    chemin = tmp_path / "sources.json"
    chemin.write_text(
        json.dumps({"sources": [{"source_id": "a", "platform": "x"}]}), encoding="utf-8"
    )
    with pytest.raises(load_sources.ErreurSources) as erreur:
        load_sources.charger_sources(chemin)
    assert "url" in str(erreur.value)


def test_identifiant_duplique_refuse(tmp_path):
    chemin = tmp_path / "sources.json"
    chemin.write_text(
        json.dumps(
            {
                "sources": [
                    {"source_id": "a", "platform": "x", "url": "https://exemple.org/1"},
                    {"source_id": "a", "platform": "x", "url": "https://exemple.org/2"},
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(load_sources.ErreurSources) as erreur:
        load_sources.charger_sources(chemin)
    assert "dupliqué" in str(erreur.value)


def test_statut_demonstration_pour_donnees_synthetiques():
    statut, methode = load_sources.statut_source({}, None, 10, jeu_synthetique=True)
    assert statut == load_sources.STATUT_DEMONSTRATION
    assert "synthétique" in methode


def test_statut_disponible_uniquement_si_donnees_importees():
    statut, _ = load_sources.statut_source({}, None, 10, jeu_synthetique=False)
    assert statut == load_sources.STATUT_DISPONIBLE


def test_statut_import_manuel_sans_donnees():
    statut, _ = load_sources.statut_source({}, {"accessible": False}, 0, jeu_synthetique=False)
    assert statut == load_sources.STATUT_IMPORT_MANUEL


def test_statut_partiel_si_metadonnees_seules():
    statut, methode = load_sources.statut_source(
        {}, {"accessible": True}, 0, jeu_synthetique=False
    )
    assert statut == load_sources.STATUT_PARTIEL
    assert "aucune interaction" in methode.lower()


def test_rapport_de_collecte_absent_est_tolere(tmp_path):
    assert load_sources.charger_rapport_collecte(tmp_path / "absent.json") == {}


def test_rapport_de_collecte_du_projet_est_lisible():
    rapport = load_sources.charger_rapport_collecte(RACINE / "data" / "collection_report.json")
    if rapport:  # le rapport n'existe que si la collecte a été tentée
        for resultat in rapport.values():
            assert "limites" in resultat
            assert isinstance(resultat["interactions_recuperees"], int)
