/**
 * Types des fichiers JSON produits par le pipeline Python.
 *
 * Aucune statistique n'est définie ici : ces interfaces décrivent uniquement la
 * forme des données lues dans `public/data/*.json`.
 */

export interface JeuDeDonnees {
  type: "synthetique" | "reel";
  synthetique: boolean;
  fichiers: string[];
  avertissement: string;
  /** « empirique » lorsque le pipeline a été lancé avec --input. */
  mode?: "empirique" | "demonstration";
  /** Effectifs par provenance : official_api, public_page, manual_verified. */
  provenances?: Record<string, number>;
}

export interface Entete {
  genere_le: string;
  titre: string;
  sous_titre: string;
  auteur: string;
  attribution: string;
  jeu_de_donnees: JeuDeDonnees;
}

export interface Repartition {
  categorie: string;
  nombre: number;
  part: number;
}

export interface Polarisation {
  modularite: number;
  interactions_intra_communautes: number;
  interactions_inter_communautes: number;
  interactions_totales: number;
  part_liens_internes: number;
  ratio_intra_inter: number | null;
  interpretation: string;
  seuils_indicatifs: Record<string, string>;
  avertissement: string;
}

export interface MetriquesReseau {
  noeuds: number;
  liens: number;
  poids_total: number;
  densite: number;
  degre_moyen: number;
  degre_entrant_moyen: number;
  degre_sortant_moyen: number;
  composantes_faibles: number;
  taille_composante_principale: number;
  part_composante_principale: number;
  reciprocite: number;
  intermediarite_exacte: boolean;
}

export interface Overview extends Entete {
  kpi: {
    sources_declarees: number;
    sources_avec_donnees_reelles: number;
    sources_couvertes_par_le_corpus: number;
    sources_import_manuel_requis: number;
    publications: number;
    utilisateurs: number;
    interactions: number;
    communautes: number;
    modularite: number;
    polarisation: string;
    contenus_potentiellement_haineux: number;
    contenus_toxiques: number;
    messages_avec_texte: number;
  };
  repartition_plateformes: {
    plateforme: string;
    libelle: string;
    interactions: number;
    part: number;
    publications: number;
  }[];
  sentiment_global: Repartition[];
  emotions_globales: Repartition[];
  haine_globale: Repartition[];
  distribution_communautes: {
    communaute: string;
    utilisateurs: number;
    messages: number;
    part_interactions_internes: number;
  }[];
  evolution_temporelle: {
    date: string;
    interactions: number;
    negatif: number;
    colere: number;
    potentiellement_haineux: number;
  }[];
  polarisation: Polarisation;
  reseau: MetriquesReseau;
  qualite_donnees: {
    lignes_ignorees: number;
    doublons_supprimes: number;
    types_inconnus: string[];
    horodatages_invalides: number;
    messages_sans_texte: number;
  };
  questions_recherche: string[];
}

export interface SourceEtudiee {
  source_id: string;
  plateforme: string;
  url: string;
  type_contenu: string;
  statut: string;
  methode_acquisition: string;
  interactions: number;
  publications: number;
  collecte_tentee: boolean;
  http_status: number | null;
  robots_txt: string;
  mur_authentification_detecte: boolean;
  metadonnees_publiques: Record<string, string>;
  voies_evaluees: VoieCollecte[];
  donnees_recuperees: string[];
  donnees_manquantes: string[];
  import_manuel_requis: boolean;
  limites: string[];
}

export interface VoieCollecte {
  voie: string;
  url: string;
  robots_txt: string;
  robots_detail: string;
  requete_effectuee: boolean;
  http_status: number | null;
  contenu_obtenu: boolean;
  remarque: string;
  resultat: string;
}

export interface Sources extends Entete {
  sources: SourceEtudiee[];
  statuts_possibles: string[];
  regles_collecte: string[];
}

export interface NoeudReseau {
  id: string;
  label: string;
  communaute_id: number;
  communaute: string;
  messages: number;
  plateformes: string[];
  sources: string[];
  degre: number;
  degre_entrant: number;
  degre_sortant: number;
  poids_entrant: number;
  poids_sortant: number;
  centralite_degre: number;
  centralite_entrante: number;
  centralite_sortante: number;
  centralite_intermediarite: number;
}

export interface LienReseau {
  source: string;
  cible: string;
  poids: number;
  types: string[];
  type_principal: string;
  plateformes: string[];
  sources: string[];
  inter_communautaire: boolean;
}

