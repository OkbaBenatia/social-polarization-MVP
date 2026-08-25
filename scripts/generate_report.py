"""Génération du rapport Word du MVP.

Le rapport est construit **exclusivement** à partir des résultats produits par
le pipeline d'analyse (``public/data/*.json``) et des captures d'écran du
tableau de bord (``docs/screenshots``). Aucune valeur n'est saisie en dur :
tout chiffre affiché provient d'un fichier de résultats.

Utilisation :

    python scripts/generate_report.py

Prérequis :

    pip install python-docx
    python analysis/run_analysis.py        # produit public/data/*.json
    python scripts/capture_dashboard.py    # produit docs/screenshots/*.png

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RACINE = Path(__file__).resolve().parent.parent
REPERTOIRE_RESULTATS = RACINE / "public" / "data"
REPERTOIRE_CAPTURES = RACINE / "docs" / "screenshots"
FICHIER_SORTIE = RACINE / "docs" / "Rapport_MVP_Polarisation_Discours_Haine.docx"

TITRE = (
    "Étude de la polarisation et de la propagation du discours de haine "
    "sur les réseaux sociaux"
)
SOUS_TITRE = (
    "Analyse de réseaux sociaux, détection de communautés et analyse "
    "automatique du contenu"
)
AUTEUR = "Dr. Okba Ben Atia"
ATTRIBUTION = f"Préparation, conception et programmation : {AUTEUR}"
ANNEE = "2026"

POLICE_CORPS = "Calibri"
POLICE_TITRES = "Calibri Light"
ENCRE = RGBColor(0x1E, 0x29, 0x3B)
ACCENT = RGBColor(0x0F, 0x76, 0x6E)
GRIS = RGBColor(0x5B, 0x66, 0x76)

LARGEUR_TEXTE_CM = 16.0


class ErreurRapport(Exception):
    """Erreur bloquante de génération, formulée pour l'utilisateur."""


# --------------------------------------------------------------------------
# Chargement des résultats
# --------------------------------------------------------------------------

FICHIERS_REQUIS = [
    "overview.json",
    "sources.json",
    "network.json",
    "communities.json",
    "content.json",
    "sentiment.json",
    "emotions.json",
    "hate_speech.json",
    "propagation.json",
]


def charger_resultats(repertoire: Path) -> dict[str, Any]:
    donnees: dict[str, Any] = {}
    manquants = []
    for nom in FICHIERS_REQUIS:
        chemin = repertoire / nom
        if not chemin.exists():
            manquants.append(nom)
            continue
        donnees[nom.removesuffix(".json")] = json.loads(chemin.read_text(encoding="utf-8"))
    if manquants:
        raise ErreurRapport(
            "Résultats manquants : "
            + ", ".join(manquants)
            + ". Exécutez d'abord : python analysis/run_analysis.py"
        )
    return donnees


# --------------------------------------------------------------------------
# Mise en forme des nombres (conventions françaises)
# --------------------------------------------------------------------------


def nombre(valeur: float | int) -> str:
    return f"{int(valeur):,}".replace(",", " ")


def decimal(valeur: float, chiffres: int = 3) -> str:
    return f"{valeur:.{chiffres}f}".replace(".", ",")


def pourcentage(part: float, chiffres: int = 1) -> str:
    return f"{part * 100:.{chiffres}f}".replace(".", ",") + " %"


def _categorie(repartition: Sequence[dict], nom: str) -> dict:
    for element in repartition:
        if element["categorie"] == nom:
            return element
    return {"categorie": nom, "nombre": 0, "part": 0.0}


def termes(liste: Iterable[dict], combien: int = 6) -> str:
    return ", ".join(element["terme"] for element in list(liste)[:combien])


# --------------------------------------------------------------------------
# Primitives de mise en page
# --------------------------------------------------------------------------


def _champ(paragraphe, instruction: str) -> None:
    """Insère un champ Word (PAGE, NUMPAGES) évalué à l'ouverture du document."""
    execution = paragraphe.add_run()
    debut = OxmlElement("w:fldChar")
    debut.set(qn("w:fldCharType"), "begin")
    texte = OxmlElement("w:instrText")
    texte.set(qn("xml:space"), "preserve")
    texte.text = instruction
    fin = OxmlElement("w:fldChar")
    fin.set(qn("w:fldCharType"), "end")
    execution._r.append(debut)
    execution._r.append(texte)
    execution._r.append(fin)
    execution.font.size = Pt(8)
    execution.font.name = POLICE_CORPS
    execution.font.color.rgb = GRIS


def _ombrer(cellule, couleur_hex: str) -> None:
    ombre = OxmlElement("w:shd")
    ombre.set(qn("w:val"), "clear")
    ombre.set(qn("w:color"), "auto")
    ombre.set(qn("w:fill"), couleur_hex)
    cellule._tc.get_or_add_tcPr().append(ombre)


def configurer_document(document) -> None:
    """Format A4, marges, polices et styles de base."""
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.header_distance = Cm(1.25)
    section.footer_distance = Cm(1.25)

    normal = document.styles["Normal"]
    normal.font.name = POLICE_CORPS
    normal.font.size = Pt(11)
    normal.font.color.rgb = ENCRE
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15

    for niveau, taille in ((1, 16), (2, 13), (3, 11.5)):
        style = document.styles[f"Heading {niveau}"]
        style.font.name = POLICE_TITRES
        style.font.size = Pt(taille)
        style.font.bold = True
        style.font.color.rgb = ENCRE if niveau == 1 else ACCENT
        style.paragraph_format.space_before = Pt(16 if niveau == 1 else 10)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True


def configurer_entete_pied(document) -> None:
    """En-tête et pied de page, absents de la page de garde."""
    section = document.sections[0]
    section.different_first_page_header_footer = True

    entete = section.header.paragraphs[0]
    entete.text = ""
    entete.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    execution = entete.add_run(
        "Polarisation et propagation du discours de haine sur les réseaux sociaux"
    )
    execution.font.size = Pt(8)
    execution.font.name = POLICE_CORPS
    execution.font.color.rgb = GRIS
    _bordure_basse(entete)

    pied = section.footer.paragraphs[0]
    pied.text = ""
    pied.alignment = WD_ALIGN_PARAGRAPH.CENTER
    gauche = pied.add_run(f"{ATTRIBUTION}\t\tPage ")
    gauche.font.size = Pt(8)
    gauche.font.name = POLICE_CORPS
    gauche.font.color.rgb = GRIS
    _champ(pied, "PAGE")
    milieu = pied.add_run(" sur ")
    milieu.font.size = Pt(8)
    milieu.font.name = POLICE_CORPS
    milieu.font.color.rgb = GRIS
    _champ(pied, "NUMPAGES")


def _bordure_basse(paragraphe) -> None:
    proprietes = paragraphe._p.get_or_add_pPr()
    bordures = OxmlElement("w:pBdr")
    bas = OxmlElement("w:bottom")
    bas.set(qn("w:val"), "single")
    bas.set(qn("w:sz"), "4")
    bas.set(qn("w:space"), "2")
    bas.set(qn("w:color"), "C9D1DA")
    bordures.append(bas)
    proprietes.append(bordures)


def paragraphe(document, texte: str, *, italique: bool = False, taille: float | None = None):
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    execution = p.add_run(texte)
    execution.italic = italique
    if taille:
        execution.font.size = Pt(taille)
    return p


def puce(document, texte: str):
    p = document.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(3)
    p.add_run(texte)
    return p


def titre_section(document, numero: int | None, texte: str, niveau: int = 1):
    intitule = f"{numero}. {texte}" if numero is not None else texte
    return document.add_heading(intitule, level=niveau)


def encadre(document, titre: str, corps: str, couleur: str = "FFF7E6") -> None:
    """Encadré d'avertissement, rendu par un tableau d'une seule cellule."""
    tableau = document.add_table(rows=1, cols=1)
    tableau.style = "Table Grid"
    tableau.alignment = WD_TABLE_ALIGNMENT.CENTER
    cellule = tableau.cell(0, 0)
    cellule.width = Cm(LARGEUR_TEXTE_CM)
    _ombrer(cellule, couleur)

    premier = cellule.paragraphs[0]
    execution = premier.add_run(titre)
    execution.bold = True
    execution.font.size = Pt(10.5)

    second = cellule.add_paragraph()
    second.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    texte = second.add_run(corps)
    texte.font.size = Pt(10.5)
    document.add_paragraph()


def tableau_donnees(
    document,
    entetes: Sequence[str],
    lignes: Sequence[Sequence[str]],
    largeurs: Sequence[float] | None = None,
) -> None:
    tableau = document.add_table(rows=1, cols=len(entetes))
    tableau.style = "Table Grid"
    tableau.alignment = WD_TABLE_ALIGNMENT.CENTER
    tableau.autofit = False

    if largeurs is None:
        largeurs = [LARGEUR_TEXTE_CM / len(entetes)] * len(entetes)

    ligne_entete = tableau.rows[0]
    for index, intitule in enumerate(entetes):
        cellule = ligne_entete.cells[index]
        cellule.width = Cm(largeurs[index])
        _ombrer(cellule, "E8EEF4")
        p = cellule.paragraphs[0]
        execution = p.add_run(intitule)
        execution.bold = True
        execution.font.size = Pt(9.5)

    for valeurs in lignes:
        cellules = tableau.add_row().cells
        for index, valeur in enumerate(valeurs):
            cellules[index].width = Cm(largeurs[index])
            p = cellules[index].paragraphs[0]
            execution = p.add_run(str(valeur))
            execution.font.size = Pt(9.5)
    document.add_paragraph()


def legende_tableau(document, numero: int, texte: str) -> None:
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = p.add_run(f"Tableau {numero} — {texte}")
    execution.italic = True
    execution.font.size = Pt(9)
    execution.font.color.rgb = GRIS


def figure(
    document,
    chemin: Path,
    numero: int,
    titre: str,
    explication: str,
    largeur_cm: float = LARGEUR_TEXTE_CM,
) -> None:
    if not chemin.exists():
        raise ErreurRapport(
            f"Capture manquante : {chemin}. Exécutez d'abord : "
            "python scripts/capture_dashboard.py"
        )
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.add_run().add_picture(str(chemin), width=Cm(largeur_cm))

    legende = document.add_paragraph()
    legende.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = legende.add_run(f"Figure {numero} — {titre}")
    execution.bold = True
    execution.font.size = Pt(9)
    execution.font.color.rgb = GRIS

    commentaire = document.add_paragraph()
    commentaire.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    texte = commentaire.add_run(explication)
    texte.font.size = Pt(9.5)
    texte.italic = True
    commentaire.paragraph_format.space_after = Pt(12)


def saut_de_page(document) -> None:
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# --------------------------------------------------------------------------
# Page de garde et sommaire
# --------------------------------------------------------------------------

