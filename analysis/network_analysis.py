"""Construction et mesure du réseau d'utilisateurs.

Le réseau est un graphe **orienté et pondéré** :

* nœud : utilisateur pseudonymisé ;
* lien : interaction dirigée (``comment``, ``reply``, ``mention``, ``share``,
  ``repost``, ``quote``) de l'auteur vers l'utilisateur visé ;
* poids : nombre d'interactions agrégées entre deux utilisateurs.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import networkx as nx
import pandas as pd

from load_data import TYPES_RELATIONNELS

# Au-delà de ce nombre de nœuds, la centralité d'intermédiarité est estimée par
# échantillonnage afin de rester exécutable sur un ordinateur standard.
SEUIL_INTERMEDIARITE_EXACTE = 800
ECHANTILLON_INTERMEDIARITE = 200


def construire_graphe(cadre: pd.DataFrame) -> nx.DiGraph:
    """Construit le graphe orienté pondéré des interactions entre utilisateurs."""
    graphe = nx.DiGraph()

    # Tous les auteurs deviennent des nœuds, même sans lien sortant.
    for utilisateur in sorted(set(cadre["source_user"]) | set(cadre["target_user"])):
        if utilisateur:
            graphe.add_node(utilisateur, messages=0, plateformes=set(), sources=set())

    for ligne in cadre.itertuples(index=False):
        auteur = ligne.source_user
        if not auteur or auteur not in graphe:
            continue
        graphe.nodes[auteur]["messages"] += 1
        graphe.nodes[auteur]["plateformes"].add(ligne.platform)
        graphe.nodes[auteur]["sources"].add(ligne.source_id)

        cible = ligne.target_user
        if not cible or cible == auteur or ligne.interaction_type not in TYPES_RELATIONNELS:
            continue
        if graphe.has_edge(auteur, cible):
            lien = graphe.edges[auteur, cible]
            lien["weight"] += 1
            lien["types"][ligne.interaction_type] = (
                lien["types"].get(ligne.interaction_type, 0) + 1
            )
            lien["plateformes"].add(ligne.platform)
            lien["sources"].add(ligne.source_id)
        else:
            graphe.add_edge(
                auteur,
                cible,
                weight=1,
                types={ligne.interaction_type: 1},
                plateformes={ligne.platform},
                sources={ligne.source_id},
            )
    return graphe


def calculer_metriques(graphe: nx.DiGraph) -> dict:
    """Métriques structurelles globales du réseau."""
    nombre_noeuds = graphe.number_of_nodes()
    nombre_liens = graphe.number_of_edges()
    if nombre_noeuds == 0:
        return {
            "noeuds": 0,
            "liens": 0,
            "poids_total": 0,
            "densite": 0.0,
            "degre_moyen": 0.0,
            "degre_entrant_moyen": 0.0,
            "degre_sortant_moyen": 0.0,
            "composantes_faibles": 0,
            "taille_composante_principale": 0,
            "part_composante_principale": 0.0,
            "reciprocite": 0.0,
            "intermediarite_exacte": True,
        }

    poids_total = int(sum(donnees["weight"] for _, _, donnees in graphe.edges(data=True)))
    composantes = sorted(nx.weakly_connected_components(graphe), key=len, reverse=True)
    principale = len(composantes[0]) if composantes else 0

    return {
        "noeuds": nombre_noeuds,
        "liens": nombre_liens,
        "poids_total": poids_total,
        "densite": round(nx.density(graphe), 5),
        "degre_moyen": round(
            sum(dict(graphe.degree()).values()) / nombre_noeuds, 3
        ),
        "degre_entrant_moyen": round(nombre_liens / nombre_noeuds, 3),
        "degre_sortant_moyen": round(nombre_liens / nombre_noeuds, 3),
        "composantes_faibles": len(composantes),
        "taille_composante_principale": principale,
        "part_composante_principale": round(principale / nombre_noeuds, 4),
        "reciprocite": round(nx.reciprocity(graphe) or 0.0, 4) if nombre_liens else 0.0,
        "intermediarite_exacte": nombre_noeuds <= SEUIL_INTERMEDIARITE_EXACTE,
    }


def calculer_centralites(graphe: nx.DiGraph) -> dict[str, dict[str, float]]:
    """Centralités par nœud : degré, degré entrant/sortant, intermédiarité."""
    if graphe.number_of_nodes() == 0:
        return {}

    centralite_degre = nx.degree_centrality(graphe)
    centralite_entrante = nx.in_degree_centrality(graphe)
    centralite_sortante = nx.out_degree_centrality(graphe)

    if graphe.number_of_nodes() <= SEUIL_INTERMEDIARITE_EXACTE:
        intermediarite = nx.betweenness_centrality(graphe, weight=None, normalized=True)
    else:
        intermediarite = nx.betweenness_centrality(
            graphe,
            k=min(ECHANTILLON_INTERMEDIARITE, graphe.number_of_nodes()),
            weight=None,
            normalized=True,
            seed=42,
        )

    return {
        noeud: {
            "degre": int(graphe.degree(noeud)),
            "degre_entrant": int(graphe.in_degree(noeud)),
            "degre_sortant": int(graphe.out_degree(noeud)),
            "poids_entrant": int(
                sum(donnees["weight"] for _, _, donnees in graphe.in_edges(noeud, data=True))
            ),
            "poids_sortant": int(
                sum(donnees["weight"] for _, _, donnees in graphe.out_edges(noeud, data=True))
            ),
            "centralite_degre": round(centralite_degre.get(noeud, 0.0), 5),
            "centralite_entrante": round(centralite_entrante.get(noeud, 0.0), 5),
            "centralite_sortante": round(centralite_sortante.get(noeud, 0.0), 5),
            "centralite_intermediarite": round(intermediarite.get(noeud, 0.0), 5),
        }
        for noeud in graphe.nodes()
    }