export interface Reseau extends Entete {
  metriques: MetriquesReseau;
  limite_noeuds: number;
  noeuds_total: number;
  liens_total: number;
  noeuds_affiches: number;
  liens_affiches: number;
  tronque: boolean;
  noeuds: NoeudReseau[];
  liens: LienReseau[];
  communautes: { id: number; nom: string }[];
  plateformes: string[];
  sources_disponibles: string[];
  types_interaction: string[];
  message: string;
}

export interface TermeCompte {
  terme: string;
  occurrences: number;
}

export interface TermeScore {
  terme: string;
  score: number;
}

export interface Communaute {
  id: number;
  nom: string;
  utilisateurs: number;
  messages: number;
  messages_avec_texte: number;
  interactions_internes: number;
  interactions_externes: number;
  part_interactions_internes: number;
  liens_internes: number;
  liens_externes: number;
  top_mots: TermeCompte[];
  top_hashtags: TermeCompte[];
  termes_caracteristiques: TermeScore[];
  sentiment: Repartition[];
  emotions: Repartition[];
  haine: Repartition[];
  plateformes: { plateforme: string; interactions: number }[];
}

export interface Communautes extends Entete {
  algorithme: string;
  nombre_communautes: number;
  modularite: number;
  polarisation: Polarisation;
  communautes: Communaute[];
  matrice_interactions: {
    source: string;
    cible: string;
    source_id: number;
    cible_id: number;
    interactions: number;
  }[];
  utilisateurs_non_affectes: number;
  message: string;
}

export interface ProfilLexical {
  messages_avec_texte: number;
  mots: TermeCompte[];
  bigrammes: TermeCompte[];
  tfidf: TermeScore[];
  hashtags: TermeCompte[];
  message: string;
}

export interface Contenu extends Entete {
  profils: Record<string, ProfilLexical>;
  communautes: { id: string; nom: string }[];
  plateformes: { id: string; nom: string }[];
  taille_top: number;
  methode: string;
}

export interface Methode {
  nom: string;
  version: string;
  langues: string[];
  type: string;
  modele_ml?: string | null;
  performance_evaluee: boolean;
  avertissement?: string;
  remplacable?: string;
  limites: string[];
}

export interface LigneDimension {
  cle: string;
  libelle: string;
  messages: number;
  [categorie: string]: string | number;
}

export interface AnalyseCategorielle extends Entete {
  categories: string[];
  methode: Methode;
  messages_analyses: number;
  global: Repartition[];
  par_communaute: LigneDimension[];
  par_plateforme: LigneDimension[];
  avertissement: string;
  message: string;
}

export interface DiscoursHaineux extends AnalyseCategorielle {
  par_source: LigneDimension[];
  confiance_moyenne: number | null;
  confiance_disponible: boolean;
  extraits: {
    label: string;
    confiance: number;
    communaute: string;
    plateforme: string;
    signaux: string[];
    extrait: string;
  }[];
  extraits_publies: boolean;
  note_extraits: string;
}

export interface Cascade {
  cascade_id: string;
  source_id: string;
  plateforme: string;
  url: string;
  auteur_racine: string;
  taille: number;
  profondeur: number;
  participants: number;
  duree_minutes: number | null;
  communautes_atteintes: string[];
  nombre_communautes_atteintes: number;
  debut: string | null;
  fin: string | null;
  taux_negatif: number;
  taux_colere: number;
  taux_soutien: number;
  taux_potentiellement_haineux: number;
  taux_toxique: number;
  repartition_types: Record<string, number>;
}

export interface NoeudCascade {
  id: string;
  parent: string | null;
  type: string;
  profondeur: number;
  auteur: string;
  communaute: string;
  communaute_id: number;
  sentiment: string;
  emotion: string;
  haine_label: string;
  horodatage: string | null;
}

export interface Propagation extends Entete {
  nombre_cascades: number;
  cascades: Cascade[];
  arbres: Record<string, NoeudCascade[]>;
  noeuds_max_par_arbre: number;
  statistiques: {
    nombre_cascades: number;
    taille_moyenne: number;
    taille_maximale: number;
    profondeur_moyenne: number;
    profondeur_maximale: number;
    duree_moyenne_minutes: number | null;
    cascades_multi_communautes: number;
  };
  methode: string;
  message: string;
}
