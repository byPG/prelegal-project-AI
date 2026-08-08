import type { MutualNdaFormData } from "@/types/mutual-nda";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatTurnResponse {
  reply: string;
  fields: Partial<MutualNdaFormData>;
}
