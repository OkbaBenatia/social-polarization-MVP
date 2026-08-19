"""Prétraitement du texte (français, arabe, texte mixte).

Le texte brut est conservé (``raw_text``) et une version nettoyée est produite
(``clean_text``). Les hashtags, mentions, URLs et emojis sont extraits séparément
afin de rester exploitables analytiquement.

Le traitement reste volontairement simple : aucune analyse morphologique lourde,
aucune normalisation avancée de la darija — ces choix sont documentés comme des
limites dans ``docs/LIMITES.md``.

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

MOTIF_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MOTIF_MENTION = re.compile(r"@([A-Za-z0-9_\.\-]{2,64})")
MOTIF_HASHTAG = re.compile(r"#([\w؀-ۿ][\w؀-ۿ\-_]{1,48})", re.UNICODE)
MOTIF_ESPACES = re.compile(r"\s+")
MOTIF_REPETITION = re.compile(r"(.)\1{3,}")
MOTIF_ARABE = re.compile(r"[؀-ۿݐ-ݿ]")
MOTIF_LATIN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]")
MOTIF_JETON = re.compile(r"[\w؀-ۿ][\w؀-ۿ'’\-]*", re.UNICODE)

# Diacritiques arabes (tashkeel) et tatweel
DIACRITIQUES_ARABES = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")

TRADUCTION_ARABE = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        "ة": "ه",
    }
)

# Mots vides français et arabes (listes courtes et explicites, sans dépendance externe).
MOTS_VIDES_FR = {
    "a", "à", "ai", "aie", "ainsi", "alors", "au", "aucun", "aussi", "autre", "aux",
    "avaient", "avais", "avait", "avant", "avec", "avoir", "bien", "car", "ce", "cela",
    "celle", "celles", "celui", "ces", "cet", "cette", "ceux", "chaque", "chez", "comme",
    "comment", "d", "dans", "de", "des", "deux", "dit", "donc", "dont", "du", "elle",
    "elles", "en", "encore", "entre", "est", "et", "étaient", "étais", "était", "été",
    "être", "eu", "faire", "fait", "fois", "font", "hors", "ici", "il", "ils", "j", "je",
    "l", "la", "le", "les", "leur", "leurs", "lui", "m", "ma", "mais", "me", "même",
    "mes", "moi", "mon", "n", "ne", "ni", "non", "nos", "notre", "nous", "on", "ont",
    "ou", "où", "par", "parce", "pas", "peu", "peut", "plus", "pour", "pourquoi",
    "qu", "quand", "que", "quel", "quelle", "quelles", "quels", "qui", "quoi", "s", "sa",
    "sans", "se", "sera", "ses", "seulement", "si", "soit", "son", "sont", "sous", "sur",
    "t", "ta", "te", "tes", "toi", "ton", "tous", "tout", "toute", "toutes", "tu", "un",
    "une", "vos", "votre", "vous", "y", "cest", "c", "ça", "déjà", "aujourd", "hui",
    "suis", "es", "sommes", "êtes", "étiez", "étions", "serai", "serait", "seront",
    "ai", "as", "avez", "avons", "aura", "aurait", "rien", "trop", "depuis", "très",
    "vraiment", "toujours", "beaucoup", "moins", "an", "ans", "va", "vais", "vont",
    "dire", "faut", "faudrait", "quelqu", "autres", "an",
}

MOTS_VIDES_AR = {
    "من", "في", "على", "الى", "إلى", "عن", "مع", "هذا", "هذه", "ذلك", "تلك", "التي",
    "الذي", "الذين", "ما", "لا", "لم", "لن", "قد", "كان", "كانت", "يكون", "هو", "هي",
    "هم", "هن", "انا", "أنا", "نحن", "انت", "أنت", "كل", "بعض", "بين", "او", "أو",
    "ثم", "حتى", "اذا", "إذا", "عند", "بعد", "قبل", "ان", "أن", "إن", "و", "ب", "ل",
    "ال", "يا", "هنا", "هناك", "كما", "لكن", "غير", "دون", "كي", "الي",
}

MOTS_VIDES = MOTS_VIDES_FR | MOTS_VIDES_AR

# Élisions françaises : « l'école » est découpé en « l » + « école » afin que le
# terme porteur de sens soit correctement isolé, et que les marques de négation
# (« n' ») restent détectables par les classifieurs.
ELISIONS = {
    "l", "d", "j", "n", "m", "t", "s", "c", "qu",
    "lorsqu", "puisqu", "jusqu", "quoiqu", "quelqu",
}


def extraire_hashtags(texte: str) -> list[str]:
    return [f"#{correspondance.lower()}" for correspondance in MOTIF_HASHTAG.findall(texte)]


def extraire_mentions(texte: str) -> list[str]:
    return [correspondance for correspondance in MOTIF_MENTION.findall(texte)]


def extraire_urls(texte: str) -> list[str]:
    return MOTIF_URL.findall(texte)


def extraire_emojis(texte: str) -> list[str]:
    return [
        caractere
        for caractere in texte
        if unicodedata.category(caractere) == "So" or ord(caractere) > 0x1F000
    ]


def detecter_langue(texte: str) -> str:
    """Détection sommaire fondée sur les systèmes d'écriture présents."""
    arabe = len(MOTIF_ARABE.findall(texte))
    latin = len(MOTIF_LATIN.findall(texte))
    if arabe == 0 and latin == 0:
        return "indetermine"
    if arabe and latin:
        proportion = arabe / (arabe + latin)
        if 0.15 <= proportion <= 0.85:
            return "mixte"
        return "ar" if proportion > 0.85 else "fr"
    return "ar" if arabe else "fr"