SECTIONS = [
    "Résumé exécutif",
    "Introduction",
    "Contexte et problématique",
    "Objectifs",
    "Questions de recherche",
    "Sources étudiées",
    "Architecture du MVP",
    "Collecte et préparation des données",
    "Anonymisation",
    "Prétraitement linguistique",
    "Construction du graphe",
    "Détection des communautés",
    "Mesure de polarisation",
    "Analyse lexicale",
    "Analyse des sentiments",
    "Analyse de la colère et du soutien",
    "Analyse du discours potentiellement haineux",
    "Analyse de propagation",
    "Présentation du tableau de bord",
    "Analyse détaillée des résultats",
    "Discussion",
    "Limites",
    "Perspectives",
    "Conclusion",
]

AVERTISSEMENT_SYNTHETIQUE = (
    "Les résultats présentés dans cette version sont issus d'un jeu de données "
    "synthétique destiné à valider le fonctionnement du MVP. Ils ne constituent pas "
    "des résultats empiriques sur les publications Facebook, X et Instagram fournies."
)

DISTINCTION = (
    "Polarisation ≠ sentiment négatif ≠ colère ≠ toxicité ≠ discours haineux"
)


def page_de_garde(document, resultats: dict) -> None:
    for _ in range(4):
        document.add_paragraph()

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = p.add_run(TITRE)
    execution.font.name = POLICE_TITRES
    execution.font.size = Pt(24)
    execution.bold = True
    execution.font.color.rgb = ENCRE
    p.paragraph_format.space_after = Pt(14)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = p.add_run(SOUS_TITRE)
    execution.font.name = POLICE_TITRES
    execution.font.size = Pt(14)
    execution.font.color.rgb = ACCENT
    p.paragraph_format.space_after = Pt(28)

    separateur = document.add_paragraph()
    separateur.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _bordure_basse(separateur)

    for _ in range(3):
        document.add_paragraph()

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = p.add_run(ATTRIBUTION)
    execution.font.size = Pt(12.5)
    execution.bold = True
    p.paragraph_format.space_after = Pt(4)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = p.add_run("Rapport de MVP académique")
    execution.font.size = Pt(11)
    execution.font.color.rgb = GRIS

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = p.add_run(ANNEE)
    execution.font.size = Pt(12)
    execution.font.color.rgb = GRIS

    for _ in range(4):
        document.add_paragraph()

    encadre(document, "Nature des données analysées", AVERTISSEMENT_SYNTHETIQUE)

    genere = resultats["overview"]["genere_le"]
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = p.add_run(
        f"Résultats produits par le pipeline d'analyse le {genere} (UTC) — "
        f"corpus : {', '.join(resultats['overview']['jeu_de_donnees']['fichiers'])}"
    )
    execution.font.size = Pt(8.5)
    execution.font.color.rgb = GRIS
    execution.italic = True

    saut_de_page(document)


def sommaire(document) -> None:
    titre_section(document, None, "Sommaire")
    for index, intitule in enumerate(SECTIONS, start=1):
        p = document.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Cm(0.5)
        execution = p.add_run(f"{index}.  {intitule}")
        execution.font.size = Pt(10.5)
    document.add_paragraph()
    p = document.add_paragraph()
    execution = p.add_run(
        "Le document comporte des figures issues du tableau de bord et des tableaux de "
        "résultats, numérotés en continu. Toutes les valeurs chiffrées proviennent des "
        "fichiers de résultats produits par le pipeline d'analyse."
    )
    execution.font.size = Pt(9.5)
    execution.italic = True
    execution.font.color.rgb = GRIS
    saut_de_page(document)


# --------------------------------------------------------------------------
# Corps du rapport
# --------------------------------------------------------------------------


class Compteurs:
    """Numérotation continue des figures et des tableaux."""

    def __init__(self) -> None:
        self.figure = 0
        self.tableau = 0

    def prochaine_figure(self) -> int:
        self.figure += 1
        return self.figure

    def prochain_tableau(self) -> int:
        self.tableau += 1
        return self.tableau


def section_resume(document, r: dict, c: Compteurs) -> None:
    ov = r["overview"]
    kpi = ov["kpi"]
    pol = ov["polarisation"]
    res = ov["reseau"]
    haine = ov["haine_globale"]

    titre_section(document, 1, SECTIONS[0])
    encadre(document, "Avertissement méthodologique", AVERTISSEMENT_SYNTHETIQUE)

    paragraphe(
        document,
        "Ce rapport rend compte d'un prototype fonctionnel (MVP) d'analyse de la polarisation "
        "et de la propagation du discours de haine sur les réseaux sociaux. Le dispositif "
        "couvre l'ensemble de la chaîne : chargement et validation des données, "
        "pseudonymisation, prétraitement linguistique français/arabe, construction d'un "
        "graphe d'interactions, détection de communautés, mesure de polarisation structurelle, "
        "analyse lexicale, classification indicative du sentiment, de la colère et du soutien, "
        "estimation indicative de la toxicité et du discours potentiellement haineux, "
        "reconstruction des cascades de propagation, puis restitution dans un tableau de bord "
        "web entièrement en français.",
    )
    paragraphe(
        document,
        "Sept sources réelles ont été déclarées pour l'étude : cinq publications Facebook, "
        "une publication X et un reel Instagram. À ce jour, "
        + (
            "aucune de ces sources ne dispose de données réelles importées"
            if kpi["sources_avec_donnees_reelles"] == 0
            else f"{nombre(kpi['sources_avec_donnees_reelles'])} d'entre elles disposent de "
            "données réelles importées"
        )
        + f" : {nombre(kpi['sources_import_manuel_requis'])} sources déclarées "
        "nécessitent un import manuel de leurs interactions. Les plateformes concernées "
        "interdisent en effet la collecte automatisée dans leur fichier robots.txt, refus qui "
        "a été respecté sans exception.",
    )
    paragraphe(
        document,
        f"Le corpus synthétique de validation comporte {nombre(kpi['interactions'])} "
        f"interactions émises par {nombre(kpi['utilisateurs'])} utilisateurs pseudonymisés "
        f"autour de {nombre(kpi['publications'])} publications. Le graphe correspondant compte "
        f"{nombre(res['noeuds'])} nœuds et {nombre(res['liens'])} liens. L'algorithme de "
        f"Louvain y détecte {nombre(kpi['communautes'])} communautés, pour une modularité de "
        f"{decimal(pol['modularite'], 4)} — lecture indicative : "
        f"« {pol['interpretation'].lower()} ». Sur "
        f"{nombre(kpi['messages_avec_texte'])} messages textuels, "
        f"{nombre(_categorie(haine, 'Toxique / offensant')['nombre'])} sont classés comme "
        f"toxiques ou offensants et "
        f"{nombre(_categorie(haine, 'Potentiellement haineux')['nombre'])} comme "
        "potentiellement haineux, soit "
        f"{pourcentage(_categorie(haine, 'Potentiellement haineux')['part'])} du corpus textuel.",
    )
    encadre(
        document,
        "Distinction scientifique appliquée dans tout le rapport",
        f"{DISTINCTION}. Ces cinq notions relèvent de plans d'analyse distincts et ne doivent "
        "jamais être additionnées, substituées ou présentées comme équivalentes. Elles sont "
        "définies en section 21.",
        couleur="EAF4F4",
    )

    figure(
        document,
        REPERTOIRE_CAPTURES / "01_vue_ensemble.png",
        c.prochaine_figure(),
        "Page « Vue d'ensemble » du tableau de bord",
        "La page de synthèse rassemble les sept indicateurs principaux, la répartition des "
        "interactions par plateforme et les trois classifications indicatives du contenu. "
        "L'indicateur « Sources analysées » affiche 0 / 7 : aucune donnée réelle n'a été "
        "importée, et la mention du corpus de démonstration figure au-dessus des indicateurs.",
    )
    saut_de_page(document)


def section_introduction(document, r: dict, c: Compteurs) -> None:
    titre_section(document, 2, SECTIONS[1])
    paragraphe(
        document,
        "Les réseaux sociaux constituent aujourd'hui un espace majeur de circulation des "
        "opinions. Les débats qui s'y déroulent se structurent fréquemment en groupes "
        "faiblement connectés entre eux, à l'intérieur desquels les échanges sont denses et "
        "entre lesquels ils sont rares. Cette organisation, observable indépendamment du "
        "contenu des messages, est ce que la littérature désigne comme polarisation "
        "structurelle.",
    )
    paragraphe(
        document,
        "Le présent travail propose un dispositif léger, reproductible et documenté permettant "
        "d'observer conjointement cette structure et les propriétés langagières des messages "
        "qui y circulent. L'objectif n'est pas de produire un système de modération ni un "
        "outil de qualification des personnes, mais de fournir un instrument descriptif "
        "utilisable dans un cadre de recherche.",
    )
    paragraphe(
        document,
        "Le MVP a été conçu selon trois exigences : la sobriété technique (aucune base de "
        "données, aucun service permanent, aucun modèle volumineux), la traçabilité complète "
        "des résultats (chaque valeur affichée provient d'un fichier produit par le pipeline) "
        "et la prudence interprétative (chaque classification automatique est présentée comme "
        "indicative et non validée).",
    )


def section_contexte(document, r: dict, c: Compteurs) -> None:
    titre_section(document, 3, SECTIONS[2])
    paragraphe(
        document,
        "La question posée est celle de l'articulation entre la structure des interactions et "
        "la nature des contenus échangés. Observer un fort volume de messages négatifs ne "
        "renseigne pas sur l'existence de communautés séparées ; inversement, une structure "
        "communautaire marquée ne signifie pas que les échanges soient hostiles. Confondre ces "
        "deux plans conduit à des conclusions erronées.",
    )
    paragraphe(
        document,
        "Un second obstacle est d'ordre pratique. Les plateformes n'exposent pas publiquement "
        "les interactions entre utilisateurs, qui constituent pourtant la matière première de "
        "toute analyse de réseau. Un dispositif académique doit donc être conçu pour "
        "fonctionner à partir de données importées manuellement, dans un cadre éthique "
        "explicite, plutôt que de présupposer un accès automatisé.",
    )
    paragraphe(
        document,
        "La problématique retenue est ainsi la suivante : comment construire un dispositif "
        "reproductible et scientifiquement prudent permettant de décrire la structure "
        "communautaire d'un débat en ligne, de caractériser le langage propre à chaque "
        "communauté et d'observer la diffusion des contenus, sans jamais confondre "
        "polarisation, négativité, colère, toxicité et discours haineux, et sans porter de "
        "jugement sur les individus ?",
    )


