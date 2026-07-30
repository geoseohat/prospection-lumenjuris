export type ProviderName = "serpapi" | "scrapedo";

export interface SearchInput {
  type_cible: string;
  requete: string;
}

export interface OrganicResult {
  position: number;
  title: string;
  link: string;
  snippet?: string;
}

export interface SiteResult {
  type_cible: string;
  requete: string;
  titre: string;
  url: string;
  domaine: string;
  description: string;
  position: number;
  moteur: "google";
  source_api: ProviderName;
  date_collecte: string;
}

export type FetchMethod = "http" | "playwright";

export interface PageResult {
  domaine: string;
  url: string;
  titre: string;
  statut_http: number | "";
  methode: FetchMethod | "";
  contenu_texte: string;
  date_collecte: string;
  erreur: string;
}

export interface RobotsRules {
  allow: string[];
  disallow: string[];
  sitemaps: string[];
  fetched: boolean;
}

export interface Sender {
  email: string;
  nom: string;
  tokenPath: string;
  signature: string;
  actif: boolean;
  limiteJournaliere: number;
  delaiMinutes: number;
  heureDebut: string;
  heureFin: string;
  categoriesAutorisees: string[];
}

export interface Prospect {
  prospect_id: string;
  nom: string;
  cabinet: string;
  email: string;
  domaine: string;
  categorie: string;
  specialite: string;
  url_source: string;
  extrait_source: string;
  expediteur_affecte: string;
}

export type QueueStatus =
  | "pending" | "approved" | "blocked" | "duplicate" | "sent" | "failed" | "opt_out";

export interface QueueRow {
  id: string;
  prospect_id: string;
  destinataire: string;
  cabinet: string;
  expediteur: string;
  objet: string;
  message: string;
  source_personnalisation: string;
  statut: QueueStatus;
  date_creation: string;
  date_prevue: string;
  date_envoi: string;
  gmail_message_id: string;
  gmail_thread_id: string;
  motif_blocage: string;
  erreur: string;
}

export interface OptOutRow {
  email: string;
  domaine: string;
  nom: string;
  date: string;
  motif: string;
  source: string;
}

export interface LogRow {
  date: string;
  prospect_id: string;
  expediteur: string;
  destinataire: string;
  objet: string;
  statut: string;
  gmail_message_id: string;
  gmail_thread_id: string;
  erreur: string;
}

export interface MonthlyUsage {
  serpapi: number;
  scrapedo: number;
}

export interface UsageFile {
  months: Record<string, MonthlyUsage>;
}
