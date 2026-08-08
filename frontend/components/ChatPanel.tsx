"use client";

import { useEffect, useRef, useState } from "react";
import { ChatApiError, fetchGreeting, sendChatMessage } from "@/lib/api";
import type { ChatMessage } from "@/types/chat";
import type { MutualNdaFormData } from "@/types/mutual-nda";

interface ChatPanelProps {
  fields: MutualNdaFormData;
  onFieldsUpdate: (update: Partial<MutualNdaFormData>) => void;
}

export function ChatPanel({ fields, onFieldsUpdate }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    fetchGreeting()
      .then((reply) => {
        if (!cancelled) setMessages([{ role: "assistant", content: reply }]);
      })
      .catch(() => {
        if (!cancelled) {
          setMessages([
            {
              role: "assistant",
              content:
                "Hi! I couldn't reach the assistant just now, but you can still fill in the form directly below.",
            },
          ]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const content = input.trim();
    if (!content || isSending) return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content }];
    setMessages(nextMessages);
    setInput("");
    setIsSending(true);
    setError(null);

    try {
      const response = await sendChatMessage(nextMessages, fields);
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
      onFieldsUpdate(response.fields);
    } catch (err) {
      setError(
        err instanceof ChatApiError ? err.message : "Couldn't reach the assistant. Please try again.",
      );
      // Let the user retry without having to retype — drop the optimistic user turn.
      setMessages(messages);
      setInput(content);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div ref={scrollRef} className="flex max-h-80 flex-col gap-3 overflow-y-auto pr-1">
        {messages.map((message, index) => (
          <div
            key={index}
            className={
              message.role === "assistant"
                ? "self-start whitespace-pre-wrap rounded-2xl rounded-bl-sm bg-parchment px-4 py-2.5 text-[0.9rem] leading-relaxed text-ink"
                : "self-end whitespace-pre-wrap rounded-2xl rounded-br-sm bg-ledger px-4 py-2.5 text-[0.9rem] leading-relaxed text-parchment-soft"
            }
          >
            {message.content}
          </div>
        ))}
        {isSending && (
          <div className="self-start rounded-2xl rounded-bl-sm bg-parchment px-4 py-2.5 text-[0.9rem] text-ink-soft">
            …
          </div>
        )}
      </div>

      {error && <p className="text-xs text-rule">{error}</p>}

      <div className="flex items-end gap-2">
        <textarea
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Tell the assistant about your NDA…"
          disabled={isSending}
          className="flex-1 resize-none border-b border-line bg-transparent py-1.5 font-sans text-[0.95rem] text-ink placeholder:text-ink-soft/40 focus:border-rule focus:outline-none disabled:opacity-50"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={isSending || !input.trim()}
          className="inline-flex items-center gap-2 rounded-full bg-ledger px-5 py-2.5 font-mono text-[0.7rem] uppercase tracking-[0.14em] text-parchment-soft transition-colors hover:bg-ledger-dark disabled:cursor-not-allowed disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