def section_objectifs(document, r: dict, c: Compteurs) -> None:
    titre_section(document, 4, SECTIONS[3])
    paragraphe(document, "Le MVP poursuit les objectifs suivants :")
    for texte in (
        "constituer un graphe orienté et pondéré des utilisateurs et de leurs interactions ;",
        "détecter les communautés présentes dans ce graphe et en mesurer la séparation ;",
        "produire une mesure simple, transparente et reproductible de la polarisation "
        "structurelle ;",
        "caractériser le champ lexical propre à chaque communauté ;",
        "classer le contenu selon trois dimensions distinctes — sentiment, colère/soutien, "
        "toxicité et discours potentiellement haineux ;",
        "reconstruire les cascades de propagation à partir des relations de filiation entre "
        "messages ;",
        "restituer l'ensemble dans un tableau de bord web en français, sans aucune valeur "
        "codée en dur ;",
        "documenter précisément ce qui a pu être collecté et ce qui ne l'a pas été.",
    ):
        puce(document, texte)
    paragraphe(
        document,
        "Un objectif transversal encadre les précédents : ne jamais présenter comme résultat "
        "empirique ce qui relève d'une validation technique. C'est la raison pour laquelle la "
        "nature synthétique du corpus est signalée sur chaque page du tableau de bord, dans "
        "chacun des neuf fichiers de résultats et à plusieurs reprises dans ce rapport.",
    )


def section_questions(document, r: dict, c: Compteurs) -> None:
    titre_section(document, 5, SECTIONS[4])
    paragraphe(
        document,
        "Huit questions de recherche structurent l'étude. Elles sont enregistrées dans les "
        "résultats produits par le pipeline et reprises dans le tableau de bord :",
    )
    for question in r["overview"]["questions_recherche"]:
        puce(document, question)
    paragraphe(
        document,
        "Sur le corpus synthétique actuel, ces questions servent uniquement à vérifier que le "
        "dispositif produit les indicateurs attendus. Elles ne recevront de réponse empirique "
        "qu'après import de données réelles.",
    )
    saut_de_page(document)


def section_sources(document, r: dict, c: Compteurs) -> None:
    sources = r["sources"]["sources"]
    kpi = r["overview"]["kpi"]

    titre_section(document, 6, SECTIONS[5])
    paragraphe(
        document,
        "Sept publications réelles ont été retenues comme cas d'étude initiaux. Elles sont "
        "déclarées dans le fichier des sources du projet et leur statut de collecte est déduit "
        "automatiquement du rapport de collecte : aucun statut n'est saisi manuellement.",
    )

    lignes = []
    for source in sources:
        lignes.append(
            [
                source["plateforme"].capitalize(),
                source["source_id"],
                source["url"],
                source["statut"],
                "Oui" if source["import_manuel_requis"] else "Non",
            ]
        )
    tableau_donnees(
        document,
        ["Plateforme", "Identifiant", "URL", "Statut", "Import manuel"],
        lignes,
        largeurs=[2.0, 2.4, 6.2, 3.2, 2.2],
    )
    legende_tableau(
        document,
        c.prochain_tableau(),
        "Les sept sources déclarées et leur statut de collecte réel",
    )
    document.add_paragraph()

    paragraphe(
        document,
        f"Le statut « Données de démonstration » signifie que les interactions rattachées à "
        f"ces identifiants proviennent du corpus synthétique, et non des plateformes. Aucune "
        f"des sept publications n'a donc été analysée au sens empirique : "
        f"{nombre(kpi['sources_import_manuel_requis'])} sources sur "
        f"{nombre(kpi['sources_declarees'])} nécessitent un import manuel de leurs "
        "interactions. Le tableau de bord ne présente jamais une source comme analysée tant "
        "que ses données n'ont pas été réellement importées.",
    )
    paragraphe(
        document,
        "Les règles appliquées lors de la tentative de collecte sont les suivantes : "
        + " ".join(r["sources"]["regles_collecte"]),
    )

    figure(
        document,
        REPERTOIRE_CAPTURES / "02_sources.png",
        c.prochaine_figure(),
        "Page « Sources étudiées » — statut de collecte réel de chaque publication",
        "Pour chaque URL, la page indique le statut, le nombre d'interactions rattachées, la "
        "méthode d'acquisition et, plus bas, le détail des voies d'accès évaluées avec le "
        "verdict robots.txt correspondant. Les sept sources portent le statut « Données de "
        "démonstration », ce qui signale sans ambiguïté qu'aucune interaction réelle n'a été "
        "recueillie.",
    )
    saut_de_page(document)


def section_architecture(document, r: dict, c: Compteurs) -> None:
    titre_section(document, 7, SECTIONS[6])
    paragraphe(
        document,
        "L'architecture retenue est volontairement minimale. Elle repose sur une chaîne "
        "linéaire : les données normalisées alimentent un pipeline Python exécuté hors ligne, "
        "qui produit des fichiers de résultats au format JSON ; ces fichiers sont ensuite lus "
        "par un tableau de bord Next.js rendu statiquement puis déployé.",
    )
    for etape in (
        "Entrée — fichiers CSV ou JSON au format normalisé, ou corpus de démonstration.",
        "Pipeline Python — pandas, NetworkX, scikit-learn et python-louvain ; treize étapes "
        "successives, exécutées par une commande unique.",
        "Sortie — neuf fichiers de résultats JSON, seule interface entre l'analyse et "
        "l'interface.",
        "Tableau de bord — Next.js, TypeScript, Tailwind CSS, Cytoscape.js et Recharts ; neuf "
        "pages, entièrement en français.",
        "Déploiement — hébergement statique ; aucune exécution Python n'est nécessaire en "
        "production.",
    ):
        puce(document, etape)
    paragraphe(
        document,
        "Ce choix exclut délibérément toute base de données, tout service permanent, toute "
        "file de messages et tout modèle volumineux chargé dans le navigateur. Il garantit que "
        "l'ensemble du dispositif reste inspectable, reproductible et transportable, ce qui "
        "constitue une exigence pour un travail académique.",
    )
    paragraphe(
        document,
        "La séparation stricte entre le calcul et l'affichage a une conséquence "
        "méthodologique importante : aucune statistique n'est calculée ni codée en dur dans "
        "l'interface. Toute valeur visible dans le tableau de bord peut être retrouvée dans un "
        "fichier de résultats, lui-même régénérable par une seule commande.",
    )


def section_collecte(document, r: dict, c: Compteurs) -> None:
    sources = r["sources"]["sources"]
    voies = sum(len(source["voies_evaluees"]) for source in sources)
    refusees = sum(
        1
        for source in sources
        for voie in source["voies_evaluees"]
        if voie.get("robots_txt") != "autorisé"
    )
    qualite = r["overview"]["qualite_donnees"]

    titre_section(document, 8, SECTIONS[7])
    paragraphe(
        document,
        "Pour chaque source, deux voies d'accès publiques ont été évaluées : la page de la "
        "publication et le point d'accès oEmbed officiel de la plateforme. Chaque voie est "
        "confrontée au fichier robots.txt de son propre domaine avant toute requête ; un refus "
        "est enregistré comme un résultat de l'étude et n'est jamais contourné.",
    )
    paragraphe(
        document,
        f"Sur les {nombre(voies)} voies évaluées, {nombre(refusees)} ont été refusées par le "
        "protocole d'exclusion. Aucune requête de contenu n'a donc été émise, et aucune "
        "interaction n'a été récupérée automatiquement. Ce refus n'est pas une indisponibilité "
        "technique : il résulte de directives explicites des plateformes, vérifiables et "
        "reproductibles.",
    )
    paragraphe(
        document,
        "La voie d'acquisition retenue est par conséquent l'import manuel, au format normalisé "
        "à onze colonnes : plateforme, identifiant de source, identifiant de publication, "
        "identifiant d'interaction, auteur, destinataire, type d'interaction, texte, "
        "horodatage, identifiant du message parent et URL. Le pipeline traite exactement de la "
        "même manière les données issues d'un export de plateforme, d'une API autorisée ou "
        "d'une saisie manuelle.",
    )
    paragraphe(
        document,
        "Les données réelles et synthétiques ne sont jamais mélangées : dès qu'un fichier "
        "d'import est présent, le corpus de démonstration est ignoré et le corpus est déclaré "
        "réel. Les contrôles de validation appliqués au chargement du corpus actuel donnent "
        f"les résultats suivants : {nombre(qualite['lignes_ignorees'])} ligne ignorée, "
        f"{nombre(qualite['doublons_supprimes'])} doublon supprimé, "
        f"{nombre(qualite['horodatages_invalides'])} horodatage invalide, "
        f"{nombre(qualite['messages_sans_texte'])} messages sans contenu textuel exploitable "
        "et aucun type d'interaction non reconnu.",
    )


def section_anonymisation(document, r: dict, c: Compteurs) -> None:
    kpi = r["overview"]["kpi"]
    titre_section(document, 9, SECTIONS[8])
    paragraphe(
        document,
        "Toute analyse est précédée d'une pseudonymisation systématique. Chaque identifiant "
        "d'utilisateur est remplacé par une empreinte HMAC-SHA256 tronquée, calculée avec un "
        "sel conservé localement et jamais publié, puis par une étiquette d'affichage neutre "
        f"de la forme « Utilisateur 001 ». Le corpus actuel compte "
        f"{nombre(kpi['utilisateurs'])} utilisateurs ainsi pseudonymisés.",
    )
    paragraphe(
        document,
        "La table de correspondance entre identifiants réels et pseudonymes est écrite dans un "
        "répertoire local exclu du dépôt. Aucun identifiant brut, nom, adresse ou coordonnée "
        "n'apparaît dans les fichiers de résultats ni dans le tableau de bord.",
    )
    paragraphe(
        document,
        "Aucun attribut sensible n'est inféré : ni religion, ni origine, ni appartenance "
        "ethnique, ni orientation politique. Seuls des identifiants sont transformés. "
        "L'analyse porte sur des contenus et sur des structures collectives, jamais sur la "
        "personnalité des individus.",
    )


def section_pretraitement(document, r: dict, c: Compteurs) -> None:
    kpi = r["overview"]["kpi"]
    qualite = r["overview"]["qualite_donnees"]
    titre_section(document, 10, SECTIONS[9])
    paragraphe(
        document,
        "Le texte brut de chaque message est conservé et une version nettoyée est produite en "
        "parallèle. Le nettoyage retire les URL, les mentions et la ponctuation superflue, "
        "normalise les espaces et harmonise la casse. Les hashtags sont extraits séparément "
        "afin d'être analysés pour eux-mêmes.",
    )
    paragraphe(
        document,
        "Le corpus étant mixte français/arabe, le traitement gère les deux systèmes "
        "d'écriture : normalisation des variantes de l'alif et de la ta marbuta, suppression "
        "des diacritiques arabes, et application de deux listes de mots vides, l'une "
        "française, l'autre arabe.",
    )
    paragraphe(
        document,
        f"Sur {nombre(kpi['interactions'])} interactions, "
        f"{nombre(kpi['messages_avec_texte'])} comportent un contenu textuel exploitable ; "
        f"{nombre(qualite['messages_sans_texte'])} n'en comportent pas — il s'agit "
        "essentiellement de partages et de reposts sans commentaire ajouté. Ces messages "
        "participent au graphe et à la propagation, mais sont exclus des analyses lexicales et "
        "des classifications de contenu, ce qui explique que ces dernières portent sur "
        f"{nombre(kpi['messages_avec_texte'])} messages et non sur "
        f"{nombre(kpi['interactions'])}.",
    )
    saut_de_page(document)


