import fs from "node:fs/promises";
import path from "node:path";
import { config } from "./config.js";
import type { LogRow, Sender } from "./types.js";

export async function loadSenders(): Promise<Sender[]> {
  try {
    const raw = JSON.parse(await fs.readFile(config.sendersFile, "utf8"));
    return Array.isArray(raw) ? raw as Sender[] : [];
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw error;
  }
}

export async function saveSenders(senders: Sender[]): Promise<void> {
  await fs.mkdir(path.dirname(config.sendersFile), { recursive: true });
  await fs.writeFile(config.sendersFile, `${JSON.stringify(senders, null, 2)}\n`, "utf8");
}

export function defaultSender(email: string, nom: string, tokenPath: string): Sender {
  return {
    email: email.toLowerCase(),
    nom,
    tokenPath,
    signature: `${nom}\nLumen Juris`,
    actif: true,
    limiteJournaliere: 10,
    delaiMinutes: 20,
    heureDebut: "09:00",
    heureFin: "18:00",
    categoriesAutorisees: []
  };
}

function minutesOfDay(value: string): number {
  const [hours, minutes] = value.split(":").map(Number);
  return (hours || 0) * 60 + (minutes || 0);
}

export function isWithinHours(sender: Sender, now: Date): boolean {
  const current = now.getHours() * 60 + now.getMinutes();
  const start = minutesOfDay(sender.heureDebut);
  const end = minutesOfDay(sender.heureFin);
  return current >= start && current <= end;
}

export interface SenderActivity {
  sentToday: number;
  lastSentAt: Date | null;
  recentError: boolean;
}

const dayKey = (date: Date) => date.toISOString().slice(0, 10);

export function summarizeActivity(log: LogRow[], email: string, now: Date): SenderActivity {
  const mine = log.filter((row) => row.expediteur?.toLowerCase() === email.toLowerCase());
  const today = dayKey(now);
  const sent = mine.filter((row) => row.statut === "sent");
  const lastSent = sent
    .map((row) => new Date(row.date))
    .filter((date) => !Number.isNaN(date.getTime()))
    .sort((a, b) => b.getTime() - a.getTime())[0] ?? null;
  // Une erreur dans les 60 dernières minutes met le compte de côté.
  const recentError = mine.some((row) => {
    if (row.statut !== "failed") return false;
    const date = new Date(row.date);
    return !Number.isNaN(date.getTime()) && now.getTime() - date.getTime() < 60 * 60 * 1000;
  });
  return {
    sentToday: sent.filter((row) => dayKey(new Date(row.date)) === today).length,
    lastSentAt: lastSent,
    recentError
  };
}

export interface SenderDecision {
  sender: Sender | null;
  raison: string;
  rejets: string[];
}

// Ordre imposé : catégorie, affectation explicite, actif, quota, délai, horaires,
// absence d'erreur récente. En cas d'égalité : moins d'envois aujourd'hui, puis
// dernier envoi le plus ancien.
export function selectSender(input: {
  senders: Sender[];
  log: LogRow[];
  categorie: string;
  expediteurAffecte: string;
  now: Date;
}): SenderDecision {
  const rejets: string[] = [];
  const affecte = input.expediteurAffecte.trim().toLowerCase();

  const eligible = input.senders.filter((sender) => {
    const activity = summarizeActivity(input.log, sender.email, input.now);
    const reject = (raison: string) => {
      rejets.push(`${sender.email} : ${raison}`);
      return false;
    };
    if (affecte && sender.email.toLowerCase() !== affecte) {
      return reject("un autre compte est explicitement affecté à ce prospect");
    }
    if (
      sender.categoriesAutorisees.length > 0 &&
      input.categorie &&
      !sender.categoriesAutorisees.includes(input.categorie)
    ) {
      return reject(`catégorie « ${input.categorie} » non autorisée`);
    }
    if (!sender.actif) return reject("compte inactif");
    if (activity.sentToday >= sender.limiteJournaliere) {
      return reject(`limite journalière atteinte (${activity.sentToday}/${sender.limiteJournaliere})`);
    }
    if (activity.lastSentAt) {
      const elapsed = (input.now.getTime() - activity.lastSentAt.getTime()) / 60_000;
      if (elapsed < sender.delaiMinutes) {
        return reject(`délai non écoulé (${Math.round(elapsed)} min sur ${sender.delaiMinutes})`);
      }
    }
    if (!isWithinHours(sender, input.now)) {
      return reject(`hors plage ${sender.heureDebut}–${sender.heureFin}`);
    }
    if (activity.recentError) return reject("erreur d'envoi il y a moins d'une heure");
    return true;
  });

  if (eligible.length === 0) return { sender: null, raison: "aucun compte éligible", rejets };

  const ranked = [...eligible].sort((a, b) => {
    const activityA = summarizeActivity(input.log, a.email, input.now);
    const activityB = summarizeActivity(input.log, b.email, input.now);
    if (activityA.sentToday !== activityB.sentToday) return activityA.sentToday - activityB.sentToday;
    const timeA = activityA.lastSentAt?.getTime() ?? 0;
    const timeB = activityB.lastSentAt?.getTime() ?? 0;
    return timeA - timeB;
  });

  const chosen = ranked[0];
  const activity = summarizeActivity(input.log, chosen.email, input.now);
  return {
    sender: chosen,
    raison: `${activity.sentToday}/${chosen.limiteJournaliere} envoyés aujourd'hui`,
    rejets
  };
}
