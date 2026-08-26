"""Pipeline complet d'analyse — point d'entrée unique du projet.

    python analysis/run_analysis.py

Étapes exécutées :

1. chargement des sources et du rapport de collecte ;
2. chargement et validation du jeu de données ;
3. pseudonymisation des utilisateurs ;
4. prétraitement du texte ;
5. construction du réseau ;
6. détection des communautés ;
7. mesure de la polarisation ;
8. analyse lexicale ;
9. analyse de sentiment ;
10. classification colère / soutien ;
11. estimation toxicité / discours potentiellement haineux ;
12. analyse de propagation ;
13. génération des fichiers JSON consommés par le tableau de bord.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import anonymize  # noqa: E402
import community_detection  # noqa: E402
import emotion_analysis  # noqa: E402
import hate_speech_analysis  # noqa: E402
import load_data  # noqa: E402
import load_sources  # noqa: E402
import network_analysis  # noqa: E402
import preprocess  # noqa: E402
import propagation_analysis  # noqa: E402
import quality_checks  # noqa: E402
import sentiment_analysis  # noqa: E402
import text_analysis  # noqa: E402

TITRE = "Étude de la polarisation et de la propagation du discours de haine sur les réseaux sociaux"
SOUS_TITRE = "Analyse de réseaux, détection de communautés et analyse automatique du contenu"
AUTEUR = "Dr. Okba Ben Atia"
ATTRIBUTION = f"Préparation, conception et programmation : {AUTEUR}"

# Limite de nœuds exportés vers le tableau de bord (fluidité du navigateur).
MAX_NETWORK_NODES = 1000
# Nombre d'extraits de contenu publiés (jeux synthétiques uniquement).
NOMBRE_EXTRAITS = 8

REPERTOIRE_DONNEES = RACINE / "data"
REPERTOIRE_IMPORTS = REPERTOIRE_DONNEES / "imported"
REPERTOIRE_PRIVE = REPERTOIRE_DONNEES / "private"
FICHIER_SOURCES = REPERTOIRE_DONNEES / "sources.json"
FICHIER_RAPPORT_COLLECTE = REPERTOIRE_DONNEES / "collection_report.json"
FICHIER_DEMONSTRATION = REPERTOIRE_DONNEES / "sample_interactions.csv"
REPERTOIRE_SORTIE = RACINE / "public" / "data"


class ErreurPipeline(Exception):
    """Erreur bloquante du pipeline, formulée pour l'utilisateur."""


def _chemin_affichable(chemin: Path) -> str:
    """Chemin relatif à la racine du projet lorsque c'est possible."""
    try:
        return str(chemin.relative_to(RACINE))
    except ValueError:
        return str(chemin)


