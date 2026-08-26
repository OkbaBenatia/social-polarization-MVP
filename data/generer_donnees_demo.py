"""Génération du jeu de données de démonstration ``sample_interactions.csv``.

Ce script produit un jeu de données **entièrement synthétique**. Il ne contient
aucune donnée réelle collectée sur Facebook, X ou Instagram : les identifiants
d'utilisateurs, les textes et les horodatages sont fabriqués.

Objectif : disposer d'un jeu de données reproductible permettant de démontrer
l'ensemble du pipeline (réseau, communautés, polarisation, lexique, sentiment,
colère/soutien, toxicité, propagation) sans exploiter de contenu réel.

Utilisation :

    python data/generer_donnees_demo.py

Le fichier produit est ``data/sample_interactions.csv``. Les résultats calculés
à partir de ce fichier ne constituent pas des résultats empiriques.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

GRAINE = 20260119
RACINE = Path(__file__).resolve().parent
FICHIER_SORTIE = RACINE / "sample_interactions.csv"
# Horodatage fixe : la génération doit rester reproductible d'une exécution à l'autre.
HORODATAGE_GENERATION = "2026-01-19T00:00:00"

COLONNES = [
    "platform",
    "source_id",
    "post_id",
    "interaction_id",
    "source_user",
    "target_user",
    "interaction_type",
    "text",
    "timestamp",
    "parent_id",
    "url",
    # Traçabilité : ce corpus est explicitement synthétique et ne doit jamais
    # alimenter un résultat empirique (voir analysis/provenance.py).
    "provenance",
    "collection_method",
    "collected_at",
]

PROVENANCE_DEMO = "synthetic_demo"
METHODE_DEMO = "generation synthetique (data/generer_donnees_demo.py)"

# --- Sources de démonstration (alignées sur data/sources.json) ---------------
SOURCES = [
    ("facebook_001", "facebook", "https://www.facebook.com/share/v/18hGjKiFVK/"),
    ("facebook_002", "facebook", "https://www.facebook.com/share/p/1HYJ6PKM2Q/"),
    ("facebook_003", "facebook", "https://www.facebook.com/share/v/1GCZzavgcV/"),
    ("facebook_004", "facebook", "https://www.facebook.com/share/p/1F5HSSqfkM/"),
    ("facebook_005", "facebook", "https://www.facebook.com/share/p/18GdU39RoV/"),
    ("x_001", "x", "https://x.com/i/status/2087872720012796385"),
    (
        "instagram_001",
        "instagram",
        "https://www.instagram.com/reel/DbtVlHYABVK/?igsh=MTBneGEwbGhndHBtNw==",
    ),
]

# --- Groupes latents --------------------------------------------------------
# Les noms ci-dessous décrivent des CHAMPS THÉMATIQUES, pas des positions
# idéologiques. Le pipeline ne réutilise jamais ces étiquettes : les
# communautés détectées sont nommées « Communauté 1 », « Communauté 2 », etc.
GROUPES = [
    {
        "cle": "langue_education",
        "taille": 26,
        "hashtags": ["#arabisation", "#école", "#langue", "#université", "#تعريب"],
        "sujets": [
            "la langue d'enseignement",
            "l'arabisation des programmes",
            "la place du français à l'école",
            "la réforme universitaire",
            "le bilinguisme",
        ],
    },
    {
        "cle": "religion_societe",
        "taille": 22,
        "hashtags": ["#religion", "#valeurs", "#société", "#tradition", "#دين"],
        "sujets": [
            "la place de la religion dans l'espace public",
            "les valeurs transmises à l'école",
            "le rapport entre foi et société",
            "la liberté de croyance",
            "les traditions familiales",
        ],
    },
    {
        "cle": "migration_economie",
        "taille": 20,
        "hashtags": ["#immigration", "#travail", "#économie", "#frontières", "#هجرة"],
        "sujets": [
            "l'immigration de travail",
            "l'accueil des nouveaux arrivants",
            "la politique migratoire",
            "l'emploi et la formation",
            "les conditions de logement",
        ],
    },
    {
        "cle": "identite_nation",
        "taille": 16,
        "hashtags": ["#identité", "#culture", "#patrimoine", "#nation", "#هوية"],
        "sujets": [
            "l'identité culturelle",
            "le patrimoine commun",
            "le sentiment d'appartenance",
            "la transmission culturelle",
            "la mémoire collective",
        ],
    },
]

# --- Banques de formulations par registre -----------------------------------
# Chaque registre correspond à un style de message attendu. Les catégories
# annotées par le pipeline (sentiment, colère/soutien, toxicité) sont ensuite
# recalculées de manière indépendante : les registres ci-dessous ne sont PAS
# écrits dans le jeu de données et ne servent pas de vérité terrain.
TEMPLATES = {
    "neutre": [
        "Il faudrait des chiffres précis sur {sujet} avant de conclure quoi que ce soit.",
        "Quelqu'un a-t-il une source sérieuse concernant {sujet} ? {hashtag}",
        "Le rapport publié l'an dernier abordait déjà {sujet}, page 42.",
        "On peut discuter de {sujet} sans transformer chaque échange en affrontement.",
        "Je partage cette vidéo pour information, elle traite de {sujet}.",
        "هذا الموضوع يحتاج إلى نقاش هادئ ومعطيات دقيقة. {hashtag}",
        "Question honnête : quelles données existent réellement sur {sujet} ?",
        "Le débat sur {sujet} revient chaque année, sans évaluation publique.",
    ],
    "positif": [
        "Excellente analyse sur {sujet}, merci pour la clarté du propos. {hashtag}",
        "Bravo pour ce travail documenté, c'est exactement ce qui manquait.",
        "Merci d'aborder {sujet} avec autant de calme et de respect.",
        "Très bonne intervention, je suis d'accord avec l'essentiel.",
        "شكرا على هذا الطرح الممتاز حول {sujet}. {hashtag}",
        "Un contenu utile et bien construit, à partager largement.",
        "Respect pour le courage de poser la question de {sujet} publiquement.",
    ],
    "soutien": [
        "Je soutiens totalement cette position sur {sujet}, continuez. {hashtag}",
        "Exactement ce que je pense depuis des années, merci de le dire.",
        "Nous sommes nombreux à partager cet avis, courage à vous.",
        "D'accord à 100 %, il faut défendre cette idée.",
        "نؤيد هذا الموقف تماما، بارك الله فيك. {hashtag}",
        "Vous avez tout mon soutien, ne lâchez rien.",
        "Bravo, enfin quelqu'un qui défend {sujet} sans complexe.",
    ],
    "negatif": [
        "Franchement, ce discours sur {sujet} est un échec complet.",
        "C'est un désastre, rien n'a avancé sur {sujet} depuis dix ans.",
        "Ce raisonnement est faux et ne repose sur aucune donnée sérieuse.",
        "Encore une promesse non tenue au sujet de {sujet}. {hashtag}",
        "هذا الكلام غير صحيح ولا يستند إلى أي دليل.",
        "Je ne suis pas d'accord, l'argument sur {sujet} ne tient pas.",
        "Décevant. On tourne en rond et le problème reste entier.",
    ],
    "colere": [
        "Ça suffit ! On nous ment depuis des années sur {sujet} !!! {hashtag}",
        "C'est une honte, j'en ai vraiment marre de ce mépris.",
        "Scandaleux ! Personne n'assume ses responsabilités sur {sujet} !",
        "Insupportable. Assez de ce cirque, réveillez-vous !",
        "كفى ! هذا عار حقيقي وما نقبلوش هذا الوضع. {hashtag}",
        "Je suis en colère, on se moque ouvertement de nous.",
        "Trop c'est trop, la coupe est pleine !!!",
    ],
    "toxique": [
        "Bande d'ignorants, vous ne comprenez rien à {sujet}.",
        "Arrête de dire n'importe quoi, tu es complètement stupide.",
        "Menteur professionnel, personne ne te croit ici.",
        "Quel imbécile, il ferait mieux de se taire.",
        "كذاب، ما عندك حتى فكرة على {sujet}.",
        "Tu es ridicule, va apprendre avant d'ouvrir la bouche.",
    ],
    "haineux": [
        "Ces gens n'ont rien à faire ici, qu'ils dégagent tous.",
        "Il faut expulser les immigrés, ce sont des envahisseurs.",
        "Les étrangers doivent partir, dehors, on ne veut pas d'eux.",
        "Ces gens-là sont des parasites, il faut les chasser du pays.",
        "اطردوهم كلهم، هؤلاء الأجانب غزاة ولا مكان لهم هنا.",
    ],
}

# Profil de registre par groupe : (neutre, positif, soutien, negatif, colere, toxique, haineux)
PROFILS = {
    "langue_education": [0.34, 0.18, 0.16, 0.18, 0.09, 0.04, 0.01],
    "religion_societe": [0.28, 0.16, 0.22, 0.16, 0.12, 0.05, 0.01],
    "migration_economie": [0.24, 0.10, 0.12, 0.22, 0.18, 0.09, 0.05],
    "identite_nation": [0.22, 0.09, 0.15, 0.19, 0.19, 0.10, 0.06],
}
REGISTRES = ["neutre", "positif", "soutien", "negatif", "colere", "toxique", "haineux"]

# Probabilité qu'une interaction vise un membre d'un autre groupe.
P_INTER_GROUPE = 0.22
# Un message adressé à un autre groupe est plus souvent conflictuel.
BONUS_CONFLIT_INTER = {"negatif": 1.9, "colere": 2.2, "toxique": 2.4, "haineux": 2.4}


def choisir_registre(rng: random.Random, groupe: str, inter_groupe: bool) -> str:
    poids = list(PROFILS[groupe])
    if inter_groupe:
        for i, reg in enumerate(REGISTRES):
            poids[i] *= BONUS_CONFLIT_INTER.get(reg, 0.7)
    return rng.choices(REGISTRES, weights=poids, k=1)[0]


def composer_texte(rng: random.Random, groupe: dict, registre: str, mention: str | None) -> str:
    modele = rng.choice(TEMPLATES[registre])
    texte = modele.format(
        sujet=rng.choice(groupe["sujets"]),
        hashtag=rng.choice(groupe["hashtags"]),
    )
    if mention and rng.random() < 0.30:
        texte = f"@{mention} {texte}"
    if rng.random() < 0.12:
        texte += " " + rng.choice(groupe["hashtags"])
    if rng.random() < 0.08:
        texte += " https://exemple.org/article-" + str(rng.randint(100, 999))
    if rng.random() < 0.06:
        texte += " " + rng.choice(["😡", "👏", "🙏", "🤔", "💯"])
    return texte


def generer() -> list[dict]:
    rng = random.Random(GRAINE)

    # --- Utilisateurs --------------------------------------------------------
    utilisateurs: list[str] = []
    groupe_de: dict[str, int] = {}
    for idx, groupe in enumerate(GROUPES):
        for _ in range(groupe["taille"]):
            uid = f"u{len(utilisateurs) + 1:03d}"
            utilisateurs.append(uid)
            groupe_de[uid] = idx
    membres = {i: [u for u in utilisateurs if groupe_de[u] == i] for i in range(len(GROUPES))}

    lignes: list[dict] = []
    compteur_interaction = 0
    debut = datetime(2026, 1, 5, 8, 0, 0)

    def prochain_id() -> str:
        nonlocal compteur_interaction
        compteur_interaction += 1
        return f"i{compteur_interaction:04d}"

    # --- Publications racines ------------------------------------------------
    # Deux publications par source, réparties sur les groupes.
    publications = []
    numero_post = 0
    for src_index, (source_id, plateforme, url) in enumerate(SOURCES):
        for k in range(2):
            numero_post += 1
            idx_groupe = (src_index + k) % len(GROUPES)
            groupe = GROUPES[idx_groupe]
            auteur = rng.choice(membres[idx_groupe])
            post_id = f"p{numero_post:03d}"
            horodatage = debut + timedelta(hours=6 * numero_post + rng.randint(0, 5))
            registre = rng.choices(
                ["neutre", "positif", "negatif", "colere"], weights=[0.5, 0.2, 0.2, 0.1], k=1
            )[0]
            lignes.append(
                {
                    "platform": plateforme,
                    "source_id": source_id,
                    "post_id": post_id,
                    "interaction_id": post_id,
                    "source_user": auteur,
                    "target_user": "",
                    "interaction_type": "post",
                    "text": composer_texte(rng, groupe, registre, None),
                    "timestamp": horodatage.isoformat(),
                    "parent_id": "",
                    "url": url,
                }
            )
            publications.append(
                {
                    "post_id": post_id,
                    "source_id": source_id,
                    "platform": plateforme,
                    "url": url,
                    "auteur": auteur,
                    "groupe": idx_groupe,
                    "horodatage": horodatage,
                }
            )

    # --- Commentaires, réponses, partages -----------------------------------
    for pub in publications:
        base = pub["horodatage"]
        commentaires: list[dict] = []
        nb_commentaires = rng.randint(6, 16)
        for _ in range(nb_commentaires):
            inter = rng.random() < P_INTER_GROUPE
            idx_groupe = (
                rng.choice([g for g in range(len(GROUPES)) if g != pub["groupe"]])
                if inter
                else pub["groupe"]
            )
            auteur = rng.choice(membres[idx_groupe])
            if auteur == pub["auteur"]:
                continue
            registre = choisir_registre(rng, GROUPES[idx_groupe]["cle"], inter)
            horodatage = base + timedelta(minutes=rng.randint(5, 900))
            iid = prochain_id()
            lignes.append(
                {
                    "platform": pub["platform"],
                    "source_id": pub["source_id"],
                    "post_id": pub["post_id"],
                    "interaction_id": iid,
                    "source_user": auteur,
                    "target_user": pub["auteur"],
                    "interaction_type": "comment",
                    "text": composer_texte(rng, GROUPES[idx_groupe], registre, None),
                    "timestamp": horodatage.isoformat(),
                    "parent_id": pub["post_id"],
                    "url": pub["url"],
                }
            )
            commentaires.append(
                {
                    "id": iid,
                    "auteur": auteur,
                    "groupe": idx_groupe,
                    "horodatage": horodatage,
                    "profondeur": 1,
                }
            )

        # Réponses en chaîne (profondeur jusqu'à 4)
        file_attente = list(commentaires)
        while file_attente:
            parent = file_attente.pop(0)
            if parent["profondeur"] >= 4:
                continue
            nb_reponses = rng.choices([0, 1, 2, 3], weights=[0.46, 0.30, 0.16, 0.08], k=1)[0]
            for _ in range(nb_reponses):
                inter = rng.random() < (P_INTER_GROUPE + 0.14)
                idx_groupe = (
                    rng.choice([g for g in range(len(GROUPES)) if g != parent["groupe"]])
                    if inter
                    else parent["groupe"]
                )
                auteur = rng.choice(membres[idx_groupe])
                if auteur == parent["auteur"]:
                    continue
                registre = choisir_registre(rng, GROUPES[idx_groupe]["cle"], inter)
                horodatage = parent["horodatage"] + timedelta(minutes=rng.randint(3, 480))
                iid = prochain_id()
                lignes.append(
                    {
                        "platform": pub["platform"],
                        "source_id": pub["source_id"],
                        "post_id": pub["post_id"],
                        "interaction_id": iid,
                        "source_user": auteur,
                        "target_user": parent["auteur"],
                        "interaction_type": "reply",
                        "text": composer_texte(rng, GROUPES[idx_groupe], registre, parent["auteur"]),
                        "timestamp": horodatage.isoformat(),
                        "parent_id": parent["id"],
                        "url": pub["url"],
                    }
                )
                file_attente.append(
                    {
                        "id": iid,
                        "auteur": auteur,
                        "groupe": idx_groupe,
                        "horodatage": horodatage,
                        "profondeur": parent["profondeur"] + 1,
                    }
                )

        # Rediffusions : share / repost / quote / mention
        types_rediffusion = {
            "facebook": ["share", "mention"],
            "x": ["repost", "quote", "mention"],
            "instagram": ["share", "mention"],
        }[pub["platform"]]
        for _ in range(rng.randint(2, 6)):
            inter = rng.random() < (P_INTER_GROUPE + 0.10)
            idx_groupe = (
                rng.choice([g for g in range(len(GROUPES)) if g != pub["groupe"]])
                if inter
                else pub["groupe"]
            )
            auteur = rng.choice(membres[idx_groupe])
            if auteur == pub["auteur"]:
                continue
            type_interaction = rng.choice(types_rediffusion)
            registre = choisir_registre(rng, GROUPES[idx_groupe]["cle"], inter)
            horodatage = base + timedelta(minutes=rng.randint(20, 2600))
            texte = (
                ""
                if type_interaction in {"share", "repost"} and rng.random() < 0.45
                else composer_texte(rng, GROUPES[idx_groupe], registre, pub["auteur"])
            )
            lignes.append(
                {
                    "platform": pub["platform"],
                    "source_id": pub["source_id"],
                    "post_id": pub["post_id"],
                    "interaction_id": prochain_id(),
                    "source_user": auteur,
                    "target_user": pub["auteur"],
                    "interaction_type": type_interaction,
                    "text": texte,
                    "timestamp": horodatage.isoformat(),
                    "parent_id": pub["post_id"],
                    "url": pub["url"],
                }
            )

    lignes.sort(key=lambda ligne: (ligne["timestamp"], ligne["interaction_id"]))
    return lignes


def main() -> None:
    lignes = generer()
    with FICHIER_SORTIE.open("w", encoding="utf-8", newline="") as flux:
        writer = csv.DictWriter(flux, fieldnames=COLONNES, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for ligne in lignes:
            ligne.setdefault("provenance", PROVENANCE_DEMO)
            ligne.setdefault("collection_method", METHODE_DEMO)
            ligne.setdefault("collected_at", HORODATAGE_GENERATION)
        writer.writerows(lignes)
    utilisateurs = {ligne["source_user"] for ligne in lignes} | {
        ligne["target_user"] for ligne in lignes if ligne["target_user"]
    }
    print(f"Fichier écrit : {FICHIER_SORTIE}")
    print(f"  interactions : {len(lignes)}")
    print(f"  utilisateurs : {len(utilisateurs)}")
    print(f"  publications : {sum(1 for l in lignes if l['interaction_type'] == 'post')}")


if __name__ == "__main__":
    main()
