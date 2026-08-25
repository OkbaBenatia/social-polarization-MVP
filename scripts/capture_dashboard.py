"""Captures d'écran reproductibles du tableau de bord.

Le script pilote un navigateur Chromium (Playwright) sur une instance locale du
tableau de bord et enregistre une capture par page dans ``docs/screenshots``.

Chaque capture attend le rendu complet : fin des requêtes réseau, présence du
contenu principal, puis rendu effectif des graphiques (SVG Recharts, canvas
Cytoscape). Le thème clair est imposé afin d'obtenir des figures lisibles à
l'impression.

Utilisation :

    python scripts/capture_dashboard.py --base-url http://localhost:3001

Prérequis :

    pip install playwright && python -m playwright install chromium

Préparation, conception et programmation : Dr. Okba Ben Atia
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import Error as ErreurPlaywright
from playwright.sync_api import TimeoutError as ExpirationPlaywright
from playwright.sync_api import sync_playwright

RACINE = Path(__file__).resolve().parent.parent
REPERTOIRE_CAPTURES = RACINE / "docs" / "screenshots"

LARGEUR = 1440
HAUTEUR = 900
FACTEUR_ECHELLE = 2  # rendu net une fois l'image réduite dans le document Word.


@dataclass
class Capture:
    """Description d'une capture à réaliser."""

    fichier: str
    chemin: str
    titre: str
    graphiques: bool = True
    selecteur: str | None = None  # capture d'un élément précis plutôt que la fenêtre
    actions: list[str] = field(default_factory=list)


CAPTURES: list[Capture] = [
    Capture("01_vue_ensemble.png", "/", "Vue d'ensemble"),
    Capture("02_sources.png", "/sources", "Sources étudiées", graphiques=False),
    Capture(
        "03_reseau.png",
        "/reseau",
        "Réseau d'interactions",
        graphiques=False,
        selecteur="main section:has([role='application'])",
        actions=["recentrer"],
    ),
    Capture("04_communautes.png", "/communautes", "Communautés"),
    Capture("05_contenu.png", "/contenu", "Analyse du contenu", graphiques=False),
    Capture("06_sentiments.png", "/sentiments", "Sentiments et émotions"),
    Capture("07_discours_haineux.png", "/discours-haineux", "Discours haineux"),
    Capture("08_propagation.png", "/propagation", "Propagation"),
    Capture("09_methodologie.png", "/methodologie", "Méthodologie", graphiques=False),
]


# Surcouches injectées par le serveur de développement Next.js : elles n'appartiennent
# pas au tableau de bord et ne doivent pas apparaître dans les figures du rapport.
CSS_MASQUAGE = """
nextjs-portal,
[data-nextjs-toast],
[data-nextjs-dialog-overlay],
#__next-build-watcher { display: none !important; }
"""


def _attendre_rendu(page, capture: Capture) -> None:
    """Attend que la page soit stable et que ses visualisations soient rendues."""
    page.wait_for_load_state("networkidle")
    page.wait_for_selector("main", state="visible", timeout=30_000)
    page.add_style_tag(content=CSS_MASQUAGE)

    if capture.graphiques:
        try:
            page.wait_for_selector("svg.recharts-surface", state="visible", timeout=20_000)
        except ExpirationPlaywright:
            print(f"      (aucun graphique Recharts détecté sur {capture.chemin})")

    if capture.selecteur:
        page.wait_for_selector(capture.selecteur, state="visible", timeout=30_000)

    if "recentrer" in capture.actions:
        # Le graphe Cytoscape est dessiné sur canvas : on attend son apparition,
        # puis on demande un recadrage pour que toutes les communautés soient
        # visibles et centrées.
        page.wait_for_selector("[role='application'] canvas", state="attached", timeout=30_000)
        page.wait_for_timeout(2_500)  # stabilisation de la disposition « cose »
        bouton = page.get_by_role("button", name="Recentrer")
        if bouton.count():
            bouton.first.click()
            page.wait_for_timeout(1_200)

    # Aucun survol résiduel : la souris est éloignée et le focus relâché.
    page.mouse.move(2, 2)
    page.evaluate("() => { if (document.activeElement) document.activeElement.blur(); }")
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(600)


def capturer(base_url: str, repertoire: Path, captures: list[Capture]) -> list[Path]:
    repertoire.mkdir(parents=True, exist_ok=True)
    ecrits: list[Path] = []

    with sync_playwright() as pilote:
        navigateur = pilote.chromium.launch()
        contexte = navigateur.new_context(
            viewport={"width": LARGEUR, "height": HAUTEUR},
            device_scale_factor=FACTEUR_ECHELLE,
            color_scheme="light",
            locale="fr-FR",
            reduced_motion="reduce",
        )
        page = contexte.new_page()

        for capture in captures:
            url = base_url.rstrip("/") + capture.chemin
            print(f"  → {capture.fichier} ({url})")
            reponse = page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            if reponse is not None and reponse.status >= 400:
                raise RuntimeError(
                    f"{url} a répondu HTTP {reponse.status} : le tableau de bord "
                    "est-il bien démarré ?"
                )
            _attendre_rendu(page, capture)

            destination = repertoire / capture.fichier
            if capture.selecteur:
                page.locator(capture.selecteur).first.screenshot(path=str(destination))
            else:
                page.screenshot(path=str(destination))
            ecrits.append(destination)

        contexte.close()
        navigateur.close()
    return ecrits


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Captures d'écran du tableau de bord (Playwright)."
    )
    analyseur.add_argument(
        "--base-url",
        default="http://localhost:3001",
        help="URL de l'instance locale du tableau de bord.",
    )
    analyseur.add_argument(
        "--sortie", type=Path, default=REPERTOIRE_CAPTURES, help="Répertoire des captures."
    )
    arguments = analyseur.parse_args()

    print(f"Captures du tableau de bord — {arguments.base_url}")
    try:
        ecrits = capturer(arguments.base_url, arguments.sortie, CAPTURES)
    except (ErreurPlaywright, RuntimeError) as erreur:
        print(f"\nERREUR : {erreur}", file=sys.stderr)
        print(
            "Démarrez le tableau de bord (npm run dev) puis relancez ce script.",
            file=sys.stderr,
        )
        return 1

    print(f"\n{len(ecrits)} captures écrites dans {arguments.sortie}")
    for chemin in ecrits:
        taille = chemin.stat().st_size
        print(f"  ✓ {chemin.name:26} {taille / 1024:7.1f} Ko")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
