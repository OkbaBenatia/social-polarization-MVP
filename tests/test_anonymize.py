"""Tests de pseudonymisation."""

from __future__ import annotations

import json

import anonymize
import load_data


def test_identifiants_bruts_absents_apres_anonymisation(cadre_minimal, tmp_path):
    cadre = load_data.normaliser(cadre_minimal)
    anonymise, etiquettes = anonymize.anonymiser(cadre, tmp_path)

    identifiants_bruts = {"a1", "a2", "a3", "b1", "b2", "b3"}
    valeurs = set(anonymise["source_user"]) | set(anonymise["target_user"])
    assert not (identifiants_bruts & valeurs)
    assert all(valeur.startswith("usr_") for valeur in valeurs if valeur)


def test_etiquettes_neutres_et_numerotees(cadre_minimal, tmp_path):
    cadre = load_data.normaliser(cadre_minimal)
    _, etiquettes = anonymize.anonymiser(cadre, tmp_path)
    assert len(etiquettes) == 6
    assert sorted(etiquettes.values()) == [f"Utilisateur {i:03d}" for i in range(1, 7)]


def test_pseudonymisation_stable_pour_un_meme_sel(cadre_minimal, tmp_path):
    cadre = load_data.normaliser(cadre_minimal)
    premier, _ = anonymize.anonymiser(cadre, tmp_path)
    second, _ = anonymize.anonymiser(cadre, tmp_path)
    assert premier["source_user"].tolist() == second["source_user"].tolist()


def test_sels_differents_produisent_des_pseudonymes_differents(tmp_path):
    assert anonymize.pseudonymiser_identifiant("a1", "sel-1") != anonymize.pseudonymiser_identifiant(
        "a1", "sel-2"
    )


def test_table_de_correspondance_reste_locale(cadre_minimal, tmp_path):
    cadre = load_data.normaliser(cadre_minimal)
    anonymize.anonymiser(cadre, tmp_path)
    table = tmp_path / anonymize.NOM_FICHIER_TABLE
    assert table.exists()
    contenu = json.loads(table.read_text(encoding="utf-8"))
    assert "ne jamais publier" in contenu["avertissement"]
    assert "a1" in contenu["correspondance"]