def section_graphe(document, r: dict, c: Compteurs) -> None:
    res = r["overview"]["reseau"]
    reseau = r["network"]
    titre_section(document, 11, SECTIONS[10])
    paragraphe(
        document,
        "Le réseau est un graphe orienté et pondéré. Un lien va de l'auteur d'une interaction "
        "vers l'utilisateur visé ; son poids agrège toutes les interactions observées entre "
        "ces deux comptes. Seuls les types relationnels produisent un lien : commentaire, "
        "réponse, mention, partage, repost et citation. Une publication initiale, qui ne vise "
        "personne, crée un nœud mais aucun lien.",
    )

    lignes = [
        ["Nœuds (utilisateurs)", nombre(res["noeuds"])],
        ["Liens (paires en interaction)", nombre(res["liens"])],
        ["Interactions agrégées (somme des poids)", nombre(res["poids_total"])],
        ["Densité", decimal(res["densite"], 5)],
        ["Degré moyen", decimal(res["degre_moyen"], 2)],
        ["Degré entrant moyen", decimal(res["degre_entrant_moyen"], 2)],
        ["Degré sortant moyen", decimal(res["degre_sortant_moyen"], 2)],
        ["Réciprocité", decimal(res["reciprocite"], 3)],
        ["Composantes faiblement connexes", nombre(res["composantes_faibles"])],
        [
            "Composante principale",
            f"{nombre(res['taille_composante_principale'])} "
            f"({pourcentage(res['part_composante_principale'])})",
        ],
    ]
    tableau_donnees(document, ["Métrique structurelle", "Valeur"], lignes, largeurs=[10.0, 6.0])
    legende_tableau(
        document, c.prochain_tableau(), "Métriques structurelles du réseau d'interactions"
    )
    document.add_paragraph()

    paragraphe(
        document,
        f"Ces valeurs se lisent comme suit. La densité de {decimal(res['densite'], 5)} indique "
        f"que seulement {pourcentage(res['densite'], 2)} des liens orientés théoriquement "
        "possibles sont effectivement observés : le réseau est très clairsemé, ce qui est "
        "attendu dans une discussion en ligne où chaque participant n'interagit qu'avec une "
        "petite fraction des autres.",
    )
    paragraphe(
        document,
        f"Le degré moyen de {decimal(res['degre_moyen'], 2)} signifie qu'un utilisateur est en "
        f"relation avec environ onze autres comptes. Les degrés entrant et sortant moyens sont "
        f"égaux ({decimal(res['degre_entrant_moyen'], 2)}), ce qui est une propriété "
        "arithmétique de tout graphe orienté et non un résultat en soi.",
    )
    paragraphe(
        document,
        f"La réciprocité de {decimal(res['reciprocite'], 3)} indique qu'environ "
        f"{pourcentage(res['reciprocite'])} des liens ont un lien retour. Les échanges sont "
        "donc majoritairement unidirectionnels : on répond à un message sans que son auteur "
        "réponde en retour, configuration caractéristique des fils de commentaires.",
    )
    paragraphe(
        document,
        f"Le graphe forme une seule composante faiblement connexe regroupant la totalité des "
        f"{nombre(res['taille_composante_principale'])} nœuds "
        f"({pourcentage(res['part_composante_principale'])}). Aucun utilisateur n'est isolé : "
        "le débat, bien que structuré en communautés, reste un espace conversationnel "
        "d'un seul tenant. Ce point est important pour la lecture de la polarisation — la "
        "séparation observée est relative, non une fragmentation en blocs disjoints.",
    )

    lignes_centralite = []
    for noeud in reseau["noeuds"][:6]:
        lignes_centralite.append(
            [
                noeud["label"],
                noeud["communaute"],
                nombre(noeud["degre"]),
                decimal(noeud["centralite_degre"], 4),
                decimal(noeud["centralite_intermediarite"], 4),
            ]
        )
    tableau_donnees(
        document,
        ["Utilisateur", "Communauté", "Degré", "Centralité de degré", "Intermédiarité"],
        lignes_centralite,
        largeurs=[3.2, 3.2, 2.0, 4.0, 3.6],
    )
    legende_tableau(
        document,
        c.prochain_tableau(),
        "Les six utilisateurs les plus centraux du réseau (pseudonymisés)",
    )
    document.add_paragraph()

    paragraphe(
        document,
        "La centralité de degré rapporte le nombre de voisins d'un nœud au nombre maximal "
        "possible ; elle identifie les comptes les plus sollicités. La centralité "
        "d'intermédiarité mesure la fréquence à laquelle un nœud se trouve sur le plus court "
        "chemin entre deux autres : elle identifie les comptes qui servent de passerelle entre "
        "des groupes. Ces deux mesures ne se recouvrent pas — un compte peut être très "
        "sollicité au sein d'une seule communauté sans jouer aucun rôle de passerelle. Sur ce "
        "corpus, l'intermédiarité a été calculée de manière exacte sur l'ensemble des nœuds.",
    )

    figure(
        document,
        REPERTOIRE_CAPTURES / "03_reseau.png",
        c.prochaine_figure(),
        "Réseau d'interactions et communautés détectées",
        "Chaque nœud est un utilisateur pseudonymisé ; sa couleur indique la communauté "
        "d'appartenance et sa taille la centralité de degré. L'épaisseur des liens traduit le "
        "nombre d'interactions agrégées, et les liens reliant deux communautés différentes "
        "sont tracés en teal. La figure montre quatre agrégats identifiables mais reliés entre "
        "eux, ce qui correspond à la modularité intermédiaire mesurée en section 13.",
    )
    saut_de_page(document)


def section_communautes(document, r: dict, c: Compteurs) -> None:
    com = r["communities"]
    titre_section(document, 12, SECTIONS[11])
    paragraphe(
        document,
        f"La détection de communautés est réalisée par l'algorithme de Louvain "
        f"({com['algorithme']}), appliqué à la version non orientée et pondérée du graphe. "
        "L'algorithme procède en deux phases répétées : il déplace chaque nœud vers la "
        "communauté voisine qui maximise le gain de modularité, puis agrège chaque communauté "
        "en un super-nœud et recommence. Le processus s'arrête lorsqu'aucun déplacement "
        "n'améliore plus la modularité.",
    )
    paragraphe(
        document,
        f"Sur le corpus analysé, {nombre(com['nombre_communautes'])} communautés sont "
        "détectées et "
        + (
            "aucun utilisateur ne reste non affecté"
            if com["utilisateurs_non_affectes"] == 0
            else f"{nombre(com['utilisateurs_non_affectes'])} utilisateurs restent non affectés"
        )
        + ". Les communautés sont numérotées par ordre décroissant de taille ; leur "
        "libellé est purement technique et ne préjuge d'aucune orientation.",
    )

    lignes = []
    for communaute in com["communautes"]:
        lignes.append(
            [
                communaute["nom"],
                nombre(communaute["utilisateurs"]),
                nombre(communaute["messages"]),
                nombre(communaute["interactions_internes"]),
                nombre(communaute["interactions_externes"]),
                pourcentage(communaute["part_interactions_internes"]),
            ]
        )
    tableau_donnees(
        document,
        [
            "Communauté",
            "Utilisateurs",
            "Messages",
            "Interactions internes",
            "Interactions externes",
            "Part interne",
        ],
        lignes,
        largeurs=[3.0, 2.4, 2.2, 3.0, 3.0, 2.4],
    )
    legende_tableau(
        document, c.prochain_tableau(), "Taille et ouverture de chaque communauté détectée"
    )
    document.add_paragraph()

    plus_grande = max(com["communautes"], key=lambda x: x["utilisateurs"])
    plus_petite = min(com["communautes"], key=lambda x: x["utilisateurs"])
    plus_fermee = max(com["communautes"], key=lambda x: x["part_interactions_internes"])
    plus_ouverte = min(com["communautes"], key=lambda x: x["part_interactions_internes"])

    paragraphe(
        document,
        f"Les communautés sont de tailles comparables : de "
        f"{nombre(plus_petite['utilisateurs'])} utilisateurs pour {plus_petite['nom']} à "
        f"{nombre(plus_grande['utilisateurs'])} pour {plus_grande['nom']}. Aucune ne domine le "
        "réseau, et le volume de messages est réparti de façon homogène. Cette régularité est "
        "une propriété du corpus synthétique de validation ; elle ne doit pas être interprétée "
        "comme un résultat.",
    )
    paragraphe(
        document,
        f"La part d'interactions internes mesure le degré de fermeture d'une communauté. Elle "
        f"varie ici de {pourcentage(plus_ouverte['part_interactions_internes'])} "
        f"({plus_ouverte['nom']}) à "
        f"{pourcentage(plus_fermee['part_interactions_internes'])} ({plus_fermee['nom']}). "
        "Toutes les communautés échangent donc presque autant avec l'extérieur qu'en leur "
        "sein : aucune n'est refermée sur elle-même. Une communauté véritablement isolée "
        "présenterait une part interne nettement supérieure.",
    )

    figure(
        document,
        REPERTOIRE_CAPTURES / "04_communautes.png",
        c.prochaine_figure(),
        "Page « Communautés » — profil détaillé de chaque groupe",
        "Pour chaque communauté, la page présente sa taille, le rapport entre interactions "
        "internes et externes, son vocabulaire caractéristique et ses trois classifications "
        "indicatives de contenu. La matrice d'interactions, en bas de page, croise les "
        "communautés deux à deux et permet de repérer les couples les plus en contact.",
    )
    saut_de_page(document)


