"use client";

import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import { useEffect, useMemo, useRef, useState } from "react";

import { couleurCommunaute, couleursTheme } from "@/lib/palette";
import { useThemeSombre } from "@/lib/theme";
import { nombre, nomPlateforme, nomTypeInteraction, decimal } from "@/lib/format";
import type { NoeudReseau, Reseau } from "@/lib/types";

const TOUTES = "toutes";

export function ReseauCytoscape({ donnees }: { donnees: Reseau }) {
  const conteneur = useRef<HTMLDivElement>(null);
  const instance = useRef<Core | null>(null);
  const sombre = useThemeSombre();

  const [plateforme, setPlateforme] = useState(TOUTES);
  const [source, setSource] = useState(TOUTES);
  const [communaute, setCommunaute] = useState(TOUTES);
  const [typeInteraction, setTypeInteraction] = useState(TOUTES);
  const [selection, setSelection] = useState<NoeudReseau | null>(null);

  const { elements, noeudsVisibles, liensVisibles } = useMemo(() => {
    const noeudsFiltres = donnees.noeuds.filter((noeud) => {
      if (communaute !== TOUTES && String(noeud.communaute_id) !== communaute) return false;
      if (plateforme !== TOUTES && !noeud.plateformes.includes(plateforme)) return false;
      if (source !== TOUTES && !noeud.sources.includes(source)) return false;
      return true;
    });
    const identifiants = new Set(noeudsFiltres.map((noeud) => noeud.id));

    const liensFiltres = donnees.liens.filter((lien) => {
      if (!identifiants.has(lien.source) || !identifiants.has(lien.cible)) return false;
      if (plateforme !== TOUTES && !lien.plateformes.includes(plateforme)) return false;
      if (source !== TOUTES && !lien.sources.includes(source)) return false;
      if (typeInteraction !== TOUTES && !lien.types.includes(typeInteraction)) return false;
      return true;
    });

    const maximumDegre = Math.max(...donnees.noeuds.map((noeud) => noeud.degre), 1);
    const maximumPoids = Math.max(...donnees.liens.map((lien) => lien.poids), 1);

    const definitions: ElementDefinition[] = [
      ...noeudsFiltres.map((noeud) => ({
        data: {
          id: noeud.id,
          label: noeud.label,
          communaute: noeud.communaute_id,
          taille: 12 + 26 * Math.sqrt(noeud.degre / maximumDegre),
        },
      })),
      ...liensFiltres.map((lien) => ({
        data: {
          id: `${lien.source}->${lien.cible}`,
          source: lien.source,
          target: lien.cible,
          poids: lien.poids,
          epaisseur: 0.6 + 4 * (lien.poids / maximumPoids),
          inter: lien.inter_communautaire ? 1 : 0,
        },
      })),
    ];

    return {
      elements: definitions,
      noeudsVisibles: noeudsFiltres.length,
      liensVisibles: liensFiltres.length,
    };
  }, [donnees, plateforme, source, communaute, typeInteraction]);

  useEffect(() => {
    if (!conteneur.current) return;
    const couleurs = couleursTheme(sombre);

    const cy = cytoscape({
      container: conteneur.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            "background-color": (element) =>
              couleurCommunaute(Number(element.data("communaute")), sombre),
            width: "data(taille)",
            height: "data(taille)",
            "border-width": 1,
            "border-color": couleurs.fond,
            label: "",
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-width": 3,
            "border-color": sombre ? "#2dd4bf" : "#0f766e",
            label: "data(label)",
            "font-size": 10,
            color: couleurs.texte,
            "text-background-color": couleurs.fond,
            "text-background-opacity": 0.85,
            "text-background-padding": "2px",
            "text-margin-y": -6,
          },
        },
        {
          selector: "edge",
          style: {
            width: "data(epaisseur)",
            "line-color": (element) =>
              Number(element.data("inter")) === 1 ? couleurs.lienInter : couleurs.lien,
            "target-arrow-color": (element) =>
              Number(element.data("inter")) === 1 ? couleurs.lienInter : couleurs.lien,
            "target-arrow-shape": "triangle",
            "arrow-scale": 0.6,
            "curve-style": "bezier",
            opacity: 0.65,
          },
        },
      ],
      layout: {
        name: "cose",
        animate: false,
        nodeRepulsion: () => 9000,
        idealEdgeLength: () => 70,
        randomize: false,
        fit: true,
        padding: 24,
      },
      minZoom: 0.15,
      maxZoom: 4,
      wheelSensitivity: 0.25,
    });

    instance.current = cy;

    const parIdentifiant = new Map(donnees.noeuds.map((noeud) => [noeud.id, noeud]));
    cy.on("tap", "node", (evenement) => {
      setSelection(parIdentifiant.get(evenement.target.id()) ?? null);
    });
    cy.on("tap", (evenement) => {
      if (evenement.target === cy) setSelection(null);
    });
    cy.nodes().forEach((noeud) => {
      const donneesNoeud = parIdentifiant.get(noeud.id());
      if (donneesNoeud) noeud.data("title", donneesNoeud.label);
    });

    return () => {
      cy.destroy();
      instance.current = null;
    };
  }, [elements, sombre, donnees.noeuds]);

  const reinitialiser = () => {
    setPlateforme(TOUTES);
    setSource(TOUTES);
    setCommunaute(TOUTES);
    setTypeInteraction(TOUTES);
    setSelection(null);
  };

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-ardoise-200 bg-white p-4 dark:border-ardoise-800 dark:bg-ardoise-900">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Selecteur
            libelle="Plateforme"
            valeur={plateforme}
            onChange={setPlateforme}
            options={[
              { valeur: TOUTES, libelle: "Toutes les plateformes" },
              ...donnees.plateformes.map((element) => ({
                valeur: element,
                libelle: nomPlateforme(element),
              })),
            ]}
          />
          <Selecteur
            libelle="Source"
            valeur={source}
            onChange={setSource}
            options={[
              { valeur: TOUTES, libelle: "Toutes les sources" },
              ...donnees.sources_disponibles.map((element) => ({
                valeur: element,
                libelle: element,
              })),
            ]}
          />
          <Selecteur
            libelle="Communauté"
            valeur={communaute}
            onChange={setCommunaute}
            options={[
              { valeur: TOUTES, libelle: "Toutes les communautés" },
              ...donnees.communautes.map((element) => ({
                valeur: String(element.id),
                libelle: element.nom,
              })),
            ]}
          />
          <Selecteur
            libelle="Type d'interaction"
            valeur={typeInteraction}
            onChange={setTypeInteraction}
            options={[
              { valeur: TOUTES, libelle: "Tous les types" },
              ...donnees.types_interaction.map((element) => ({
                valeur: element,
                libelle: nomTypeInteraction(element),
              })),
            ]}
          />
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-ardoise-500 dark:text-ardoise-400">
          <p>
            {nombre(noeudsVisibles)} nœuds et {nombre(liensVisibles)} liens affichés
            {donnees.tronque
              ? ` — réseau tronqué aux ${nombre(donnees.limite_noeuds)} nœuds les plus connectés sur ${nombre(donnees.noeuds_total)}.`
              : "."}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => instance.current?.fit(undefined, 24)}
              className="rounded border border-ardoise-200 px-2.5 py-1 font-medium text-ardoise-700 hover:bg-ardoise-100 dark:border-ardoise-700 dark:text-ardoise-200 dark:hover:bg-ardoise-800"
            >
              Recentrer
            </button>
            <button
              type="button"
              onClick={reinitialiser}
              className="rounded border border-ardoise-200 px-2.5 py-1 font-medium text-ardoise-700 hover:bg-ardoise-100 dark:border-ardoise-700 dark:text-ardoise-200 dark:hover:bg-ardoise-800"
            >
              Réinitialiser les filtres
            </button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        <div className="lg:col-span-3">
          {noeudsVisibles === 0 ? (
            <div className="flex h-[420px] items-center justify-center rounded-lg border border-dashed border-ardoise-300 bg-white text-sm text-ardoise-500 dark:border-ardoise-700 dark:bg-ardoise-900 dark:text-ardoise-400">
              Aucun nœud ne correspond à cette combinaison de filtres.
            </div>
          ) : (
            <div
              ref={conteneur}
              role="application"
              aria-label="Graphe des interactions entre utilisateurs"
              className="h-[420px] w-full rounded-lg border border-ardoise-200 bg-white sm:h-[560px] dark:border-ardoise-800 dark:bg-ardoise-950"
            />
          )}
          <p className="mt-2 text-xs text-ardoise-500 dark:text-ardoise-400">
            Molette : zoom — glisser : déplacement — clic sur un nœud : détail de l'utilisateur.
            La couleur indique la communauté, la taille la centralité de degré, l'épaisseur des
            liens le nombre d'interactions agrégées. Les liens entre communautés différentes
            sont affichés en teal.
          </p>
        </div>

        <aside className="rounded-lg border border-ardoise-200 bg-white p-4 dark:border-ardoise-800 dark:bg-ardoise-900">
          <h3 className="text-sm font-semibold text-ardoise-800 dark:text-ardoise-100">
            Détail de la sélection
          </h3>
          {selection ? (
            <dl className="mt-3 space-y-2 text-sm">
              <Detail terme="Utilisateur" valeur={selection.label} />
              <Detail terme="Communauté" valeur={selection.communaute} />
              <Detail terme="Messages" valeur={nombre(selection.messages)} />
              <Detail terme="Degré" valeur={nombre(selection.degre)} />
              <Detail terme="Degré entrant" valeur={nombre(selection.degre_entrant)} />
              <Detail terme="Degré sortant" valeur={nombre(selection.degre_sortant)} />
              <Detail
                terme="Centralité de degré"
                valeur={decimal(selection.centralite_degre, 4)}
              />
              <Detail
                terme="Centralité d'intermédiarité"
                valeur={decimal(selection.centralite_intermediarite, 4)}
              />
              <Detail
                terme="Plateformes"
                valeur={selection.plateformes.map(nomPlateforme).join(", ")}
              />
              <Detail terme="Sources" valeur={selection.sources.join(", ") || "—"} />
            </dl>
          ) : (
            <p className="mt-3 text-sm text-ardoise-500 dark:text-ardoise-400">
              Cliquez sur un nœud du graphe pour afficher ses indicateurs. Les utilisateurs sont
              pseudonymisés : aucune donnée personnelle n'est affichée.
            </p>
          )}

          <h4 className="mt-6 text-xs font-semibold uppercase tracking-wide text-ardoise-500 dark:text-ardoise-400">
            Légende des communautés
          </h4>
          <ul className="mt-2 space-y-1.5 text-sm">
            {donnees.communautes.map((element) => (
              <li key={element.id} className="flex items-center gap-2">
                <span
                  aria-hidden="true"
                  className="h-3 w-3 shrink-0 rounded-full"
                  style={{ backgroundColor: couleurCommunaute(element.id, sombre) }}
                />
                <span className="text-ardoise-700 dark:text-ardoise-300">{element.nom}</span>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  );
}

function Selecteur({
  libelle,
  valeur,
  onChange,
  options,
}: {
  libelle: string;
  valeur: string;
  onChange: (valeur: string) => void;
  options: { valeur: string; libelle: string }[];
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-xs font-medium text-ardoise-600 dark:text-ardoise-400">
        {libelle}
      </span>
      <select
        value={valeur}
        onChange={(evenement) => onChange(evenement.target.value)}
        className="w-full rounded-md border border-ardoise-300 bg-white px-3 py-2 text-sm text-ardoise-800 focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600 dark:border-ardoise-700 dark:bg-ardoise-950 dark:text-ardoise-100"
      >
        {options.map((option) => (
          <option key={option.valeur} value={option.valeur}>
            {option.libelle}
          </option>
        ))}
      </select>
    </label>
  );
}

function Detail({ terme, valeur }: { terme: string; valeur: string }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-ardoise-500 dark:text-ardoise-400">{terme}</dt>
      <dd className="text-right font-medium tabular-nums text-ardoise-900 dark:text-ardoise-100">
        {valeur}
      </dd>
    </div>
  );
}
