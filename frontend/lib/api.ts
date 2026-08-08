import type { ChatMessage, ChatTurnResponse } from "@/types/chat";
import type { MutualNdaFormData } from "@/types/mutual-nda";

// Empty string = same-origin, which is what the packaged app uses (FastAPI
// serves the static export and /api/* from one process/port). Only needed
// for local dev, where `next dev` (port 3000) and the backend (port 8000)
// run separately.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export class ChatApiError extends Error {}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // Body wasn't JSON (or had no `detail`) — fall through to the generic message below.
  }
  return `Something went wrong (${response.status}). Please try again.`;
}

export async function fetchGreeting(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/chat/greeting`);
  if (!response.ok) throw new ChatApiError(await parseErrorDetail(response));
  const body: { reply: string } = await response.json();
  return body.reply;
}

export async function sendChatMessage(
  messages: ChatMessage[],
  fields: MutualNdaFormData,
): Promise<ChatTurnResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, fields }),
  });
  if (!response.ok) throw new ChatApiError(await parseErrorDetail(response));
  return response.json();
}