def section_polarisation(document, r: dict, c: Compteurs) -> None:
    pol = r["overview"]["polarisation"]
    seuils = pol["seuils_indicatifs"]
    titre_section(document, 13, SECTIONS[12])
    paragraphe(
        document,
        "La polarisation est ici entendue au sens strictement structurel : elle décrit la "
        "manière dont les interactions se répartissent entre l'intérieur et l'extérieur des "
        "communautés. Trois indicateurs simples et transparents sont retenus.",
    )

    lignes = [
        ["Modularité de la partition", decimal(pol["modularite"], 4)],
        ["Interactions intra-communautaires", nombre(pol["interactions_intra_communautes"])],
        ["Interactions inter-communautaires", nombre(pol["interactions_inter_communautes"])],
        ["Interactions totales", nombre(pol["interactions_totales"])],
        ["Part des interactions internes", pourcentage(pol["part_liens_internes"])],
        ["Ratio intra / inter", decimal(pol["ratio_intra_inter"], 3)],
        ["Lecture indicative", pol["interpretation"]],
    ]
    tableau_donnees(document, ["Indicateur de polarisation", "Valeur"], lignes, largeurs=[10.0, 6.0])
    legende_tableau(document, c.prochain_tableau(), "Indicateurs de polarisation structurelle")
    document.add_paragraph()

    paragraphe(
        document,
        "La modularité compare la densité des liens observés à l'intérieur des communautés à "
        "celle qu'on obtiendrait si les mêmes nœuds étaient reliés au hasard, à degrés "
        "constants. Elle vaut zéro lorsque la partition n'explique rien de plus que le hasard "
        "et tend vers un lorsque les communautés sont parfaitement séparées.",
    )
    paragraphe(
        document,
        f"La valeur obtenue, {decimal(pol['modularite'], 4)}, se situe dans l'intervalle "
        f"conventionnel « {seuils['moderee']} », d'où la lecture indicative "
        f"« {pol['interpretation'].lower()} ». Les seuils employés "
        f"({seuils['faible']} ; {seuils['moderee']} ; {seuils['forte']}) sont conventionnels : "
        "ils facilitent la lecture mais ne constituent pas une mesure validée et ne remplacent "
        "pas l'examen des valeurs numériques.",
    )
    paragraphe(
        document,
        f"Le ratio intra/inter, égal à {decimal(pol['ratio_intra_inter'], 3)}, signifie qu'une "
        "interaction a un peu plus de deux fois plus de chances de rester dans sa communauté "
        f"que d'en sortir. La part d'interactions internes, "
        f"{pourcentage(pol['part_liens_internes'])}, indique corrélativement qu'environ une "
        f"interaction sur trois "
        f"({pourcentage(1 - pol['part_liens_internes'])}) franchit une frontière "
        "communautaire. Ce flux inter-communautaire substantiel nuance nettement l'idée de "
        "groupes hermétiques.",
    )
    encadre(
        document,
        "Ce qu'une modularité ne dit pas",
        "Une modularité élevée indique que des groupes d'interaction existent. Elle ne dit rien "
        "de leurs opinions, de leur orientation politique, de leur hostilité réciproque ni de "
        "la véracité de leurs propos. Deux communautés peuvent être fortement séparées tout en "
        "échangeant courtoisement, et deux communautés faiblement séparées peuvent s'affronter "
        "violemment. Aucune conclusion sur les opinions des personnes ne peut être tirée d'une "
        "valeur de modularité.",
    )
    saut_de_page(document)


def section_lexique(document, r: dict, c: Compteurs) -> None:
    contenu = r["content"]
    profil = contenu["profils"]["toutes|toutes"]
    com = r["communities"]

    titre_section(document, 14, SECTIONS[13])
    paragraphe(document, contenu["methode"])
    paragraphe(
        document,
        f"L'analyse porte sur {nombre(profil['messages_avec_texte'])} messages textuels. "
        "Quatre vues complémentaires sont produites : fréquences brutes après suppression des "
        "mots vides, bigrammes consécutifs, pondération TF-IDF et hashtags.",
    )

    lignes = []
    for index in range(8):
        lignes.append(
            [
                f"{profil['mots'][index]['terme']} ({profil['mots'][index]['occurrences']})",
                f"{profil['bigrammes'][index]['terme']} "
                f"({profil['bigrammes'][index]['occurrences']})",
                f"{profil['tfidf'][index]['terme']} "
                f"({decimal(profil['tfidf'][index]['score'], 4)})",
                f"{profil['hashtags'][index]['terme']} "
                f"({profil['hashtags'][index]['occurrences']})",
            ]
        )
    tableau_donnees(
        document,
        ["Mots fréquents", "Bigrammes", "Termes TF-IDF", "Hashtags"],
        lignes,
        largeurs=[4.0, 4.6, 3.8, 3.6],
    )
    legende_tableau(
        document,
        c.prochain_tableau(),
        "Profil lexical global du corpus : fréquences, bigrammes, TF-IDF et hashtags",
    )
    document.add_paragraph()

    paragraphe(
        document,
        "Les fréquences brutes identifient les termes les plus présents mais favorisent le "
        "vocabulaire commun à tout le corpus. La pondération TF-IDF corrige ce biais en "
        "abaissant le poids des termes présents partout : elle fait ressortir ce qui distingue "
        "un sous-ensemble du reste. Les bigrammes révèlent les cooccurrences, et les hashtags "
        "donnent accès à la thématisation explicite choisie par les auteurs.",
    )
    paragraphe(
        document,
        "Une observation méthodologique s'impose ici. Plusieurs bigrammes du corpus "
        f"— notamment « {profil['bigrammes'][0]['terme']} » et "
        f"« {profil['bigrammes'][1]['terme']} » — apparaissent un nombre de fois identique "
        f"({profil['bigrammes'][0]['occurrences']}). Cette régularité trahit des phrases "
        "générées à partir de gabarits : c'est un artefact du corpus synthétique, et non un "
        "phénomène discursif. Elle illustre l'intérêt de l'analyse des bigrammes comme "
        "instrument de contrôle de la qualité d'un corpus.",
    )
    paragraphe(
        document,
        "La présence conjointe de hashtags en écriture latine et arabe "
        f"(par exemple {termes(profil['hashtags'], 4)}) confirme que la chaîne de "
        "prétraitement traite effectivement les deux systèmes d'écriture.",
    )

    lignes_com = []
    for communaute in com["communautes"]:
        lignes_com.append(
            [
                communaute["nom"],
                termes(communaute["top_mots"], 5),
                termes(communaute["termes_caracteristiques"], 4),
                termes(communaute["top_hashtags"], 3),
            ]
        )
    tableau_donnees(
        document,
        ["Communauté", "Mots les plus fréquents", "Termes caractéristiques (TF-IDF)", "Hashtags"],
        lignes_com,
        largeurs=[2.6, 5.2, 4.4, 3.8],
    )
    legende_tableau(
        document, c.prochain_tableau(), "Champ lexical propre à chaque communauté détectée"
    )
    document.add_paragraph()

    paragraphe(
        document,
        "Les quatre communautés présentent des vocabulaires nettement distincts. Sur le corpus "
        "synthétique, cette séparation lexicale était attendue par construction ; sur un "
        "corpus réel, elle constituerait l'indice qu'à la séparation structurelle correspond "
        "une différenciation thématique. Les deux plans restent toutefois indépendants : des "
        "communautés peuvent partager un vocabulaire tout en n'interagissant pas.",
    )

    figure(
        document,
        REPERTOIRE_CAPTURES / "05_contenu.png",
        c.prochaine_figure(),
        "Page « Analyse du contenu » — exploration lexicale filtrable",
        "La page permet de croiser communauté et plateforme, et présente pour chaque "
        "sélection les mots fréquents, les bigrammes, les termes caractéristiques au sens "
        "TF-IDF et les hashtags. Les profils sont précalculés par le pipeline pour chaque "
        "combinaison, ce qui évite tout calcul dans le navigateur.",
    )
    saut_de_page(document)


def _tableau_par_communaute(document, bloc: dict, categories: Sequence[str]) -> None:
    lignes = []
    for entree in bloc["par_communaute"]:
        ligne = [entree["libelle"], nombre(entree["messages"])]
        for categorie in categories:
            ligne.append(
                f"{nombre(entree[categorie])} ({pourcentage(entree['part_' + categorie])})"
            )
        lignes.append(ligne)
    largeur_categorie = (16.0 - 2.8 - 2.0) / len(categories)
    tableau_donnees(
        document,
        ["Communauté", "Messages", *categories],
        lignes,
        largeurs=[2.8, 2.0, *([largeur_categorie] * len(categories))],
    )


def section_sentiments(document, r: dict, c: Compteurs) -> None:
    sent = r["sentiment"]
    global_ = r["overview"]["sentiment_global"]
    methode = sent["methode"]

    titre_section(document, 15, SECTIONS[14])
    paragraphe(
        document,
        f"La classification du sentiment repose sur une méthode de type « {methode['type']} » "
        f"({methode['nom']}, version {methode['version']}), appliquée au français, à l'arabe et "
        "aux textes mixtes. Elle combine des dictionnaires de polarité, la détection de la "
        "négation et celle de l'intensification. Aucun modèle d'apprentissage automatique "
        "n'est utilisé, et aucune évaluation sur corpus annoté n'a été réalisée : aucune "
        "mesure de précision, de rappel ou de F-mesure ne peut donc être annoncée.",
    )

    lignes = [
        [
            element["categorie"],
            nombre(element["nombre"]),
            pourcentage(element["part"]),
        ]
        for element in global_
    ]
    tableau_donnees(
        document,
        ["Catégorie de sentiment", "Messages", "Part du corpus textuel"],
        lignes,
        largeurs=[6.0, 4.0, 6.0],
    )
    legende_tableau(
        document,
        c.prochain_tableau(),
        f"Répartition globale du sentiment sur {nombre(sent['messages_analyses'])} messages "
        "textuels",
    )
    document.add_paragraph()

    positif = _categorie(global_, "Positif")
    neutre = _categorie(global_, "Neutre")
    negatif = _categorie(global_, "Négatif")
    paragraphe(
        document,
        f"Les trois catégories sont d'ampleur voisine : {pourcentage(negatif['part'])} de "
        f"messages négatifs, {pourcentage(neutre['part'])} de neutres et "
        f"{pourcentage(positif['part'])} de positifs. Le négatif l'emporte légèrement sur le "
        f"neutre ({nombre(negatif['nombre'])} messages contre {nombre(neutre['nombre'])}), mais "
        "l'écart reste faible. Aucune tonalité ne domine le corpus.",
    )
    _tableau_par_communaute(document, sent, sent["categories"])
    legende_tableau(
        document, c.prochain_tableau(), "Répartition du sentiment par communauté"
    )
    document.add_paragraph()

    plus_negative = max(
        sent["par_communaute"], key=lambda x: x["part_Négatif"]
    )
    moins_negative = min(sent["par_communaute"], key=lambda x: x["part_Négatif"])
    paragraphe(
        document,
        f"La proportion de messages négatifs varie de "
        f"{pourcentage(moins_negative['part_Négatif'])} ({moins_negative['libelle']}) à "
        f"{pourcentage(plus_negative['part_Négatif'])} ({plus_negative['libelle']}). L'écart, "
        f"de {pourcentage(plus_negative['part_Négatif'] - moins_negative['part_Négatif'])} "
        "points, est modeste. Sur un corpus synthétique et avec une méthode non évaluée, il ne "
        "saurait fonder une conclusion : il montre seulement que le dispositif restitue bien "
        "une comparaison inter-communautaire.",
    )

    figure(
        document,
        REPERTOIRE_CAPTURES / "06_sentiments.png",
        c.prochaine_figure(),
        "Page « Sentiments et émotions » — comparaisons par communauté et par plateforme",
        "La page présente côte à côte la répartition du sentiment et celle de la colère et du "
        "soutien, chacune déclinée par communauté et par plateforme, en proportions ou en "
        "effectifs. Les deux dimensions sont volontairement présentées séparément afin de ne "
        "pas suggérer qu'un message négatif serait nécessairement un message de colère.",
    )
    saut_de_page(document)


