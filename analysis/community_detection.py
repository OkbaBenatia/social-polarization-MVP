"""Détection des communautés et mesure de la polarisation structurelle.

L'algorithme employé est **Louvain** (Blondel et al., 2008), appliqué à la
projection non orientée et pondérée du réseau d'interactions.

Les communautés reçoivent uniquement des noms neutres (« Communauté 1 »,
« Communauté 2 »…). Aucune étiquette idéologique n'est générée
automatiquement : l'interprétation reste une tâche humaine.

Les seuils d'interprétation de la polarisation sont **indicatifs** et
documentés comme tels (voir ``docs/METHODOLOGIE.md``).

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import networkx as nx

try:  # python-louvain
    import community as community_louvain
except ImportError:  # pragma: no cover - dépendance déclarée dans requirements.txt
    community_louvain = None

GRAINE = 42

# Seuils indicatifs fondés sur l'usage courant de la modularité de Newman.
# Ils ne constituent pas une métrique validée : ils servent uniquement à
# formuler une lecture qualitative.
SEUIL_MODULARITE_MODEREE = 0.30
SEUIL_MODULARITE_FORTE = 0.50


def projeter_non_oriente(graphe: nx.DiGraph) -> nx.Graph:
    """Projection non orientée pondérée (les poids opposés sont additionnés)."""
    projection = nx.Graph()
    projection.add_nodes_from(graphe.nodes())
    for origine, destination, donnees in graphe.edges(data=True):
        poids = donnees.get("weight", 1)
        if projection.has_edge(origine, destination):
            projection.edges[origine, destination]["weight"] += poids
        else:
            projection.add_edge(origine, destination, weight=poids)
    return projection


def detecter_communautes(graphe: nx.DiGraph) -> tuple[dict[str, int], float, str]:
    """Retourne (appartenance, modularité, algorithme utilisé)."""
    projection = projeter_non_oriente(graphe)
    if projection.number_of_nodes() == 0:
        return {}, 0.0, "aucun"
    if projection.number_of_edges() == 0:
        # Sans lien, chaque utilisateur est isolé : aucune communauté détectable.
        return {noeud: 0 for noeud in projection.nodes()}, 0.0, "aucun (réseau sans lien)"

    if community_louvain is not None:
        appartenance = community_louvain.best_partition(
            projection, weight="weight", random_state=GRAINE
        )
        algorithme = "Louvain (python-louvain)"
    else:  # repli sur l'implémentation NetworkX
        groupes = nx.community.louvain_communities(
            projection, weight="weight", seed=GRAINE
        )
        appartenance = {
            noeud: index for index, groupe in enumerate(groupes) for noeud in groupe
        }
        algorithme = "Louvain (networkx)"

    # Renumérotation stable : les communautés les plus grandes en premier.
    tailles: dict[int, int] = {}
    for identifiant in appartenance.values():
        tailles[identifiant] = tailles.get(identifiant, 0) + 1
    ordre = sorted(tailles, key=lambda identifiant: (-tailles[identifiant], identifiant))
    renumerotation = {ancien: nouveau for nouveau, ancien in enumerate(ordre, start=1)}
    appartenance = {noeud: renumerotation[identifiant] for noeud, identifiant in appartenance.items()}

    groupes_finaux: dict[int, set[str]] = {}
    for noeud, identifiant in appartenance.items():
        groupes_finaux.setdefault(identifiant, set()).add(noeud)
    modularite = nx.community.modularity(
        projection, list(groupes_finaux.values()), weight="weight"
    )
    return appartenance, float(modularite), algorithme


def nom_communaute(identifiant: int) -> str:
    """Nom neutre affiché dans le tableau de bord."""
    return f"Communauté {identifiant}"


def compter_liens_internes_externes(
    graphe: nx.DiGraph, appartenance: dict[str, int]
) -> dict[int, dict[str, int]]:
    """Interactions internes et externes, par communauté."""
    compteurs: dict[int, dict[str, int]] = {}
    for identifiant in set(appartenance.values()):
        compteurs[identifiant] = {
            "liens_internes": 0,
            "liens_externes": 0,
            "interactions_internes": 0,
            "interactions_externes": 0,
        }
    for origine, destination, donnees in graphe.edges(data=True):
        groupe_origine = appartenance.get(origine)
        groupe_destination = appartenance.get(destination)
        if groupe_origine is None or groupe_destination is None:
            continue
        poids = int(donnees.get("weight", 1))
        if groupe_origine == groupe_destination:
            compteurs[groupe_origine]["liens_internes"] += 1
            compteurs[groupe_origine]["interactions_internes"] += poids
        else:
            compteurs[groupe_origine]["liens_externes"] += 1
            compteurs[groupe_origine]["interactions_externes"] += poids
            compteurs[groupe_destination]["liens_externes"] += 1
            compteurs[groupe_destination]["interactions_externes"] += poids
    return compteurs


def matrice_interactions(
    graphe: nx.DiGraph, appartenance: dict[str, int]
) -> list[dict[str, object]]:
    """Matrice orientée des interactions entre communautés."""
    matrice: dict[tuple[int, int], int] = {}
    for origine, destination, donnees in graphe.edges(data=True):
        groupe_origine = appartenance.get(origine)
        groupe_destination = appartenance.get(destination)
        if groupe_origine is None or groupe_destination is None:
            continue
        cle = (groupe_origine, groupe_destination)
        matrice[cle] = matrice.get(cle, 0) + int(donnees.get("weight", 1))
    return [
        {
            "source": nom_communaute(origine),
            "cible": nom_communaute(destination),
            "source_id": origine,
            "cible_id": destination,
            "interactions": valeur,
        }
        for (origine, destination), valeur in sorted(matrice.items())
    ]


def interpreter_polarisation(modularite: float) -> str:
    """Lecture qualitative **indicative** de la modularité."""
    if modularite < SEUIL_MODULARITE_MODEREE:
        return "Polarisation faible"
    if modularite < SEUIL_MODULARITE_FORTE:
        return "Polarisation modérée"
    return "Polarisation forte"


def mesurer_polarisation(
    graphe: nx.DiGraph, appartenance: dict[str, int], modularite: float
) -> dict:
    """Indicateurs simples et transparents de polarisation structurelle."""
    internes = 0
    externes = 0
    for origine, destination, donnees in graphe.edges(data=True):
        groupe_origine = appartenance.get(origine)
        groupe_destination = appartenance.get(destination)
        if groupe_origine is None or groupe_destination is None:
            continue
        poids = int(donnees.get("weight", 1))
        if groupe_origine == groupe_destination:
            internes += poids
        else:
            externes += poids

    total = internes + externes
    part_internes = internes / total if total else 0.0
    ratio = internes / externes if externes else None

    return {
        "modularite": round(modularite, 4),
        "interactions_intra_communautes": internes,
        "interactions_inter_communautes": externes,
        "interactions_totales": total,
        "part_liens_internes": round(part_internes, 4),
        "ratio_intra_inter": round(ratio, 3) if ratio is not None else None,
        "interpretation": interpreter_polarisation(modularite),
        "seuils_indicatifs": {
            "faible": f"modularité < {SEUIL_MODULARITE_MODEREE}",
            "moderee": f"{SEUIL_MODULARITE_MODEREE} ≤ modularité < {SEUIL_MODULARITE_FORTE}",
            "forte": f"modularité ≥ {SEUIL_MODULARITE_FORTE}",
        },
        "avertissement": (
            "Les seuils d'interprétation sont indicatifs et conventionnels. Ils ne "
            "constituent pas une mesure validée de la polarisation et ne remplacent pas "
            "la lecture des valeurs numériques."
        ),
    }