def nettoyer_texte(texte: str, conserver_hashtags: bool = True) -> str:
    """Produit ``clean_text`` : texte normalisé destiné à l'analyse lexicale."""
    if not texte:
        return ""
    resultat = unicodedata.normalize("NFKC", texte)
    resultat = MOTIF_URL.sub(" ", resultat)
    resultat = MOTIF_MENTION.sub(" ", resultat)
    if conserver_hashtags:
        # Le croisillon est retiré mais le terme, porteur de sens, est conservé.
        resultat = re.sub(r"#(?=[\w؀-ۿ])", " ", resultat)
    else:
        resultat = MOTIF_HASHTAG.sub(" ", resultat)
    resultat = DIACRITIQUES_ARABES.sub("", resultat)
    resultat = resultat.translate(TRADUCTION_ARABE)
    resultat = MOTIF_REPETITION.sub(r"\1\1", resultat)
    resultat = resultat.lower()
    resultat = re.sub(r"[^\w؀-ۿ'’\-\s]", " ", resultat)
    resultat = re.sub(r"[_\d]+", " ", resultat)
    return MOTIF_ESPACES.sub(" ", resultat).strip()


def _decouper_elision(jeton: str) -> list[str]:
    """Sépare le préfixe élidé du terme qu'il introduit."""
    parties = re.split(r"['’]", jeton, maxsplit=1)
    if len(parties) == 2 and parties[0] in ELISIONS and parties[1]:
        return [parties[0], parties[1]]
    return [jeton]


def jetons(texte_nettoye: str, retirer_mots_vides: bool = True, longueur_min: int = 2) -> list[str]:
    """Découpe en jetons analytiques.

    ``retirer_mots_vides`` est activé pour l'analyse lexicale et désactivé pour
    les classifieurs, qui ont besoin des marques de négation et des adverbes
    d'intensité.
    """
    resultat = []
    for brut in MOTIF_JETON.findall(texte_nettoye):
        for jeton in _decouper_elision(brut):
            jeton = jeton.strip("-'’")
            if len(jeton) < longueur_min:
                continue
            if retirer_mots_vides and jeton in MOTS_VIDES:
                continue
            resultat.append(jeton)
    return resultat


def pretraiter(cadre: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes de prétraitement au tableau d'interactions."""
    cadre = cadre.copy()
    cadre["raw_text"] = cadre["text"].fillna("").astype(str)
    cadre["clean_text"] = cadre["raw_text"].map(nettoyer_texte)
    cadre["hashtags"] = cadre["raw_text"].map(extraire_hashtags)
    cadre["mentions"] = cadre["raw_text"].map(extraire_mentions)
    cadre["urls"] = cadre["raw_text"].map(extraire_urls)
    cadre["emojis"] = cadre["raw_text"].map(extraire_emojis)
    cadre["langue"] = cadre["raw_text"].map(detecter_langue)
    # Jetons complets : utilisés par les classifieurs. Les jetons d'un seul
    # caractère sont conservés car « n' » porte la négation (« n'est pas »).
    cadre["jetons"] = cadre["clean_text"].map(
        lambda texte: jetons(texte, retirer_mots_vides=False, longueur_min=1)
    )
    # Jetons lexicaux : mots vides retirés, utilisés pour l'analyse lexicale.
    cadre["jetons_lexicaux"] = cadre["clean_text"].map(
        lambda texte: jetons(texte, retirer_mots_vides=True)
    )
    cadre["a_du_texte"] = cadre["clean_text"].str.len() > 0
    return cadre