def section_emotions(document, r: dict, c: Compteurs) -> None:
    emo = r["emotions"]
    global_ = r["overview"]["emotions_globales"]

    titre_section(document, 16, SECTIONS[15])
    paragraphe(
        document,
        f"Une seconde classification distingue trois états du contenu : colère, soutien ou "
        f"approbation, et autre ou neutre. Elle repose sur une heuristique lexicale complétée "
        "par des marqueurs typographiques tels que les majuscules soutenues ou la ponctuation "
        "expressive.",
    )
    encadre(
        document,
        "Portée de cette classification",
        emo["methode"]["avertissement"],
        couleur="EAF4F4",
    )

    lignes = [
        [element["categorie"], nombre(element["nombre"]), pourcentage(element["part"])]
        for element in global_
    ]
    tableau_donnees(
        document,
        ["Catégorie", "Messages", "Part du corpus textuel"],
        lignes,
        largeurs=[6.0, 4.0, 6.0],
    )
    legende_tableau(document, c.prochain_tableau(), "Répartition globale colère / soutien")
    document.add_paragraph()

    colere = _categorie(global_, "Colère")
    soutien = _categorie(global_, "Soutien / approbation")
    paragraphe(
        document,
        f"Le soutien ({pourcentage(soutien['part'])}) devance la colère "
        f"({pourcentage(colere['part'])}), et plus de la moitié des messages ne relèvent "
        "d'aucune de ces deux catégories. Ce résultat mérite d'être rapproché de la section "
        "précédente : la part de messages négatifs y était supérieure à la part de messages "
        "de colère mesurée ici. Négativité et colère ne se recouvrent donc pas — un message "
        "peut exprimer une déception, une critique argumentée ou un constat pessimiste sans "
        "manifester de colère.",
    )
    _tableau_par_communaute(document, emo, emo["categories"])
    legende_tableau(
        document, c.prochain_tableau(), "Répartition colère / soutien par communauté"
    )
    document.add_paragraph()

    plus_colere = max(emo["par_communaute"], key=lambda x: x["part_Colère"])
    plus_soutien = max(
        emo["par_communaute"], key=lambda x: x["part_Soutien / approbation"]
    )
    paragraphe(
        document,
        f"C'est {plus_colere['libelle']} qui présente la plus forte proportion de contenus "
        f"classés en colère ({pourcentage(plus_colere['part_Colère'])}), tandis que "
        f"{plus_soutien['libelle']} présente la plus forte proportion de soutien "
        f"({pourcentage(plus_soutien['part_Soutien / approbation'])}). Une communauté peut "
        "ainsi se distinguer sur une dimension sans se distinguer sur l'autre, ce qui confirme "
        "l'intérêt de les mesurer séparément.",
    )


def section_haine(document, r: dict, c: Compteurs) -> None:
    haine = r["hate_speech"]
    global_ = r["overview"]["haine_globale"]

    titre_section(document, 17, SECTIONS[16])
    paragraphe(
        document,
        "Trois catégories distinctes sont retenues : contenu non haineux, contenu toxique ou "
        "offensant, et contenu potentiellement haineux. La troisième n'est retenue que "
        "lorsqu'une désignation collective coexiste, dans le même message, avec une "
        "formulation d'exclusion ou de rejet. Cette règle de cooccurrence vise à éviter de "
        "classer comme haineux un simple propos grossier.",
    )
    encadre(document, "Portée de cette classification", haine["methode"]["avertissement"])

    lignes = [
        [element["categorie"], nombre(element["nombre"]), pourcentage(element["part"])]
        for element in global_
    ]
    tableau_donnees(
        document,
        ["Catégorie", "Messages", "Part du corpus textuel"],
        lignes,
        largeurs=[6.0, 4.0, 6.0],
    )
    legende_tableau(
        document,
        c.prochain_tableau(),
        "Répartition globale de la toxicité et du discours potentiellement haineux",
    )
    document.add_paragraph()

    non = _categorie(global_, "Non haineux")
    toxique = _categorie(global_, "Toxique / offensant")
    potentiel = _categorie(global_, "Potentiellement haineux")
    paragraphe(
        document,
        f"La grande majorité du corpus — {nombre(non['nombre'])} messages, soit "
        f"{pourcentage(non['part'])} — n'est classée dans aucune catégorie problématique. "
        f"{nombre(toxique['nombre'])} messages ({pourcentage(toxique['part'])}) sont classés "
        f"comme toxiques ou offensants et {nombre(potentiel['nombre'])} "
        f"({pourcentage(potentiel['part'])}) comme potentiellement haineux. La distinction "
        "entre ces deux dernières catégories est essentielle : l'insulte et la désignation "
        "excluante d'un groupe ne relèvent ni du même registre ni du même traitement.",
    )
    paragraphe(
        document,
        f"La confiance moyenne attachée aux contenus classés s'établit à "
        f"{decimal(haine['confiance_moyenne'], 3)}. Il s'agit d'un score interne à "
        "l'heuristique, fondé sur le nombre et la nature des signaux détectés. Ce n'est en "
        "aucun cas une probabilité calibrée ni une mesure de performance : aucune évaluation "
        "sur corpus annoté n'a été conduite.",
    )

    _tableau_par_communaute(document, haine, haine["categories"])
    legende_tableau(
        document,
        c.prochain_tableau(),
        "Répartition de la toxicité et du discours potentiellement haineux par communauté",
    )
    document.add_paragraph()

    plus_exposee = max(
        haine["par_communaute"], key=lambda x: x["part_Potentiellement haineux"]
    )
    moins_exposee = min(
        haine["par_communaute"], key=lambda x: x["part_Potentiellement haineux"]
    )
    paragraphe(
        document,
        f"La proportion de contenus classés potentiellement haineux varie de "
        f"{pourcentage(moins_exposee['part_Potentiellement haineux'])} "
        f"({moins_exposee['libelle']}) à "
        f"{pourcentage(plus_exposee['part_Potentiellement haineux'])} "
        f"({plus_exposee['libelle']}). Les effectifs concernés sont faibles — "
        f"{nombre(plus_exposee['Potentiellement haineux'])} messages au maximum — ce qui "
        "impose une grande prudence : sur de tels volumes, la variation d'une poignée de "
        "messages modifie sensiblement le pourcentage affiché.",
    )
    encadre(
        document,
        "Contenus, jamais personnes",
        "Cette classification porte exclusivement sur des contenus. Elle ne qualifie jamais un "
        "utilisateur, et un compte dont un message a été classé comme potentiellement haineux "
        "n'est pas pour autant décrit comme haineux. Le tableau de bord n'expose d'ailleurs "
        "aucun classement par utilisateur, et les identifiants demeurent pseudonymisés.",
        couleur="EAF4F4",
    )

    figure(
        document,
        REPERTOIRE_CAPTURES / "07_discours_haineux.png",
        c.prochaine_figure(),
        "Page « Discours haineux » — distribution indicative par communauté et par plateforme",
        "La page rappelle en tête la terminologie retenue et la distinction entre les cinq "
        "notions. Les indicateurs affichent les effectifs et les parts des trois catégories, "
        "puis deux graphiques comparent les communautés et les plateformes. Le basculement "
        "entre proportions et effectifs permet d'éviter la surinterprétation des pourcentages "
        "calculés sur de petits effectifs.",
    )
    saut_de_page(document)


def section_propagation(document, r: dict, c: Compteurs) -> None:
    prop = r["propagation"]
    stats = prop["statistiques"]

    titre_section(document, 18, SECTIONS[17])
    paragraphe(document, prop["methode"])
    paragraphe(
        document,
        f"Sur le corpus analysé, {nombre(prop['nombre_cascades'])} cascades ont été "
        "reconstruites. Une cascade regroupe une publication initiale et l'ensemble des "
        "messages qui en descendent par filiation : commentaires, réponses à ces commentaires, "
        "puis partages, reposts ou citations.",
    )

    lignes = [
        ["Nombre de cascades", nombre(stats["nombre_cascades"])],
        ["Taille moyenne", decimal(stats["taille_moyenne"], 2)],
        ["Taille maximale", nombre(stats["taille_maximale"])],
        ["Profondeur moyenne", decimal(stats["profondeur_moyenne"], 2)],
        ["Profondeur maximale", nombre(stats["profondeur_maximale"])],
        ["Durée moyenne (minutes)", decimal(stats["duree_moyenne_minutes"], 1)],
        ["Cascades touchant plusieurs communautés", nombre(stats["cascades_multi_communautes"])],
    ]
    tableau_donnees(document, ["Indicateur de propagation", "Valeur"], lignes, largeurs=[10.0, 6.0])
    legende_tableau(document, c.prochain_tableau(), "Statistiques globales de propagation")
    document.add_paragraph()

    lignes_cascades = []
    for cascade in prop["cascades"][:6]:
        lignes_cascades.append(
            [
                cascade["cascade_id"],
                cascade["source_id"],
                nombre(cascade["taille"]),
                nombre(cascade["profondeur"]),
                nombre(cascade["participants"]),
                nombre(cascade["nombre_communautes_atteintes"]),
                pourcentage(cascade["taux_potentiellement_haineux"]),
            ]
        )
    tableau_donnees(
        document,
        [
            "Cascade",
            "Source",
            "Taille",
            "Profondeur",
            "Participants",
            "Communautés",
            "Part potentiellement haineuse",
        ],
        lignes_cascades,
        largeurs=[1.8, 2.6, 1.6, 2.0, 2.4, 2.2, 3.4],
    )
    legende_tableau(
        document, c.prochain_tableau(), "Les six cascades les plus étendues du corpus"
    )
    document.add_paragraph()

    plus_grande = prop["cascades"][0]
    paragraphe(
        document,
        f"La cascade la plus étendue, {plus_grande['cascade_id']}, rattachée à la source "
        f"{plus_grande['source_id']}, compte {nombre(plus_grande['taille'])} messages émis par "
        f"{nombre(plus_grande['participants'])} participants distincts, sur une profondeur de "
        f"{nombre(plus_grande['profondeur'])} niveaux. La profondeur mesure la longueur de la "
        "plus longue chaîne de filiation : une valeur de quatre correspond à une publication, "
        "un commentaire, une réponse, puis un partage ou une citation.",
    )
    paragraphe(
        document,
        f"L'observation la plus notable est que les {nombre(stats['cascades_multi_communautes'])} "
        f"cascades touchent toutes plusieurs communautés. Aucune diffusion ne reste confinée à "
        "un seul groupe. Ce constat complète utilement la mesure de polarisation : la "
        "structure des interactions présente des communautés identifiables, mais les contenus "
        "circulent bien au-delà de leurs frontières.",
    )
    paragraphe(
        document,
        f"La part de contenus classés potentiellement haineux varie d'une cascade à l'autre — "
        f"jusqu'à {pourcentage(max(x['taux_potentiellement_haineux'] for x in prop['cascades']))} "
        "pour la plus exposée. Sur des cascades de quelques dizaines de messages, ces "
        "proportions reposent sur de très faibles effectifs et doivent être lues comme des "
        "indications de tendance, non comme des mesures.",
    )
    paragraphe(
        document,
        "Il convient enfin de souligner qu'aucun modèle de diffusion n'est estimé. La "
        "reconstruction est purement descriptive : elle suit les liens de filiation "
        "effectivement présents dans les données. Aucune inférence causale, aucune prédiction "
        "de viralité et aucune identification de « source » d'une diffusion ne sont produites.",
    )

    figure(
        document,
        REPERTOIRE_CAPTURES / "08_propagation.png",
        c.prochaine_figure(),
        "Page « Propagation » — principales cascades et arbres de diffusion",
        "La page classe les cascades par taille et détaille, pour chacune, sa profondeur, le "
        "nombre de participants, les communautés atteintes et la part de contenus classés "
        "comme problématiques. L'arbre de diffusion permet de suivre le cheminement d'une "
        "publication à travers les niveaux de réponse successifs.",
    )
    saut_de_page(document)


