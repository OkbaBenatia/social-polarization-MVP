"""Tests de bout en bout : exécution du pipeline et génération des JSON."""

from __future__ import annotations

import json

import pytest

import load_sources
import run_analysis

FICHIERS_ATTENDUS = [
    "overview.json",
    "sources.json",
    "network.json",
    "communities.json",
    "content.json",
    "sentiment.json",
    "emotions.json",
    "hate_speech.json",
    "propagation.json",
]


@pytest.fixture(scope="module")
def sortie(tmp_path_factory):
    repertoire = tmp_path_factory.mktemp("public_data")
    resume = run_analysis.executer(repertoire)
    donnees = {
        nom: json.loads((repertoire / nom).read_text(encoding="utf-8"))
        for nom in FICHIERS_ATTENDUS
    }
    return repertoire, resume, donnees


def test_tous_les_json_sont_generes(sortie):
    repertoire, _, _ = sortie
    for nom in FICHIERS_ATTENDUS:
        chemin = repertoire / nom
        assert chemin.exists(), f"{nom} manquant"
        assert chemin.stat().st_size > 0


def test_attribution_presente_dans_chaque_json(sortie):
    _, _, donnees = sortie
    for nom, contenu in donnees.items():
        assert contenu["attribution"] == "Préparation, conception et programmation : Dr. Okba Ben Atia"
        assert contenu["auteur"] == "Dr. Okba Ben Atia"


def test_jeu_synthetique_toujours_identifie(sortie):
    _, resume, donnees = sortie
    for contenu in donnees.values():
        jeu = contenu["jeu_de_donnees"]
        assert jeu["type"] in {"synthetique", "reel"}
        if jeu["synthetique"]:
            assert "synthétiques" in jeu["avertissement"]
        else:
            assert jeu["avertissement"] == ""


def test_coherence_des_kpi(sortie):
    _, resume, donnees = sortie
    kpi = donnees["overview.json"]["kpi"]
    assert kpi["interactions"] == resume["interactions"]
    assert kpi["utilisateurs"] == resume["utilisateurs"]
    assert kpi["communautes"] == resume["communautes"] == donnees["communities.json"]["nombre_communautes"]
    assert kpi["modularite"] == donnees["communities.json"]["modularite"]


def test_reseau_calcule_et_borne(sortie):
    _, _, donnees = sortie
    reseau = donnees["network.json"]
    assert reseau["metriques"]["noeuds"] > 0
    assert reseau["metriques"]["liens"] > 0
    assert len(reseau["noeuds"]) <= run_analysis.MAX_NETWORK_NODES
    assert len(reseau["noeuds"]) == reseau["noeuds_affiches"]
    identifiants = {noeud["id"] for noeud in reseau["noeuds"]}
    for lien in reseau["liens"]:
        assert lien["source"] in identifiants and lien["cible"] in identifiants
        assert lien["poids"] >= 1


def test_aucun_identifiant_brut_dans_les_json(sortie):
    repertoire, _, _ = sortie
    bruts = {f"u{index:03d}" for index in range(1, 200)}
    for nom in FICHIERS_ATTENDUS:
        texte = (repertoire / nom).read_text(encoding="utf-8")
        for brut in bruts:
            assert f'"{brut}"' not in texte, f"identifiant brut {brut} exposé dans {nom}"


def test_etiquettes_utilisateurs_neutres(sortie):
    _, _, donnees = sortie
    for noeud in donnees["network.json"]["noeuds"]:
        assert noeud["label"].startswith("Utilisateur ")
        assert noeud["id"].startswith("usr_")


def test_communautes_nommees_neutralement(sortie):
    _, _, donnees = sortie
    interdits = ["pro-", "anti-", "extrémiste", "haineux", "islam", "immigration"]
    for communaute in donnees["communities.json"]["communautes"]:
        assert communaute["nom"].startswith("Communauté ")
        minuscule = communaute["nom"].lower()
        assert not any(mot in minuscule for mot in interdits)


def test_polarisation_transparente_et_documentee(sortie):
    _, _, donnees = sortie
    polarisation = donnees["communities.json"]["polarisation"]
    assert polarisation["interactions_totales"] == (
        polarisation["interactions_intra_communautes"]
        + polarisation["interactions_inter_communautes"]
    )
    assert polarisation["seuils_indicatifs"]
    assert "indicatifs" in polarisation["avertissement"]


def test_statuts_de_sources_coherents(sortie):
    _, _, donnees = sortie
    sources = donnees["sources.json"]["sources"]
    assert len(sources) == 7
    urls = {source["url"] for source in sources}
    assert "https://x.com/i/status/2087872720012796385" in urls
    assert any("instagram.com/reel/DbtVlHYABVK" in url for url in urls)
    assert sum(1 for source in sources if source["plateforme"] == "facebook") == 5
    for source in sources:
        assert source["statut"] in donnees["sources.json"]["statuts_possibles"]
        if source["statut"] == load_sources.STATUT_DISPONIBLE:
            assert source["interactions"] > 0


def test_sentiment_emotions_haine_separes(sortie):
    _, _, donnees = sortie
    assert donnees["sentiment.json"]["categories"] == ["Positif", "Neutre", "Négatif"]
    assert donnees["emotions.json"]["categories"] == [
        "Colère",
        "Soutien / approbation",
        "Autre / neutre",
    ]
    assert donnees["hate_speech.json"]["categories"] == [
        "Non haineux",
        "Toxique / offensant",
        "Potentiellement haineux",
    ]
    for nom in ("sentiment.json", "emotions.json", "hate_speech.json"):
        assert donnees[nom]["methode"]["performance_evaluee"] is False


def test_repartitions_somment_au_nombre_de_messages(sortie):
    _, _, donnees = sortie
    for nom in ("sentiment.json", "emotions.json", "hate_speech.json"):
        contenu = donnees[nom]
        total = sum(element["nombre"] for element in contenu["global"])
        assert total == contenu["messages_analyses"]


def test_propagation_reconstruite(sortie):
    _, _, donnees = sortie
    propagation = donnees["propagation.json"]
    assert propagation["nombre_cascades"] > 0
    for cascade in propagation["cascades"]:
        assert cascade["taille"] >= 1
        assert cascade["profondeur"] >= 0
        assert 0.0 <= cascade["taux_potentiellement_haineux"] <= 1.0
        assert cascade["auteur_racine"].startswith("Utilisateur ") or cascade["auteur_racine"] == ""


def test_contenu_expose_les_filtres_attendus(sortie):
    _, _, donnees = sortie
    contenu = donnees["content.json"]
    assert contenu["communautes"][0]["id"] == "toutes"
    assert contenu["plateformes"][0]["id"] == "toutes"
    for communaute in contenu["communautes"]:
        for plateforme in contenu["plateformes"]:
            assert f"{communaute['id']}|{plateforme['id']}" in contenu["profils"]
