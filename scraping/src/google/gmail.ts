import { google } from "googleapis";
import type { OAuth2Client } from "./oauth.js";

export interface SendAsAlias {
  email: string;
  nom: string;
  parDefaut: boolean;
  verifie: boolean;
}

export interface GmailMatch {
  compte: string;
  messageId: string;
  threadId: string;
  emplacement: string;
  date: string;
  extrait: string;
}

function gmailFor(client: OAuth2Client) {
  return google.gmail({ version: "v1", auth: client });
}

export async function getAuthenticatedAddress(client: OAuth2Client): Promise<string> {
  const profile = await gmailFor(client).users.getProfile({ userId: "me" });
  const address = profile.data.emailAddress;
  if (!address) throw new Error("Adresse authentifiée introuvable.");
  return address.toLowerCase();
}

export async function listSendAs(client: OAuth2Client): Promise<SendAsAlias[]> {
  const response = await gmailFor(client).users.settings.sendAs.list({ userId: "me" });
  return (response.data.sendAs ?? []).map((alias) => ({
    email: (alias.sendAsEmail ?? "").toLowerCase(),
    nom: alias.displayName ?? "",
    parDefaut: Boolean(alias.isDefault),
    // Une adresse principale n'a pas de statut de vérification explicite.
    verifie: alias.verificationStatus === "accepted" || Boolean(alias.isPrimary)
  }));
}

const locationLabels: Record<string, string> = {
  SENT: "message envoyé",
  DRAFT: "brouillon",
  INBOX: "réponse reçue"
};

// Recherche dans les envois, brouillons et réponses. Gmail applique déjà
// l'opérateur OR entre les termes fournis dans une parenthèse.
export async function searchMailbox(
  client: OAuth2Client,
  accountEmail: string,
  terms: string[]
): Promise<GmailMatch[]> {
  const cleaned = terms.map((term) => term.trim()).filter((term) => term.length >= 3);
  if (cleaned.length === 0) return [];

  const quoted = cleaned.map((term) => `"${term.replaceAll('"', "")}"`).join(" OR ");
  const query = `(${quoted}) (in:sent OR in:draft OR in:inbox)`;
  const gmail = gmailFor(client);
  const list = await gmail.users.messages.list({ userId: "me", q: query, maxResults: 25 });

  const matches: GmailMatch[] = [];
  for (const item of list.data.messages ?? []) {
    if (!item.id) continue;
    const detail = await gmail.users.messages.get({
      userId: "me",
      id: item.id,
      format: "metadata",
      metadataHeaders: ["To", "From", "Subject", "Date"]
    });
    const labels = detail.data.labelIds ?? [];
    const location = labels.find((label) => label in locationLabels);
    const headers = detail.data.payload?.headers ?? [];
    const header = (name: string) =>
      headers.find((entry) => entry.name?.toLowerCase() === name.toLowerCase())?.value ?? "";
    matches.push({
      compte: accountEmail,
      messageId: detail.data.id ?? item.id,
      threadId: detail.data.threadId ?? "",
      emplacement: location ? locationLabels[location] : labels.join("/") || "inconnu",
      date: header("Date"),
      extrait: `${header("Subject")} — ${header("To") || header("From")}`.trim()
    });
  }
  return matches;
}

function encodeHeader(value: string): string {
  // RFC 2047 : nécessaire dès qu'un accent apparaît dans l'objet ou le nom.
  return /^[\x20-\x7e]*$/.test(value)
    ? value
    : `=?UTF-8?B?${Buffer.from(value, "utf8").toString("base64")}?=`;
}

export function buildRawMessage(input: {
  from: string;
  fromName: string;
  to: string;
  subject: string;
  body: string;
}): string {
  const lines = [
    `From: ${encodeHeader(input.fromName)} <${input.from}>`,
    `To: <${input.to}>`,
    `Subject: ${encodeHeader(input.subject)}`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
    "",
    Buffer.from(input.body, "utf8").toString("base64")
  ];
  return Buffer.from(lines.join("\r\n"), "utf8")
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

export async function sendMessage(
  client: OAuth2Client,
  raw: string
): Promise<{ messageId: string; threadId: string }> {
  const response = await gmailFor(client).users.messages.send({
    userId: "me",
    requestBody: { raw }
  });
  return {
    messageId: response.data.id ?? "",
    threadId: response.data.threadId ?? ""
  };
}