def _ecrire_json(repertoire: Path, nom: str, contenu: dict) -> Path:
    repertoire.mkdir(parents=True, exist_ok=True)
    chemin = repertoire / nom
    chemin.write_text(
        json.dumps(contenu, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    return chemin


def _repartition(valeurs: pd.Series, categories: list[str]) -> list[dict]:
    total = int(len(valeurs))
    comptes = valeurs.value_counts().to_dict()
    return [
        {
            "categorie": categorie,
            "nombre": int(comptes.get(categorie, 0)),
            "part": round(int(comptes.get(categorie, 0)) / total, 4) if total else 0.0,
        }
        for categorie in categories
    ]


def _fichiers_importes() -> list[Path]:
    if not REPERTOIRE_IMPORTS.exists():
        return []
    return sorted(
        chemin
        for chemin in REPERTOIRE_IMPORTS.iterdir()
        if chemin.suffix.lower() in {".csv", ".json"} and not chemin.name.startswith(".")
    )


def executer(
    repertoire_sortie: Path = REPERTOIRE_SORTIE, entree: Path | None = None
) -> dict:
    """Exécute le pipeline complet et écrit les fichiers JSON. Retourne un résumé.

    ``entree`` désigne un jeu de données empirique explicite (option ``--input``).
    Dans ce mode, chaque interaction doit déclarer une provenance réelle ; le
    corpus de démonstration n'est jamais utilisé en repli.
    """
    horodatage = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # --- 1. Sources -------------------------------------------------------
    print("1/13  Chargement des sources…")
    sources = load_sources.charger_sources(FICHIER_SOURCES)
    rapport_collecte = load_sources.charger_rapport_collecte(FICHIER_RAPPORT_COLLECTE)
    print(f"       {len(sources)} sources déclarées, "
          f"{len(rapport_collecte)} tentatives de collecte enregistrées.")

    # --- 2. Jeu de données ------------------------------------------------
    print("2/13  Chargement et validation du jeu de données…")
    if entree is not None:
        print(f"       mode empirique — jeu de données imposé : {_chemin_affichable(entree)}")
        cadre, meta_donnees = load_data.charger_fichier_empirique(entree)
        quality_checks.controler_ou_echouer(
            cadre, {source["source_id"] for source in sources}
        )
        print(f"       contrôles de provenance : {len(cadre)} interactions validées "
              f"({', '.join(f'{k} : {v}' for k, v in meta_donnees['provenances'].items())})")
    else:
        cadre, meta_donnees = load_data.charger_jeu_de_donnees(
            _fichiers_importes(), FICHIER_DEMONSTRATION
        )
    print(f"       {len(cadre)} interactions ({meta_donnees['type']}) — "
          f"fichiers : {', '.join(meta_donnees['fichiers'])}")
    if meta_donnees["types_inconnus"]:
        print(f"       Attention : types d'interaction non reconnus : "
              f"{', '.join(meta_donnees['types_inconnus'])}")

    # --- 3. Anonymisation --------------------------------------------------
    print("3/13  Pseudonymisation des utilisateurs…")
    cadre, etiquettes = anonymize.anonymiser(cadre, REPERTOIRE_PRIVE)
    cadre["auteur_etiquette"] = cadre["source_user"].map(lambda u: etiquettes.get(u, ""))
    print(f"       {len(etiquettes)} utilisateurs pseudonymisés.")

    # --- 4. Prétraitement ---------------------------------------------------
    print("4/13  Prétraitement du texte…")
    cadre = preprocess.pretraiter(cadre)
    messages_avec_texte = int(cadre["a_du_texte"].sum())
    print(f"       {messages_avec_texte} messages contiennent du texte exploitable.")

    # --- 5. Réseau -----------------------------------------------------------
    print("5/13  Construction du réseau…")
    graphe = network_analysis.construire_graphe(cadre)
    metriques_reseau = network_analysis.calculer_metriques(graphe)
    centralites = network_analysis.calculer_centralites(graphe)
    print(f"       {metriques_reseau['noeuds']} nœuds, {metriques_reseau['liens']} liens, "
          f"densité {metriques_reseau['densite']}.")

    # --- 6. Communautés -------------------------------------------------------
    print("6/13  Détection des communautés…")
    appartenance, modularite, algorithme = community_detection.detecter_communautes(graphe)
    identifiants_communautes = sorted(set(appartenance.values())) if appartenance else []
    identifiants_communautes = [i for i in identifiants_communautes if i > 0]
    noms_communautes = {
        identifiant: community_detection.nom_communaute(identifiant)
        for identifiant in identifiants_communautes
    }
    cadre["communaute_id"] = cadre["source_user"].map(lambda u: appartenance.get(u, 0))
    cadre["communaute"] = cadre["communaute_id"].map(
        lambda identifiant: noms_communautes.get(identifiant, "Non affecté")
    )
    print(f"       {len(noms_communautes)} communautés détectées "
          f"({algorithme}), modularité {modularite:.4f}.")

    # --- 7. Polarisation ---------------------------------------------------------
    print("7/13  Mesure de la polarisation…")
    polarisation = community_detection.mesurer_polarisation(graphe, appartenance, modularite)
    compteurs_communautes = community_detection.compter_liens_internes_externes(
        graphe, appartenance
    )
    matrice = community_detection.matrice_interactions(graphe, appartenance)
    print(f"       modularité {polarisation['modularite']} — "
          f"{polarisation['interpretation'].lower()} (interprétation indicative).")

    # --- 8-11. Contenu ------------------------------------------------------------
    print("8/13  Analyse de sentiment…")
    cadre = sentiment_analysis.analyser_sentiment(cadre)
    print("9/13  Classification colère / soutien…")
    cadre = emotion_analysis.analyser_emotions(cadre)
    print("10/13 Estimation toxicité / discours potentiellement haineux…")
    cadre = hate_speech_analysis.analyser_discours_haineux(cadre)
    print("11/13 Analyse lexicale…")
    plateformes = sorted(set(cadre["platform"]) - {""})
    contenu = text_analysis.analyser_contenu(cadre, noms_communautes, plateformes)

    # --- 12. Propagation -------------------------------------------------------------
    print("12/13 Analyse de la propagation…")
    propagation = propagation_analysis.construire_cascades(cadre, noms_communautes)
    print(f"       {propagation['nombre_cascades']} cascades reconstruites.")

    # --- 13. Génération des JSON -------------------------------------------------------
    print("13/13 Génération des fichiers JSON…")
    fichiers = _generer_json(
        repertoire_sortie=repertoire_sortie,
        horodatage=horodatage,
        cadre=cadre,
        meta_donnees=meta_donnees,
        sources=sources,
        rapport_collecte=rapport_collecte,
        graphe=graphe,
        metriques_reseau=metriques_reseau,
        centralites=centralites,
        appartenance=appartenance,
        noms_communautes=noms_communautes,
        algorithme=algorithme,
        polarisation=polarisation,
        compteurs_communautes=compteurs_communautes,
        matrice=matrice,
        contenu=contenu,
        propagation=propagation,
        etiquettes=etiquettes,
    )

    return {
        "fichiers": fichiers,
        "interactions": int(len(cadre)),
        "utilisateurs": len(etiquettes),
        "communautes": len(noms_communautes),
        "modularite": polarisation["modularite"],
        "jeu_de_donnees": meta_donnees,
    }


def _generer_json(**contexte) -> list[str]:
    repertoire = contexte["repertoire_sortie"]
    cadre: pd.DataFrame = contexte["cadre"]
    meta_donnees = contexte["meta_donnees"]
    noms_communautes: dict[int, str] = contexte["noms_communautes"]
    horodatage = contexte["horodatage"]
    polarisation = contexte["polarisation"]

    entete = {
        "genere_le": horodatage,
        "titre": TITRE,
        "sous_titre": SOUS_TITRE,
        "auteur": AUTEUR,
        "attribution": ATTRIBUTION,
        "jeu_de_donnees": {
            "type": meta_donnees["type"],
            "synthetique": meta_donnees["synthetique"],
            "fichiers": meta_donnees["fichiers"],
            "avertissement": meta_donnees["avertissement"],
            "mode": meta_donnees.get("mode", "demonstration"),
            "provenances": meta_donnees.get("provenances", {}),
        },
    }

    publications = cadre[cadre["interaction_type"] == "post"]
    compte_interactions = Counter(cadre["source_id"])
    compte_publications = Counter(publications["source_id"])

    # ---------------- sources.json ----------------
    etat_sources = load_sources.construire_etat_sources(
        contexte["sources"],
        contexte["rapport_collecte"],
        compte_interactions,
        compte_publications,
        meta_donnees["synthetique"],
    )
    sources_json = {
        **entete,
        "sources": etat_sources,
        "statuts_possibles": [
            load_sources.STATUT_DISPONIBLE,
            load_sources.STATUT_PARTIEL,
            load_sources.STATUT_IMPORT_MANUEL,
            load_sources.STATUT_DEMONSTRATION,
        ],
        "regles_collecte": [
            "Aucune authentification, aucun cookie personnel, aucune session privée.",
            "Aucun contournement de CAPTCHA, de protection anti-bot ou de limitation d'API.",
            "Respect du fichier robots.txt de chaque plateforme.",
            "Aucune donnée privée n'est recherchée ni conservée.",
        ],
    }

    # ---------------- network.json ----------------
    graphe = contexte["graphe"]
    centralites: dict = contexte["centralites"]
    appartenance: dict = contexte["appartenance"]
    etiquettes: dict = contexte["etiquettes"]

    noeuds_ordonnes = sorted(
        graphe.nodes(),
        key=lambda noeud: (
            -centralites.get(noeud, {}).get("degre", 0),
            etiquettes.get(noeud, noeud),
        ),
    )
    noeuds_retenus = noeuds_ordonnes[:MAX_NETWORK_NODES]
    ensemble_retenu = set(noeuds_retenus)

    messages_par_utilisateur = Counter(cadre["source_user"])
    noeuds_json = []
    for noeud in noeuds_retenus:
        mesures = centralites.get(noeud, {})
        identifiant_communaute = appartenance.get(noeud, 0)
        donnees_noeud = graphe.nodes[noeud]
        noeuds_json.append(
            {
                "id": noeud,
                "label": etiquettes.get(noeud, "Utilisateur"),
                "communaute_id": identifiant_communaute,
                "communaute": noms_communautes.get(identifiant_communaute, "Non affecté"),
                "messages": int(messages_par_utilisateur.get(noeud, 0)),
                "plateformes": sorted(donnees_noeud.get("plateformes", set())),
                "sources": sorted(donnees_noeud.get("sources", set())),
                **mesures,
            }
        )

    liens_json = [
        {
            "source": origine,
            "cible": destination,
            "poids": int(donnees.get("weight", 1)),
            "types": sorted(donnees.get("types", {})),
            "type_principal": max(
                donnees.get("types", {"reply": 1}).items(), key=lambda item: item[1]
            )[0],
            "plateformes": sorted(donnees.get("plateformes", set())),
            "sources": sorted(donnees.get("sources", set())),
            "inter_communautaire": appartenance.get(origine) != appartenance.get(destination),
        }
        for origine, destination, donnees in graphe.edges(data=True)
        if origine in ensemble_retenu and destination in ensemble_retenu
    ]

    network_json = {
        **entete,
        "metriques": contexte["metriques_reseau"],
        "limite_noeuds": MAX_NETWORK_NODES,
        "noeuds_total": graphe.number_of_nodes(),
        "liens_total": graphe.number_of_edges(),
        "noeuds_affiches": len(noeuds_json),
        "liens_affiches": len(liens_json),
        "tronque": graphe.number_of_nodes() > len(noeuds_json),
        "noeuds": noeuds_json,
        "liens": liens_json,
        "communautes": [
            {"id": identifiant, "nom": nom} for identifiant, nom in sorted(noms_communautes.items())
        ],
        "plateformes": sorted(set(cadre["platform"]) - {""}),
        "sources_disponibles": sorted(set(cadre["source_id"]) - {""}),
        "types_interaction": sorted(
            set(cadre["interaction_type"]) & load_data.TYPES_RELATIONNELS
        ),
        "message": ""
        if graphe.number_of_edges()
        else "Aucun lien d'interaction n'a pu être construit à partir des données fournies.",
    }

    # ---------------- communities.json ----------------
    compteurs = contexte["compteurs_communautes"]
    communautes_json = []
    for identifiant, nom in sorted(noms_communautes.items()):
        membres = [noeud for noeud, groupe in appartenance.items() if groupe == identifiant]
        sous_ensemble = cadre[cadre["communaute_id"] == identifiant]
        avec_texte = sous_ensemble[sous_ensemble["a_du_texte"]]
        profil = text_analysis.profil_lexical(sous_ensemble, taille=10)
        compteur = compteurs.get(identifiant, {})
        internes = compteur.get("interactions_internes", 0)
        externes = compteur.get("interactions_externes", 0)
        communautes_json.append(
            {
                "id": identifiant,
                "nom": nom,
                "utilisateurs": len(membres),
                "messages": int(len(sous_ensemble)),
                "messages_avec_texte": int(len(avec_texte)),
                "interactions_internes": internes,
                "interactions_externes": externes,
                "part_interactions_internes": round(internes / (internes + externes), 4)
                if (internes + externes)
                else 0.0,
                "liens_internes": compteur.get("liens_internes", 0),
                "liens_externes": compteur.get("liens_externes", 0),
                "top_mots": profil["mots"],
                "top_hashtags": profil["hashtags"],
                "termes_caracteristiques": profil["tfidf"],
                "sentiment": _repartition(avec_texte["sentiment"], sentiment_analysis.CATEGORIES),
                "emotions": _repartition(avec_texte["emotion"], emotion_analysis.CATEGORIES),
                "haine": _repartition(avec_texte["haine_label"], hate_speech_analysis.CATEGORIES),
                "plateformes": [
                    {"plateforme": plateforme, "interactions": int(nombre)}
                    for plateforme, nombre in sous_ensemble["platform"].value_counts().items()
                ],
            }
        )

    communities_json = {
        **entete,
        "algorithme": contexte["algorithme"],
        "nombre_communautes": len(noms_communautes),
        "modularite": polarisation["modularite"],
        "polarisation": polarisation,
        "communautes": communautes_json,
        "matrice_interactions": contexte["matrice"],
        "utilisateurs_non_affectes": int(
            sum(1 for noeud in graphe.nodes() if appartenance.get(noeud, 0) == 0)
        ),
        "message": ""
        if communautes_json
        else "Aucune communauté n'a pu être détectée : le réseau ne contient aucun lien.",
    }

    # ---------------- content.json ----------------
    content_json = {**entete, **contexte["contenu"]}

    # ---------------- sentiment / emotions / hate ----------------
    avec_texte_global = cadre[cadre["a_du_texte"]]

    def _par_dimension(colonne: str, categories: list[str], dimension: str) -> list[dict]:
        resultat = []
        for valeur, groupe in avec_texte_global.groupby(dimension, sort=True):
            if not valeur:
                continue
            entree = {
                "cle": str(valeur),
                "libelle": str(valeur).capitalize() if dimension == "platform" else str(valeur),
                "messages": int(len(groupe)),
            }
            for element in _repartition(groupe[colonne], categories):
                entree[element["categorie"]] = element["nombre"]
                entree[f"part_{element['categorie']}"] = element["part"]
            resultat.append(entree)
        return resultat

    sentiment_json = {
        **entete,
        "categories": sentiment_analysis.CATEGORIES,
        "methode": sentiment_analysis.METHODE,
        "messages_analyses": int(len(avec_texte_global)),
        "global": _repartition(avec_texte_global["sentiment"], sentiment_analysis.CATEGORIES),
        "par_communaute": _par_dimension(
            "sentiment", sentiment_analysis.CATEGORIES, "communaute"
        ),
        "par_plateforme": _par_dimension(
            "sentiment", sentiment_analysis.CATEGORIES, "platform"
        ),
        "avertissement": (
            "Ces résultats correspondent à des classifications automatiques indicatives et "
            "doivent être interprétés avec prudence."
        ),
        "message": ""
        if len(avec_texte_global)
        else "Aucun contenu textuel n'est disponible : l'analyse de sentiment n'a pas pu être menée.",
    }

    emotions_json = {
        **entete,
        "categories": emotion_analysis.CATEGORIES,
        "methode": emotion_analysis.METHODE,
        "messages_analyses": int(len(avec_texte_global)),
        "global": _repartition(avec_texte_global["emotion"], emotion_analysis.CATEGORIES),
        "par_communaute": _par_dimension("emotion", emotion_analysis.CATEGORIES, "communaute"),
        "par_plateforme": _par_dimension("emotion", emotion_analysis.CATEGORIES, "platform"),
        "avertissement": (
            "Classification automatique indicative du contenu. Elle ne décrit pas l'état "
            "psychologique d'un utilisateur."
        ),
        "message": ""
        if len(avec_texte_global)
        else "Aucun contenu textuel n'est disponible : l'analyse colère/soutien n'a pas pu être menée.",
    }

    haineux = avec_texte_global[
        avec_texte_global["haine_label"] != hate_speech_analysis.NON_HAINEUX
    ]
    confiances = haineux["haine_confiance"].tolist()
    extraits = []
    if meta_donnees["synthetique"]:
        # Des extraits ne sont publiés que pour un corpus synthétique : aucun
        # contenu réel d'utilisateur n'est republié dans public/.
        for ligne in haineux.sort_values("haine_confiance", ascending=False).head(
            NOMBRE_EXTRAITS
        ).itertuples(index=False):
            extraits.append(
                {
                    "label": ligne.haine_label,
                    "confiance": float(ligne.haine_confiance),
                    "communaute": ligne.communaute,
                    "plateforme": ligne.platform,
                    "signaux": list(ligne.haine_signaux),
                    "extrait": ligne.raw_text[:220],
                }
            )

    hate_json = {
        **entete,
        "categories": hate_speech_analysis.CATEGORIES,
        "methode": hate_speech_analysis.METHODE,
        "messages_analyses": int(len(avec_texte_global)),
        "global": _repartition(avec_texte_global["haine_label"], hate_speech_analysis.CATEGORIES),
        "par_communaute": _par_dimension(
            "haine_label", hate_speech_analysis.CATEGORIES, "communaute"
        ),
        "par_plateforme": _par_dimension(
            "haine_label", hate_speech_analysis.CATEGORIES, "platform"
        ),
        "par_source": _par_dimension(
            "haine_label", hate_speech_analysis.CATEGORIES, "source_id"
        ),
        "confiance_moyenne": round(sum(confiances) / len(confiances), 3) if confiances else None,
        "confiance_disponible": bool(confiances),
        "extraits": extraits,
        "extraits_publies": bool(extraits),
        "note_extraits": (
            "Extraits publiés uniquement parce que le corpus analysé est synthétique."
            if extraits
            else "Aucun extrait n'est publié : le corpus analysé n'est pas synthétique, "
            "ou aucun contenu n'a été classé."
        ),
        "avertissement": (
            "Il s'agit de contenus classifiés comme potentiellement haineux, jamais "
            "d'utilisateurs qualifiés de haineux. Sentiment négatif ≠ colère ≠ toxicité "
            "≠ discours haineux ≠ polarisation."
        ),
        "message": ""
        if len(avec_texte_global)
        else "Aucun contenu textuel n'est disponible : la classification n'a pas pu être menée.",
    }

    # ---------------- propagation.json ----------------
    propagation_json = {**entete, **contexte["propagation"]}

    # ---------------- overview.json ----------------
    horodatages = cadre["horodatage"].dropna()
    evolution = []
    if not horodatages.empty:
        temporel = cadre.dropna(subset=["horodatage"]).copy()
        temporel["jour"] = temporel["horodatage"].dt.strftime("%Y-%m-%d")
        for jour, groupe in temporel.groupby("jour", sort=True):
            avec_texte_jour = groupe[groupe["a_du_texte"]]
            evolution.append(
                {
                    "date": jour,
                    "interactions": int(len(groupe)),
                    "negatif": int((avec_texte_jour["sentiment"] == "Négatif").sum()),
                    "colere": int((avec_texte_jour["emotion"] == "Colère").sum()),
                    "potentiellement_haineux": int(
                        (
                            avec_texte_jour["haine_label"]
                            == hate_speech_analysis.POTENTIELLEMENT_HAINEUX
                        ).sum()
                    ),
                }
            )

    total_interactions = int(len(cadre))
    repartition_plateformes = [
        {
            "plateforme": plateforme,
            "libelle": plateforme.capitalize(),
            "interactions": int(nombre),
            "part": round(int(nombre) / total_interactions, 4) if total_interactions else 0.0,
            "publications": int((publications["platform"] == plateforme).sum()),
        }
        for plateforme, nombre in cadre["platform"].value_counts().items()
        if plateforme
    ]

    # Une source n'est comptée comme « analysée » que si des interactions RÉELLES
    # lui sont rattachées. Un corpus synthétique couvre des identifiants de source
    # mais ne constitue jamais une donnée collectée : les deux comptes sont donc
    # exposés séparément, et jamais confondus.
    sources_couvertes = sum(1 for source in etat_sources if source["interactions"] > 0)
    sources_avec_donnees_reelles = 0 if meta_donnees["synthetique"] else sources_couvertes
    # Une source déjà pourvue en interactions réelles n'est plus « en attente » :
    # le compte des sources réelles et celui des sources en attente doivent
    # rester complémentaires et ne jamais dépasser le nombre de sources déclarées.
    sources_import_manuel = sum(
        1
        for source in etat_sources
        if source.get("import_manuel_requis", True)
        and not (source["interactions"] > 0 and not meta_donnees["synthetique"])
    )
    contenus_haineux = int(
        (
            avec_texte_global["haine_label"] == hate_speech_analysis.POTENTIELLEMENT_HAINEUX
        ).sum()
    )
    contenus_toxiques = int(
        (avec_texte_global["haine_label"] == hate_speech_analysis.TOXIQUE).sum()
    )

    overview_json = {
        **entete,
        "kpi": {
            "sources_declarees": len(etat_sources),
            "sources_avec_donnees_reelles": sources_avec_donnees_reelles,
            "sources_couvertes_par_le_corpus": sources_couvertes,
            "sources_import_manuel_requis": sources_import_manuel,
            "publications": int(len(publications)),
            "utilisateurs": len(etiquettes),
            "interactions": total_interactions,
            "communautes": len(noms_communautes),
            "modularite": polarisation["modularite"],
            "polarisation": polarisation["interpretation"],
            "contenus_potentiellement_haineux": contenus_haineux,
            "contenus_toxiques": contenus_toxiques,
            "messages_avec_texte": int(len(avec_texte_global)),
        },
        "repartition_plateformes": repartition_plateformes,
        "sentiment_global": _repartition(
            avec_texte_global["sentiment"], sentiment_analysis.CATEGORIES
        ),
        "emotions_globales": _repartition(
            avec_texte_global["emotion"], emotion_analysis.CATEGORIES
        ),
        "haine_globale": _repartition(
            avec_texte_global["haine_label"], hate_speech_analysis.CATEGORIES
        ),
        "distribution_communautes": [
            {
                "communaute": communaute["nom"],
                "utilisateurs": communaute["utilisateurs"],
                "messages": communaute["messages"],
                "part_interactions_internes": communaute["part_interactions_internes"],
            }
            for communaute in communautes_json
        ],
        "evolution_temporelle": evolution,
        "polarisation": polarisation,
        "reseau": contexte["metriques_reseau"],
        "qualite_donnees": {
            "lignes_ignorees": meta_donnees["lignes_ignorees"],
            "doublons_supprimes": meta_donnees["doublons_supprimes"],
            "types_inconnus": meta_donnees["types_inconnus"],
            "horodatages_invalides": meta_donnees["horodatages_invalides"],
            "messages_sans_texte": total_interactions - int(len(avec_texte_global)),
        },
        "questions_recherche": [
            "RQ1. Les interactions observées forment-elles des communautés distinctes ?",
            "RQ2. Quel niveau de polarisation structurelle peut être observé ?",
            "RQ3. Les communautés utilisent-elles des champs lexicaux différents ?",
            "RQ4. Certaines communautés présentent-elles davantage de sentiment négatif ?",
            "RQ5. Certaines communautés expriment-elles davantage de colère ou de soutien ?",
            "RQ6. Certaines communautés présentent-elles davantage de contenus classifiés "
            "comme toxiques ou potentiellement haineux ?",
            "RQ7. Comment les contenus se propagent-ils à travers le réseau et entre "
            "communautés ?",
            "RQ8. Observe-t-on des différences entre Facebook, X et Instagram lorsque les "
            "données disponibles permettent une comparaison valide ?",
        ],
    }

    fichiers = {
        "overview.json": overview_json,
        "sources.json": sources_json,
        "network.json": network_json,
        "communities.json": communities_json,
        "content.json": content_json,
        "sentiment.json": sentiment_json,
        "emotions.json": emotions_json,
        "hate_speech.json": hate_json,
        "propagation.json": propagation_json,
    }
    ecrits = []
    for nom, contenu_fichier in fichiers.items():
        chemin = _ecrire_json(repertoire, nom, contenu_fichier)
        affichage = _chemin_affichable(chemin)
        ecrits.append(affichage)
        print(f"       ✓ {affichage}")
    return ecrits


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Pipeline d'analyse de la polarisation et du discours de haine."
    )
    analyseur.add_argument(
        "--sortie",
        type=Path,
        default=REPERTOIRE_SORTIE,
        help="Répertoire de sortie des fichiers JSON (défaut : public/data).",
    )
    analyseur.add_argument(
        "--input",
        dest="entree",
        type=Path,
        default=None,
        help="Jeu de données empirique explicite (ex. data/real_interactions.csv). "
        "Chaque interaction doit déclarer une provenance réelle.",
    )
    arguments = analyseur.parse_args()

    print("=" * 78)
    print(TITRE)
    print(ATTRIBUTION)
    print("=" * 78)

    try:
        resume = executer(arguments.sortie, arguments.entree)
    except (
        load_sources.ErreurSources,
        load_data.ErreurDonnees,
        quality_checks.ErreurQualite,
        ErreurPipeline,
    ) as erreur:
        print(f"\nERREUR : {erreur}", file=sys.stderr)
        return 1

    print("-" * 78)
    if resume["jeu_de_donnees"]["synthetique"]:
        print(f"AVERTISSEMENT : {resume['jeu_de_donnees']['avertissement']}")
    print(
        f"Terminé : {resume['interactions']} interactions, {resume['utilisateurs']} utilisateurs, "
        f"{resume['communautes']} communautés, modularité {resume['modularite']}."
    )
    print(f"{len(resume['fichiers'])} fichiers JSON écrits dans {arguments.sortie}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
