import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { google } from "googleapis";
import { config, projectRoot } from "../config.js";

export type OAuth2Client = InstanceType<typeof google.auth.OAuth2>;

// gmail.send pour l'envoi, gmail.readonly pour le contrôle des doublons,
// gmail.settings.basic pour la liste des alias, spreadsheets pour le suivi.
export const scopes = [
  "https://www.googleapis.com/auth/gmail.send",
  "https://www.googleapis.com/auth/gmail.readonly",
  "https://www.googleapis.com/auth/gmail.settings.basic",
  "https://www.googleapis.com/auth/spreadsheets"
];

export function tokenPathFor(email: string): string {
  const safe = email.toLowerCase().replace(/[^a-z0-9@._-]/g, "_");
  return path.join(config.tokensDir, `${safe}.json`);
}

function createClient(): OAuth2Client {
  if (!config.googleClientId || !config.googleClientSecret) {
    throw new Error(
      "GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET sont absents de .env. " +
      "Créez un identifiant OAuth de type « Application de bureau » dans Google Cloud Console."
    );
  }
  return new google.auth.OAuth2(
    config.googleClientId,
    config.googleClientSecret,
    `http://localhost:${config.googleRedirectPort}/oauth2callback`
  );
}

// Attend le retour du navigateur sur un serveur local éphémère.
function waitForCode(): Promise<string> {
  return new Promise((resolve, reject) => {
    const server = http.createServer((request, response) => {
      const url = new URL(request.url ?? "/", `http://localhost:${config.googleRedirectPort}`);
      if (url.pathname !== "/oauth2callback") {
        response.writeHead(404).end();
        return;
      }
      const code = url.searchParams.get("code");
      const error = url.searchParams.get("error");
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      response.end(
        code
          ? "<p>Compte connecté. Vous pouvez fermer cet onglet.</p>"
          : `<p>Échec de l'autorisation : ${error ?? "code absent"}</p>`
      );
      server.close();
      if (code) resolve(code);
      else reject(new Error(error ?? "Code d'autorisation absent."));
    });
    server.on("error", reject);
    server.listen(config.googleRedirectPort);
    setTimeout(() => {
      server.close();
      reject(new Error("Délai d'autorisation dépassé (5 minutes)."));
    }, 300_000).unref();
  });
}

export function authorizationUrl(client: OAuth2Client, loginHint: string): string {
  return client.generateAuthUrl({
    access_type: "offline",
    prompt: "consent",
    scope: scopes,
    login_hint: loginHint
  });
}

export async function runAuthFlow(email: string): Promise<OAuth2Client> {
  const client = createClient();
  const url = authorizationUrl(client, email);
  console.log("\nOuvrez cette adresse dans votre navigateur, puis autorisez l'accès :\n");
  console.log(url);
  console.log("\nEn attente du retour de Google…");

  const code = await waitForCode();
  const { tokens } = await client.getToken(code);
  client.setCredentials(tokens);

  await fs.mkdir(config.tokensDir, { recursive: true });
  const filePath = tokenPathFor(email);
  await fs.writeFile(filePath, `${JSON.stringify(tokens, null, 2)}\n`, { mode: 0o600 });
  console.log(`Jeton enregistré dans ${path.relative(projectRoot, filePath)}`);
  return client;
}

export async function loadClient(tokenFile: string): Promise<OAuth2Client> {
  const client = createClient();
  const tokens = JSON.parse(await fs.readFile(tokenFile, "utf8"));
  client.setCredentials(tokens);
  // Persiste le jeton rafraîchi pour éviter une reconnexion à chaque exécution.
  client.on("tokens", (fresh) => {
    const merged = { ...tokens, ...fresh };
    fs.writeFile(tokenFile, `${JSON.stringify(merged, null, 2)}\n`, { mode: 0o600 })
      .catch(() => undefined);
  });
  return client;
}
