"""Tests de construction du graphe et de détection des communautés."""

from __future__ import annotations

import networkx as nx
import pandas as pd

import community_detection
import load_data
import network_analysis
import preprocess


def _preparer(cadre_brut) -> pd.DataFrame:
    return preprocess.pretraiter(load_data.normaliser(cadre_brut))


def test_graphe_oriente_et_pondere(cadre_minimal):
    graphe = network_analysis.construire_graphe(_preparer(cadre_minimal))
    assert isinstance(graphe, nx.DiGraph)
    assert graphe.number_of_nodes() == 6
    # 5 interactions relationnelles distinctes (les posts ne créent pas de lien)
    assert graphe.number_of_edges() == 5
    assert graphe.has_edge("a2", "a1")
    assert not graphe.has_edge("a1", "a2")


def test_poids_agreges_entre_deux_utilisateurs(cadre_minimal):
    double = pd.concat([cadre_minimal, cadre_minimal.iloc[[1]]], ignore_index=True)
    double.loc[len(double) - 1, "interaction_id"] = "i099"
    graphe = network_analysis.construire_graphe(_preparer(double))
    assert graphe.edges["a2", "a1"]["weight"] == 2


def test_metriques_du_reseau(cadre_minimal):
    graphe = network_analysis.construire_graphe(_preparer(cadre_minimal))
    metriques = network_analysis.calculer_metriques(graphe)
    assert metriques["noeuds"] == 6
    assert metriques["liens"] == 5
    assert 0 < metriques["densite"] <= 1
    assert metriques["taille_composante_principale"] == 6


def test_centralites_par_noeud(cadre_minimal):
    graphe = network_analysis.construire_graphe(_preparer(cadre_minimal))
    centralites = network_analysis.calculer_centralites(graphe)
    assert set(centralites) == set(graphe.nodes())
    for mesures in centralites.values():
        assert 0.0 <= mesures["centralite_degre"] <= 1.0
        assert mesures["centralite_intermediarite"] >= 0.0


def test_graphe_vide_ne_casse_pas():
    graphe = nx.DiGraph()
    metriques = network_analysis.calculer_metriques(graphe)
    assert metriques["noeuds"] == 0 and metriques["liens"] == 0
    assert network_analysis.calculer_centralites(graphe) == {}


def test_detection_de_communautes_sur_deux_groupes():
    # Deux triangles denses reliés par une seule arête : deux communautés nettes.
    graphe = nx.DiGraph()
    for origine, destination in [("a1", "a2"), ("a2", "a3"), ("a3", "a1"),
                                 ("b1", "b2"), ("b2", "b3"), ("b3", "b1"),
                                 ("a1", "b1")]:
        graphe.add_edge(origine, destination, weight=1)
    appartenance, modularite, algorithme = community_detection.detecter_communautes(graphe)
    assert len(set(appartenance.values())) == 2
    assert modularite > 0.2
    assert "Louvain" in algorithme


def test_noms_de_communautes_neutres():
    assert community_detection.nom_communaute(1) == "Communauté 1"
    assert community_detection.nom_communaute(7) == "Communauté 7"


def test_reseau_sans_lien_ne_produit_aucune_communaute():
    graphe = nx.DiGraph()
    graphe.add_nodes_from(["a1", "a2", "a3"])
    appartenance, modularite, algorithme = community_detection.detecter_communautes(graphe)
    assert modularite == 0.0
    assert set(appartenance.values()) == {0}
    assert "sans lien" in algorithme


def test_polarisation_transparente(cadre_minimal):
    graphe = network_analysis.construire_graphe(_preparer(cadre_minimal))
    appartenance, modularite, _ = community_detection.detecter_communautes(graphe)
    polarisation = community_detection.mesurer_polarisation(graphe, appartenance, modularite)
    assert polarisation["interactions_totales"] == (
        polarisation["interactions_intra_communautes"]
        + polarisation["interactions_inter_communautes"]
    )
    assert 0.0 <= polarisation["part_liens_internes"] <= 1.0
    assert polarisation["interpretation"] in {
        "Polarisation faible",
        "Polarisation modérée",
        "Polarisation forte",
    }
    assert "indicatifs" in polarisation["avertissement"]


def test_interpretation_suit_les_seuils():
    assert community_detection.interpreter_polarisation(0.10) == "Polarisation faible"
    assert community_detection.interpreter_polarisation(0.40) == "Polarisation modérée"
    assert community_detection.interpreter_polarisation(0.65) == "Polarisation forte"
