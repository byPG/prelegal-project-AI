"use client";

import Link from "next/link";
import { useState } from "react";
import { ChatApiError, saveDocument, updateSavedDocument } from "@/lib/api";
import { useAuth } from "@/lib/AuthProvider";
import type { DocumentTemplate } from "@/types/document";

interface SaveDocumentButtonProps {
  documentTypeId: string;
  template: DocumentTemplate;
  fields: Record<string, string>;
}

function defaultTitle(template: DocumentTemplate, fields: Record<string, string>): string {
  const partyOne = fields.partyOneName?.trim() || "Party One";
  const partyTwo = fields.partyTwoName?.trim() || "Party Two";
  return `${partyOne} × ${partyTwo} — ${template.name}`;
}

export function SaveDocumentButton({ documentTypeId, template, fields }: SaveDocumentButtonProps) {
  const { status, token } = useAuth();
  const [savedDocumentId, setSavedDocumentId] = useState<number | null>(null);
  const [savedDocumentTypeId, setSavedDocumentTypeId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // A save tied to one document type shouldn't silently overwrite a saved
  // row that belongs to a different type if the assistant switches types
  // mid-conversation.
  const activeSavedDocumentId = savedDocumentTypeId === documentTypeId ? savedDocumentId : null;

  async function handleSave() {
    if (!token) return;
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const title = defaultTitle(template, fields);
      if (activeSavedDocumentId != null) {
        await updateSavedDocument(token, activeSavedDocumentId, { title, fields });
      } else {
        const saved = await saveDocument(token, { document_type_id: documentTypeId, title, fields });
        setSavedDocumentId(saved.id);
        setSavedDocumentTypeId(documentTypeId);
      }
      setMessage("Saved — view it under My Documents.");
    } catch (err) {
      setError(err instanceof ChatApiError ? err.message : "Couldn't save this document. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  if (status !== "authenticated") {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled
          title="Sign in to save this document"
          className="inline-flex cursor-not-allowed items-center gap-2.5 rounded-full bg-ledger/40 px-6 py-3 font-mono text-[0.75rem] uppercase tracking-[0.14em] text-parchment-soft/70"
        >
          Save document
        </button>
        <Link href="/login/" className="text-xs text-ledger hover:underline">
          Sign in to save
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={handleSave}
        disabled={isSaving}
        className="inline-flex items-center gap-2.5 rounded-full bg-ledger px-6 py-3 font-mono text-[0.75rem] uppercase tracking-[0.14em] text-parchment-soft shadow-[0_10px_24px_-12px_rgba(30,56,35,0.65)] transition-all duration-150 ease-out hover:bg-ledger-dark active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSaving ? "Saving…" : activeSavedDocumentId != null ? "Update saved document" : "Save document"}
      </button>
      {message && <span className="text-xs text-ledger">{message}</span>}
      {error && <span className="text-xs text-rule">{error}</span>}
    </div>
  );
}
