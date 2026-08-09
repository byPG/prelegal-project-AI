export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatTurnResponse {
  reply: string;
  document_id: string | null;
  fields: Record<string, string | null>;
}
