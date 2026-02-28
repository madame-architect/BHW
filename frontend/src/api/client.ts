import { Item } from "../types";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function parseFile(format: "bib" | "rdf", file: File): Promise<{sessionId:string;items:Item[];summary:any}> {
  const fd = new FormData();
  fd.append("format", format);
  fd.append("file", file);
  const r = await fetch(`${API}/api/parse`, { method: "POST", body: fd });
  return r.json();
}

export async function runPipeline(sessionId: string) {
  const r = await fetch(`${API}/api/sessions/${sessionId}/run`, { method: "POST" });
  return r.json();
}

export async function acceptProposal(sessionId: string, proposalId: string) {
  return fetch(`${API}/api/sessions/${sessionId}/proposals/${proposalId}/accept`, { method: "POST" });
}

export async function rejectProposal(sessionId: string, proposalId: string) {
  return fetch(`${API}/api/sessions/${sessionId}/proposals/${proposalId}/reject`, { method: "POST" });
}

export async function getDuplicates(sessionId: string) {
  const r = await fetch(`${API}/api/sessions/${sessionId}/duplicates`);
  return r.json();
}

export async function mergeDuplicates(sessionId: string, payload: any) {
  const r = await fetch(`${API}/api/sessions/${sessionId}/merge`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
  });
  return r.json();
}

export function exportUrl(sessionId: string, format: string) {
  return `${API}/api/sessions/${sessionId}/export?format=${format}`;
}
