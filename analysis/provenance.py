"""Provenance des données : vocabulaire commun à toute la chaîne.

Chaque interaction analysée doit déclarer d'où elle vient. Trois provenances
correspondent à des données réellement obtenues depuis les publications
étudiées ; la quatrième identifie le corpus synthétique de démonstration, qui
ne doit jamais alimenter un résultat empirique.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

# --- Provenances -----------------------------------------------------------
OFFICIAL_API = "official_api"
PUBLIC_PAGE = "public_page"
MANUAL_VERIFIED = "manual_verified"
#: Données publiques collectées via l'API tierce ScrapeCreators.
SCRAPECREATORS_PUBLIC = "scrapecreators_public"
SYNTHETIC_DEMO = "synthetic_demo"

PROVENANCES = (
    OFFICIAL_API,
    PUBLIC_PAGE,
    MANUAL_VERIFIED,
    SCRAPECREATORS_PUBLIC,
    SYNTHETIC_DEMO,
)

#: Provenances admises dans un jeu de données empirique.
PROVENANCES_REELLES = (
    OFFICIAL_API,
    PUBLIC_PAGE,
    MANUAL_VERIFIED,
    SCRAPECREATORS_PUBLIC,
)

LIBELLES_PROVENANCE = {
    OFFICIAL_API: "API officielle de la plateforme",
    PUBLIC_PAGE: "Page publique",
    MANUAL_VERIFIED: "Import manuel vérifié",
    SCRAPECREATORS_PUBLIC: "Commentaires publics via l'API ScrapeCreators",
    SYNTHETIC_DEMO: "Jeu de démonstration synthétique",
}

# --- Colonnes de traçabilité ajoutées au format normalisé ------------------
COLONNES_PROVENANCE = ["provenance", "collection_method", "collected_at"]

# --- Statuts de collecte par source ----------------------------------------
REAL_DATA_COLLECTED = "real_data_collected"
PARTIAL_REAL_DATA = "partial_real_data"
MANUAL_IMPORT_REQUIRED = "manual_import_required"
UNAVAILABLE = "unavailable"

STATUTS_COLLECTE = (
    REAL_DATA_COLLECTED,
    PARTIAL_REAL_DATA,
    MANUAL_IMPORT_REQUIRED,
    UNAVAILABLE,
)

LIBELLES_STATUT = {
    REAL_DATA_COLLECTED: "Données réelles collectées",
    PARTIAL_REAL_DATA: "Données réelles partielles",
    MANUAL_IMPORT_REQUIRED: "Import manuel requis",
    UNAVAILABLE: "Indisponible",
}


def est_reelle(provenance: str) -> bool:
    """Vrai si la provenance correspond à une donnée réellement collectée."""
    return str(provenance).strip().lower() in PROVENANCES_REELLES


def valider_provenance(provenance: str) -> str:
    """Normalise une provenance et refuse toute valeur inconnue."""
    valeur = str(provenance).strip().lower()
    if valeur not in PROVENANCES:
        raise ValueError(
            f"Provenance inconnue : « {provenance} ». "
            f"Valeurs admises : {', '.join(PROVENANCES)}."
        )
    return valeur
