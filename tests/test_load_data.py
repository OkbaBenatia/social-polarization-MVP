"""Tests de chargement et de validation du jeu de données."""

from __future__ import annotations

import pandas as pd
import pytest

import load_data
from conftest import COLONNES


def test_csv_valide_est_normalise(cadre_minimal):
    cadre = load_data.normaliser(cadre_minimal)
    assert len(cadre) == 7
    assert set(load_data.COLONNES_REQUISES).issubset(cadre.columns)
    assert cadre["horodatage"].notna().all()
    assert cadre.attrs["doublons_supprimes"] == 0


def test_colonnes_manquantes_leve_une_erreur(cadre_minimal):
    incomplet = cadre_minimal.drop(columns=["target_user", "timestamp"])
    with pytest.raises(load_data.ErreurDonnees) as erreur:
        load_data.valider_colonnes(incomplet, "test.csv")
    message = str(erreur.value)
    assert "colonnes manquantes" in message
    assert "target_user" in message and "timestamp" in message


def test_dataset_vide_leve_une_erreur():
    vide = pd.DataFrame(columns=COLONNES)
    with pytest.raises(load_data.ErreurDonnees) as erreur:
        load_data.normaliser(vide, "vide.csv")
    assert "vide" in str(erreur.value)


def test_lignes_sans_identifiant_sont_ignorees(cadre_minimal):
    degrade = pd.concat(
        [cadre_minimal, pd.DataFrame([{colonne: "" for colonne in COLONNES}])],
        ignore_index=True,
    )
    cadre = load_data.normaliser(degrade)
    assert len(cadre) == 7
    assert cadre.attrs["lignes_ignorees"] == 1


def test_doublons_interaction_id_supprimes(cadre_minimal):
    doublon = pd.concat([cadre_minimal, cadre_minimal.iloc[[1]]], ignore_index=True)
    cadre = load_data.normaliser(doublon)
    assert cadre.attrs["doublons_supprimes"] == 1
    assert cadre["interaction_id"].is_unique


def test_horodatage_invalide_est_signale(cadre_minimal):
    cadre_minimal.loc[0, "timestamp"] = "pas-une-date"
    cadre = load_data.normaliser(cadre_minimal)
    assert cadre.attrs["horodatages_invalides"] == 1


def test_type_interaction_inconnu_est_signale(cadre_minimal):
    cadre_minimal.loc[1, "interaction_type"] = "like"
    cadre = load_data.normaliser(cadre_minimal)
    assert "like" in cadre.attrs["types_inconnus"]
    assert not cadre.loc[1, "type_reconnu"]


def test_csv_reel_prioritaire_sur_demonstration(tmp_path, cadre_minimal):
    reel = tmp_path / "import.csv"
    cadre_minimal.to_csv(reel, index=False)
    demo = tmp_path / "demo.csv"
    cadre_minimal.head(3).to_csv(demo, index=False)

    cadre, meta = load_data.charger_jeu_de_donnees([reel], demo)
    assert meta["type"] == "reel"
    assert meta["synthetique"] is False
    assert meta["avertissement"] == ""
    assert len(cadre) == 7


def test_repli_sur_le_jeu_de_demonstration(tmp_path, cadre_minimal):
    demo = tmp_path / "demo.csv"
    cadre_minimal.to_csv(demo, index=False)
    cadre, meta = load_data.charger_jeu_de_donnees([tmp_path / "absent.csv"], demo)
    assert meta["synthetique"] is True
    assert "synthétiques" in meta["avertissement"]
    assert len(cadre) == 7


def test_aucun_jeu_de_donnees_message_explicite(tmp_path):
    with pytest.raises(load_data.ErreurDonnees) as erreur:
        load_data.charger_jeu_de_donnees([], tmp_path / "absent.csv")
    assert "Aucun jeu de données" in str(erreur.value)


def test_import_json_equivalent_au_csv(tmp_path, cadre_minimal):
    chemin = tmp_path / "import.json"
    cadre_minimal.to_json(chemin, orient="records", force_ascii=False)
    cadre, meta = load_data.charger_jeu_de_donnees([chemin], None)
    assert len(cadre) == 7
    assert meta["type"] == "reel"


def test_csv_invalide_message_francais(tmp_path):
    chemin = tmp_path / "casse.csv"
    chemin.write_text("colonne_a,colonne_b\n1,2\n", encoding="utf-8")
    with pytest.raises(load_data.ErreurDonnees) as erreur:
        load_data.charger_jeu_de_donnees([chemin], None)
    assert "colonnes manquantes" in str(erreur.value)
