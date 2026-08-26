"""Tests des invariants de provenance et du mode empirique.

Ces tests protègent la validité scientifique des résultats : ils vérifient
qu'aucune donnée synthétique ne peut alimenter un résultat empirique, qu'aucune
interaction ne peut être analysée sans provenance traçable, et que le pipeline
recalcule bien l'ensemble des indicateurs à partir d'un jeu réel.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

import load_data
import provenance as prov
import quality_checks
import run_analysis

COLONNES = load_data.COLONNES_REQUISES + prov.COLONNES_PROVENANCE


def ligne(**valeurs) -> dict:
    base = {colonne: "" for colonne in COLONNES}
    base.update(
        {
            "provenance": prov.MANUAL_VERIFIED,
            "collection_method": "transcription manuelle",
            "collected_at": "2026-08-25T12:00:00",
        }
    )
    base.update(valeurs)
    return base


@pytest.fixture
def corpus_reel() -> pd.DataFrame:
    """Petit corpus de provenance réelle : deux groupes reliés par un pont."""
    lignes = []
    for source, prefixe, auteurs in (
        ("facebook_001", "a", ["ua1", "ua2", "ua3"]),
        ("x_001", "b", ["ub1", "ub2", "ub3"]),
    ):
        publication = f"{prefixe}_post"
        lignes.append(
            ligne(
                platform="facebook" if prefixe == "a" else "x",
                source_id=source,
                post_id=publication,
                interaction_id=publication,
                source_user=auteurs[0],
                interaction_type="post",
                text="Le rapport publié aborde la question de la langue à l'école.",
                timestamp="2026-01-05T10:00:00",
                url="https://exemple.org/" + publication,
            )
        )
        for index, auteur in enumerate(auteurs[1:], start=1):
            lignes.append(
                ligne(
                    platform="facebook" if prefixe == "a" else "x",
                    source_id=source,
                    post_id=publication,
                    interaction_id=f"{prefixe}_c{index}",
                    source_user=auteur,
                    target_user=auteurs[0],
                    interaction_type="comment",
                    text="Je ne suis pas d'accord, ce texte est décevant et injuste.",
                    timestamp=f"2026-01-05T1{index}:00:00",
                    parent_id=publication,
                    url="https://exemple.org/" + publication,
                )
            )
            lignes.append(
                ligne(
                    platform="facebook" if prefixe == "a" else "x",
                    source_id=source,
                    post_id=publication,
                    interaction_id=f"{prefixe}_r{index}",
                    source_user=auteurs[0],
                    target_user=auteur,
                    interaction_type="reply",
                    text="Merci pour ce retour, je soutiens cette réforme utile.",
                    timestamp=f"2026-01-05T1{index}:30:00",
                    parent_id=f"{prefixe}_c{index}",
                    url="https://exemple.org/" + publication,
                )
            )
    # Un pont entre les deux groupes, sans lequel le graphe serait scindé.
    lignes.append(
        ligne(
            platform="x",
            source_id="x_001",
            post_id="b_post",
            interaction_id="pont_1",
            source_user="ua2",
            target_user="ub1",
            interaction_type="mention",
            text="Voir aussi le débat mené par l'autre groupe sur la même question.",
            timestamp="2026-01-05T18:00:00",
            parent_id="b_post",
            url="https://exemple.org/b_post",
        )
    )
    return pd.DataFrame(lignes, columns=COLONNES)


# --------------------------------------------------------------------------
# Invariants de qualité
# --------------------------------------------------------------------------


def test_corpus_reel_passe_tous_les_controles(corpus_reel):
    anomalies = quality_checks.controler(corpus_reel, {"facebook_001", "x_001"})
    assert anomalies == []


def test_provenance_absente_detectee(corpus_reel):
    cadre = corpus_reel.copy()
    cadre.loc[0, "provenance"] = ""
    anomalies = quality_checks.verifier_provenance_renseignee(cadre)
    assert anomalies and "sans provenance" in anomalies[0]


def test_provenance_inconnue_detectee(corpus_reel):
    cadre = corpus_reel.copy()
    cadre.loc[0, "provenance"] = "scraping_sauvage"
    anomalies = quality_checks.verifier_provenance_renseignee(cadre)
    assert anomalies and "inconnue" in anomalies[0]


def test_ligne_synthetique_refusee_dans_jeu_empirique(corpus_reel):
    cadre = corpus_reel.copy()
    cadre.loc[0, "provenance"] = prov.SYNTHETIC_DEMO
    anomalies = quality_checks.verifier_absence_de_synthetique(cadre)
    assert anomalies and prov.SYNTHETIC_DEMO in anomalies[0]


def test_doublon_d_interaction_detecte(corpus_reel):
    cadre = pd.concat([corpus_reel, corpus_reel.iloc[[1]]], ignore_index=True)
    anomalies = quality_checks.verifier_doublons(cadre)
    assert anomalies and "dupliqué" in anomalies[0]


def test_interaction_sans_source_detectee(corpus_reel):
    cadre = corpus_reel.copy()
    cadre.loc[0, "source_id"] = ""
    anomalies = quality_checks.verifier_sources(cadre, {"facebook_001", "x_001"})
    assert anomalies and "sans source_id" in anomalies[0]


def test_source_non_declaree_detectee(corpus_reel):
    anomalies = quality_checks.verifier_sources(corpus_reel, {"facebook_001"})
    assert anomalies and "x_001" in anomalies[0]


def test_filiation_orpheline_detectee(corpus_reel):
    cadre = corpus_reel.copy()
    cadre.loc[1, "parent_id"] = "inexistant_42"
    anomalies = quality_checks.verifier_filiation(cadre)
    assert anomalies and "inexistant_42" in anomalies[0]


# --------------------------------------------------------------------------
# Mode empirique du pipeline
# --------------------------------------------------------------------------


def _ecrire(cadre: pd.DataFrame, chemin) -> None:
    cadre.to_csv(chemin, index=False, encoding="utf-8")


def test_jeu_vide_refuse(tmp_path):
    chemin = tmp_path / "vide.csv"
    pd.DataFrame(columns=COLONNES).to_csv(chemin, index=False)
    with pytest.raises(load_data.ErreurDonnees) as erreur:
        load_data.charger_fichier_empirique(chemin)
    assert "aucune interaction" in str(erreur.value).lower()


def test_colonnes_de_tracabilite_obligatoires(tmp_path, corpus_reel):
    chemin = tmp_path / "sans_provenance.csv"
    corpus_reel.drop(columns=prov.COLONNES_PROVENANCE).to_csv(chemin, index=False)
    with pytest.raises(load_data.ErreurDonnees) as erreur:
        load_data.charger_fichier_empirique(chemin)
    assert "traçabilité" in str(erreur.value)


def test_synthetique_refuse_en_mode_empirique(tmp_path, corpus_reel):
    cadre = corpus_reel.copy()
    cadre.loc[0, "provenance"] = prov.SYNTHETIC_DEMO
    chemin = tmp_path / "melange.csv"
    _ecrire(cadre, chemin)
    with pytest.raises(load_data.ErreurDonnees) as erreur:
        load_data.charger_fichier_empirique(chemin)
    assert prov.SYNTHETIC_DEMO in str(erreur.value)


def test_chargement_empirique_conserve_la_provenance(tmp_path, corpus_reel):
    chemin = tmp_path / "reel.csv"
    _ecrire(corpus_reel, chemin)
    cadre, meta = load_data.charger_fichier_empirique(chemin)
    assert meta["synthetique"] is False
    assert meta["mode"] == "empirique"
    assert meta["provenances"] == {prov.MANUAL_VERIFIED: len(corpus_reel)}
    assert set(cadre["provenance"]) == {prov.MANUAL_VERIFIED}


def test_pipeline_complet_sur_corpus_reel(tmp_path, corpus_reel):
    """Bout en bout : le pipeline recalcule tout à partir d'un jeu réel."""
    entree = tmp_path / "real_interactions.csv"
    _ecrire(corpus_reel, entree)
    sortie = tmp_path / "sortie"

    resume = run_analysis.executer(sortie, entree)

    assert resume["interactions"] == len(corpus_reel)
    assert resume["jeu_de_donnees"]["synthetique"] is False

    overview = json.loads((sortie / "overview.json").read_text(encoding="utf-8"))
    jeu = overview["jeu_de_donnees"]
    assert jeu["type"] == "reel"
    assert jeu["mode"] == "empirique"
    assert jeu["avertissement"] == ""
    assert jeu["provenances"] == {prov.MANUAL_VERIFIED: len(corpus_reel)}

    kpi = overview["kpi"]
    assert kpi["interactions"] == len(corpus_reel)
    assert kpi["publications"] == 2
    assert kpi["utilisateurs"] == 6
    # Deux sources réelles portent des interactions : elles sont comptées comme telles,
    # et ne figurent plus parmi les sources en attente d'import.
    assert kpi["sources_avec_donnees_reelles"] == 2
    assert kpi["sources_import_manuel_requis"] == 5
    assert (
        kpi["sources_avec_donnees_reelles"] + kpi["sources_import_manuel_requis"]
        == kpi["sources_declarees"]
    )

    # Le graphe, les communautés et la propagation sont bien recalculés.
    assert overview["reseau"]["noeuds"] > 0
    assert overview["reseau"]["liens"] > 0
    assert kpi["communautes"] >= 1
    propagation = json.loads((sortie / "propagation.json").read_text(encoding="utf-8"))
    assert propagation["nombre_cascades"] >= 1

    # Aucune trace de corpus synthétique dans les résultats empiriques.
    for nom in ("overview.json", "sources.json", "communities.json", "content.json"):
        contenu = (sortie / nom).read_text(encoding="utf-8")
        assert prov.SYNTHETIC_DEMO not in contenu
        assert "sample_interactions.csv" not in contenu


def test_statuts_de_sources_en_mode_empirique(tmp_path, corpus_reel):
    """Seules les sources réellement pourvues sont déclarées « Données disponibles »."""
    entree = tmp_path / "real_interactions.csv"
    _ecrire(corpus_reel, entree)
    sortie = tmp_path / "sortie"
    run_analysis.executer(sortie, entree)

    sources = json.loads((sortie / "sources.json").read_text(encoding="utf-8"))["sources"]
    pourvues = {s["source_id"] for s in sources if s["interactions"] > 0}
    assert pourvues == {"facebook_001", "x_001"}
    for source in sources:
        if source["source_id"] in pourvues:
            assert source["statut"] == "Données disponibles"
        else:
            assert source["statut"] != "Données disponibles"