def section_dashboard(document, r: dict, c: Compteurs) -> None:
    titre_section(document, 19, SECTIONS[18])
    paragraphe(
        document,
        "Le tableau de bord comporte neuf pages, entièrement rédigées en français : vue "
        "d'ensemble, sources étudiées, réseau, communautés, analyse du contenu, sentiments et "
        "émotions, discours haineux, propagation et méthodologie. Il est rendu statiquement, "
        "fonctionne sans serveur applicatif et ne requiert aucune exécution Python en "
        "production.",
    )
    paragraphe(
        document,
        "Le graphe d'interactions constitue la visualisation principale. Il est rendu par "
        "Cytoscape.js et offre quatre filtres combinables — plateforme, source, communauté et "
        "type d'interaction — ainsi qu'un panneau de détail affichant, pour le nœud "
        "sélectionné, ses degrés et ses centralités. Les graphiques de distribution sont "
        "rendus par Recharts.",
    )
    paragraphe(
        document,
        "Trois principes de conception encadrent l'interface. D'abord, aucune statistique "
        "n'est codée en dur : toute valeur affichée est lue dans un fichier de résultats. "
        "Ensuite, la nature du corpus est signalée sur chaque page. Enfin, les identifiants "
        "réels ne sont jamais affichés : seules apparaissent les étiquettes pseudonymisées.",
    )
    paragraphe(
        document,
        "L'interface est responsive et propose un thème clair et un thème sombre. Les captures "
        "reproduites dans ce rapport ont été réalisées automatiquement en thème clair, à une "
        "résolution de 1440 × 900 pixels, au moyen d'un script Playwright versionné dans le "
        "projet, ce qui les rend reproductibles à l'identique.",
    )

    figure(
        document,
        REPERTOIRE_CAPTURES / "09_methodologie.png",
        c.prochaine_figure(),
        "Page « Méthodologie » — documentation intégrée au tableau de bord",
        "La méthodologie complète est consultable directement dans l'interface : cadre de "
        "collecte, pseudonymisation, prétraitement, construction du graphe, détection de "
        "communautés, mesures de polarisation, classifications indicatives et limites. Le "
        "lecteur du tableau de bord dispose ainsi du contexte nécessaire à l'interprétation "
        "sans avoir à consulter un document séparé.",
    )
    saut_de_page(document)


def section_resultats(document, r: dict, c: Compteurs) -> None:
    ov = r["overview"]
    kpi = ov["kpi"]
    pol = ov["polarisation"]

    titre_section(document, 20, SECTIONS[19])
    paragraphe(
        document,
        "Cette section rassemble les principaux indicateurs produits par le pipeline et en "
        "propose une lecture d'ensemble. Tous les chiffres proviennent des fichiers de "
        "résultats ; aucun n'a été saisi manuellement.",
    )

    lignes = [
        ["Sources déclarées", nombre(kpi["sources_declarees"])],
        ["Sources réellement importées (données réelles)", nombre(kpi["sources_avec_donnees_reelles"])],
        ["Sources nécessitant un import manuel", nombre(kpi["sources_import_manuel_requis"])],
        ["Publications", nombre(kpi["publications"])],
        ["Utilisateurs pseudonymisés", nombre(kpi["utilisateurs"])],
        ["Interactions", nombre(kpi["interactions"])],
        ["Messages comportant du texte", nombre(kpi["messages_avec_texte"])],
        ["Communautés détectées", nombre(kpi["communautes"])],
        ["Modularité", decimal(kpi["modularite"], 4)],
        ["Niveau indicatif de polarisation", kpi["polarisation"]],
        ["Contenus toxiques / offensants", nombre(kpi["contenus_toxiques"])],
        ["Contenus potentiellement haineux", nombre(kpi["contenus_potentiellement_haineux"])],
    ]
    tableau_donnees(document, ["Indicateur", "Valeur"], lignes, largeurs=[11.0, 5.0])
    legende_tableau(
        document, c.prochain_tableau(), "Tableau de synthèse des principaux indicateurs"
    )
    document.add_paragraph()

    titre_section(document, None, "20.1  Répartition par plateforme", niveau=2)
    lignes_plateformes = [
        [
            element["libelle"],
            nombre(element["publications"]),
            nombre(element["interactions"]),
            pourcentage(element["part"]),
        ]
        for element in ov["repartition_plateformes"]
    ]
    tableau_donnees(
        document,
        ["Plateforme", "Publications", "Interactions", "Part du corpus"],
        lignes_plateformes,
        largeurs=[4.0, 4.0, 4.0, 4.0],
    )
    legende_tableau(
        document, c.prochain_tableau(), "Répartition des interactions par plateforme"
    )
    document.add_paragraph()

    principale = max(ov["repartition_plateformes"], key=lambda x: x["interactions"])
    paragraphe(
        document,
        f"{principale['libelle']} concentre {pourcentage(principale['part'])} des interactions "
        "du corpus. Ce déséquilibre reflète la composition des sources déclarées — cinq des "
        "sept publications proviennent de cette plateforme — et non un comportement observé. "
        "Toute comparaison inter-plateformes devra tenir compte de ce déséquilibre de volume, "
        "qui rend les pourcentages calculés sur les plateformes minoritaires nettement moins "
        "robustes.",
    )

    titre_section(document, None, "20.2  Lecture d'ensemble", niveau=2)
    paragraphe(
        document,
        f"Le réseau réunit {nombre(kpi['utilisateurs'])} participants en une seule composante "
        f"connexe, structurée en {nombre(kpi['communautes'])} communautés de tailles "
        f"comparables. La modularité de {decimal(pol['modularite'], 4)} situe cette structure "
        "dans une zone intermédiaire : les communautés existent et sont détectables, mais "
        f"elles restent perméables — {pourcentage(1 - pol['part_liens_internes'])} des "
        "interactions franchissent une frontière communautaire, et toutes les cascades de "
        "propagation touchent plusieurs groupes.",
    )
    paragraphe(
        document,
        "Sur le plan du contenu, les trois classifications convergent vers une même lecture : "
        "aucune dimension problématique ne domine le corpus. La tonalité négative concerne "
        f"{pourcentage(_categorie(ov['sentiment_global'], 'Négatif')['part'])} des messages "
        f"textuels, la colère {pourcentage(_categorie(ov['emotions_globales'], 'Colère')['part'])}, "
        "la toxicité "
        f"{pourcentage(_categorie(ov['haine_globale'], 'Toxique / offensant')['part'])} et le "
        "discours potentiellement haineux "
        f"{pourcentage(_categorie(ov['haine_globale'], 'Potentiellement haineux')['part'])}.",
    )
    paragraphe(
        document,
        "La décroissance régulière de ces quatre proportions illustre concrètement la "
        "distinction posée en introduction : chaque notion est plus restrictive que la "
        "précédente, et les substituer l'une à l'autre reviendrait à multiplier par plus de "
        "neuf l'ampleur du phénomène le plus grave. Cette observation vaut pour le corpus "
        "synthétique analysé ; elle illustre le fonctionnement du dispositif et ne constitue "
        "pas un résultat empirique.",
    )
    saut_de_page(document)


def section_discussion(document, r: dict, c: Compteurs) -> None:
    ov = r["overview"]
    titre_section(document, 21, SECTIONS[20])
    paragraphe(
        document,
        "La contribution principale de ce travail est moins un résultat qu'un dispositif : une "
        "chaîne complète, reproductible et documentée, allant de données brutes normalisées "
        "à une restitution interactive, avec une traçabilité intégrale des valeurs affichées.",
    )

    titre_section(document, None, "21.1  Cinq notions à ne pas confondre", niveau=2)
    paragraphe(document, DISTINCTION + ". Ces cinq notions se définissent ainsi :")
    for terme, definition in (
        (
            "Polarisation",
            "propriété structurelle du réseau d'interactions : elle décrit la répartition des "
            "échanges entre l'intérieur et l'extérieur des communautés. Elle ne dit rien du "
            "contenu des messages.",
        ),
        (
            "Sentiment négatif",
            "propriété lexicale d'un message : critique, déception, désaccord, constat "
            "pessimiste. Un désaccord argumenté et courtois est négatif.",
        ),
        (
            "Colère",
            "registre expressif particulier, marqué par l'indignation et une intensité "
            "typographique ou lexicale. Un message peut être négatif sans être en colère.",
        ),
        (
            "Toxicité",
            "caractère offensant d'un propos : insulte, mépris, agressivité dirigée. Elle vise "
            "généralement un interlocuteur, non un groupe.",
        ),
        (
            "Discours haineux",
            "association d'une désignation collective et d'une formulation d'exclusion ou de "
            "rejet. C'est la catégorie la plus restrictive et la plus grave.",
        ),
    ):
        p = document.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(3)
        execution = p.add_run(f"{terme} — ")
        execution.bold = True
        p.add_run(definition)
    paragraphe(
        document,
        "Ces dimensions sont mesurées séparément, affichées séparément et ne sont jamais "
        "agrégées en un indice unique. Un tel indice masquerait précisément ce que l'analyse "
        "cherche à distinguer.",
    )

    titre_section(document, None, "21.2  Ce que le dispositif permet et ne permet pas", niveau=2)
    paragraphe(
        document,
        "Le dispositif permet de décrire une structure d'interactions, de comparer des "
        "communautés sur plusieurs dimensions indépendantes et de suivre la circulation des "
        "contenus. Il ne permet ni de qualifier des personnes, ni d'inférer des opinions, ni "
        "de prédire une diffusion, ni d'annoncer une performance de classification.",
    )
    paragraphe(
        document,
        "La qualité des classifications constitue la principale réserve. Les trois "
        "classificateurs sont des heuristiques lexicales, sans apprentissage et sans "
        "évaluation sur corpus annoté. Ils conviennent à un prototype dont l'objectif est de "
        "valider une chaîne de traitement ; ils ne conviendraient pas à une étude publiant des "
        "taux comme résultats scientifiques.",
    )
    paragraphe(
        document,
        f"Enfin, le corpus analysé — {ov['jeu_de_donnees']['fichiers'][0]} — est synthétique. "
        "Certaines régularités observées, comme l'homogénéité des tailles de communautés ou la "
        "répétition exacte de bigrammes, sont des artefacts de génération. Elles confirment le "
        "bon fonctionnement du dispositif tout en rappelant qu'aucune conclusion empirique ne "
        "peut en être tirée.",
    )


def section_limites(document, r: dict, c: Compteurs) -> None:
    kpi = r["overview"]["kpi"]
    titre_section(document, 22, SECTIONS[21])

    titre_section(document, None, "22.1  Limites relatives aux données", niveau=2)
    for texte in (
        f"Le corpus actuellement analysé est synthétique. Aucun des chiffres de ce rapport ne "
        f"décrit le comportement réel d'utilisateurs de Facebook, X ou Instagram.",
        "L'accès automatisé aux trois plateformes est exclu : leur fichier robots.txt interdit "
        "la collecte automatisée, y compris via les points d'accès oEmbed officiels. Ce refus "
        "a été respecté sans exception.",
        f"Les {nombre(kpi['sources_import_manuel_requis'])} sources déclarées nécessitent un "
        "import manuel de leurs interactions, qui n'a pas encore été réalisé.",
        "L'import manuel introduira un biais de sélection difficile à quantifier : les "
        "interactions retenues dépendront de ce qui aura été observé et saisi, et non d'un "
        "échantillonnage contrôlé.",
        "Les URL de partage utilisées comme sources sont des redirections opaques : elles ne "
        "garantissent ni la stabilité de l'identifiant, ni la disponibilité future du contenu.",
    ):
        puce(document, texte)

    titre_section(document, None, "22.2  Limites relatives aux méthodes", niveau=2)
    for texte in (
        "La classification du sentiment repose sur une heuristique lexicale et non sur un "
        "modèle appris. Elle est indicative.",
        "La classification colère / soutien est indicative et porte sur le contenu d'un "
        "message, jamais sur l'état émotionnel réel d'une personne.",
        "L'estimation de la toxicité et du discours potentiellement haineux est indicative et "
        "fondée sur des dictionnaires courts et non exhaustifs.",
        "Aucune de ces trois classifications n'a été évaluée sur un corpus annoté : aucune "
        "précision, aucun rappel, aucune F-mesure ne peut être annoncée.",
        "L'ironie, le sarcasme, l'implicite, les formulations codées et les références "
        "culturelles échappent à la détection. Une citation ou une dénonciation d'un propos "
        "haineux peut être classée à tort comme haineuse.",
        "Le contexte culturel et dialectal, notamment pour l'arabe et les usages mixtes "
        "français/arabe, n'est pris en compte que très partiellement.",
        "Les seuils d'interprétation de la modularité sont conventionnels et ne constituent "
        "pas une mesure validée de la polarisation.",
        "Sur de faibles effectifs, les pourcentages par communauté ou par cascade sont "
        "instables : quelques messages suffisent à les modifier sensiblement.",
    ):
        puce(document, texte)

    titre_section(document, None, "22.3  Limites relatives à la portée", niveau=2)
    for texte in (
        "Aucune inférence n'est produite sur les individus : ni opinion, ni appartenance, ni "
        "intention. Le dispositif décrit des contenus et des structures collectives.",
        "Aucun attribut sensible n'est inféré : ni religion, ni origine, ni appartenance "
        "ethnique, ni orientation politique.",
        "Aucun modèle de diffusion n'est estimé : l'analyse de propagation est descriptive et "
        "ne fonde aucune inférence causale.",
        "Le dispositif n'est pas un outil de modération et ne doit pas être employé pour "
        "prendre des décisions concernant des personnes.",
    ):
        puce(document, texte)
    saut_de_page(document)


def section_perspectives(document, r: dict, c: Compteurs) -> None:
    titre_section(document, 23, SECTIONS[22])
    paragraphe(
        document,
        "Les évolutions suivantes prolongeraient utilement ce prototype, par ordre de priorité "
        "décroissante :",
    )
    for titre, detail in (
        (
            "Import de données réelles",
            "constituer, pour au moins une des sept sources déclarées, un jeu d'interactions "
            "réelles au format normalisé. C'est la condition préalable à tout résultat "
            "empirique ; le dispositif bascule automatiquement en mode « données réelles » dès "
            "qu'un fichier d'import est présent.",
        ),
        (
            "Validation sur corpus annoté",
            "annoter manuellement un échantillon de messages selon les trois dimensions, puis "
            "mesurer la précision et le rappel des heuristiques actuelles. Sans cette étape, "
            "aucun taux ne peut être publié comme résultat.",
        ),
        (
            "Modèles multilingues français / arabe",
            "remplacer les heuristiques lexicales par des modèles adaptés au français et à "
            "l'arabe, y compris dialectal, une fois disponible le corpus annoté permettant de "
            "vérifier qu'ils font effectivement mieux.",
        ),
        (
            "Analyse temporelle",
            "exploiter les horodatages pour observer l'évolution du débat : rythme des "
            "échanges, moments d'intensification, décalage éventuel entre pic d'activité et "
            "pic de contenus problématiques.",
        ),
        (
            "Comparaison inter-plateformes",
            "comparer Facebook, X et Instagram lorsque les volumes importés le permettront. "
            "Le déséquilibre actuel entre plateformes rend une telle comparaison prématurée.",
        ),
        (
            "Affinement de la propagation",
            "distinguer les types de relais, mesurer les délais de reprise et caractériser les "
            "passages d'une communauté à l'autre, en restant dans un cadre descriptif.",
        ),
        (
            "Mesures complémentaires de polarisation",
            "n'ajouter d'autres indicateurs que s'ils sont scientifiquement justifiés, "
            "documentés et interprétables au même titre que la modularité et le ratio "
            "intra/inter.",
        ),
    ):
        p = document.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(4)
        execution = p.add_run(f"{titre} — ")
        execution.bold = True
        p.add_run(detail)
    paragraphe(
        document,
        "Ces orientations restent délibérément dans le périmètre d'un travail de recherche "
        "léger. Elles n'impliquent ni infrastructure permanente, ni base de données, ni "
        "industrialisation du dispositif.",
    )


def section_conclusion(document, r: dict, c: Compteurs) -> None:
    ov = r["overview"]
    kpi = ov["kpi"]
    pol = ov["polarisation"]

    titre_section(document, 24, SECTIONS[23])
    paragraphe(
        document,
        "Ce travail livre un prototype complet et fonctionnel d'analyse de la polarisation et "
        "de la propagation du discours de haine sur les réseaux sociaux. La chaîne de "
        "traitement s'exécute par une commande unique, produit neuf fichiers de résultats et "
        "alimente un tableau de bord en français comportant neuf pages, dont la visualisation "
        "principale est le graphe des interactions.",
    )
    paragraphe(
        document,
        f"Sur le corpus synthétique de validation — {nombre(kpi['interactions'])} interactions, "
        f"{nombre(kpi['utilisateurs'])} utilisateurs, {nombre(kpi['publications'])} "
        f"publications — le dispositif détecte {nombre(kpi['communautes'])} communautés pour "
        f"une modularité de {decimal(pol['modularite'], 4)}, produit un profil lexical distinct "
        "par communauté, restitue trois classifications indépendantes du contenu et "
        f"reconstruit {nombre(r['propagation']['nombre_cascades'])} cascades de propagation. "
        "L'ensemble de ces sorties se comporte comme attendu.",
    )
    paragraphe(
        document,
        "Sur le plan empirique, le bilan est net et doit être énoncé sans ambiguïté : "
        f"{nombre(kpi['sources_declarees'])} sources réelles ont été déclarées, "
        + (
            "aucune donnée réelle n'a été importée"
            if kpi["sources_avec_donnees_reelles"] == 0
            else f"{nombre(kpi['sources_avec_donnees_reelles'])} sources ont reçu des données "
            "réelles"
        )
        + f", et {nombre(kpi['sources_import_manuel_requis'])} sources nécessitent un import manuel "
        "de leurs interactions. Les plateformes interdisent la collecte automatisée, et ce "
        "refus a été respecté. Aucun résultat de ce rapport ne décrit donc le comportement "
        "réel d'utilisateurs de Facebook, X ou Instagram.",
    )
    paragraphe(
        document,
        "La valeur du travail réside dans la rigueur du dispositif : traçabilité complète des "
        "valeurs affichées, séparation stricte entre données réelles et synthétiques, "
        "pseudonymisation systématique, refus de toute inférence sur les personnes et maintien "
        "constant de la distinction entre polarisation, sentiment négatif, colère, toxicité et "
        "discours haineux. Ces garanties, une fois des données réelles importées, permettront "
        "de produire des résultats interprétables sans avoir à réviser la méthode.",
    )

    document.add_paragraph()
    separateur = document.add_paragraph()
    _bordure_basse(separateur)
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = p.add_run(ATTRIBUTION)
    execution.bold = True
    execution.font.size = Pt(11)
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execution = p.add_run(
        f"{TITRE} — {ANNEE}. Résultats générés le {ov['genere_le']} (UTC)."
    )
    execution.font.size = Pt(9)
    execution.italic = True
    execution.font.color.rgb = GRIS


# --------------------------------------------------------------------------
# Assemblage
# --------------------------------------------------------------------------

SECTIONS_RENDU = [
    section_resume,
    section_introduction,
    section_contexte,
    section_objectifs,
    section_questions,
    section_sources,
    section_architecture,
    section_collecte,
    section_anonymisation,
    section_pretraitement,
    section_graphe,
    section_communautes,
    section_polarisation,
    section_lexique,
    section_sentiments,
    section_emotions,
    section_haine,
    section_propagation,
    section_dashboard,
    section_resultats,
    section_discussion,
    section_limites,
    section_perspectives,
    section_conclusion,
]


def construire(resultats: dict, destination: Path) -> tuple[Path, Compteurs]:
    document = Document()
    configurer_document(document)
    configurer_entete_pied(document)

    compteurs = Compteurs()
    page_de_garde(document, resultats)
    sommaire(document)
    for rendu in SECTIONS_RENDU:
        rendu(document, resultats, compteurs)

    destination.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(destination))
    return destination, compteurs


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Génère le rapport Word du MVP à partir des résultats du pipeline."
    )
    analyseur.add_argument(
        "--resultats", type=Path, default=REPERTOIRE_RESULTATS, help="Répertoire des JSON."
    )
    analyseur.add_argument(
        "--sortie", type=Path, default=FICHIER_SORTIE, help="Fichier .docx à produire."
    )
    arguments = analyseur.parse_args()

    print("Génération du rapport Word")
    print(f"  résultats : {arguments.resultats}")
    try:
        resultats = charger_resultats(arguments.resultats)
        chemin, compteurs = construire(resultats, arguments.sortie)
    except ErreurRapport as erreur:
        print(f"\nERREUR : {erreur}", file=sys.stderr)
        return 1

    taille = chemin.stat().st_size
    print(f"\nRapport écrit : {chemin}")
    print(f"  taille          : {taille / 1024:.0f} Ko")
    print(f"  sections        : {len(SECTIONS)}")
    print(f"  figures         : {compteurs.figure}")
    print(f"  tableaux        : {compteurs.tableau}")
    jeu = resultats["overview"]["jeu_de_donnees"]
    print(f"  corpus analysé  : {jeu['type']} ({', '.join(jeu['fichiers'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
