"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ChatApiError, deleteSavedDocument, listSavedDocuments } from "@/lib/api";
import { useAuth } from "@/lib/AuthProvider";
import type { SavedDocumentSummary } from "@/types/savedDocument";

function formatDate(isoString: string): string {
  // SQLite's datetime('now') returns UTC with no timezone suffix — append
  // "Z" so the browser parses it as UTC instead of local time.
  return new Date(`${isoString}Z`).toLocaleString();
}

export default function DocumentsPage() {
  const { status, token } = useAuth();
  const router = useRouter();
  const [documents, setDocuments] = useState<SavedDocumentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/login/");
  }, [status, router]);

  useEffect(() => {
    if (status !== "authenticated" || !token) return;
    let cancelled = false;
    listSavedDocuments(token)
      .then((docs) => {
        if (!cancelled) setDocuments(docs);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ChatApiError ? err.message : "Couldn't load your documents.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [status, token]);

  async function handleDelete(id: number) {
    if (!token) return;
    if (!window.confirm("Delete this document? This can't be undone.")) return;
    setDeletingId(id);
    try {
      await deleteSavedDocument(token, id);
      setDocuments((prev) => prev?.filter((doc) => doc.id !== id) ?? null);
    } catch (err) {
      setError(err instanceof ChatApiError ? err.message : "Couldn't delete this document.");
    } finally {
      setDeletingId(null);
    }
  }

  if (status !== "authenticated") return null;

  return (
    <main className="mx-auto max-w-4xl px-6 py-10 sm:px-10">
      <h1 className="font-display text-2xl font-semibold text-brand-navy">My documents</h1>
      <p className="mt-1 text-sm text-brand-gray">Documents you&rsquo;ve saved while drafting.</p>

      {error && <p className="mt-4 text-sm text-brand-danger">{error}</p>}

      {documents === null && !error && (
        <p className="mt-8 text-sm text-brand-gray">Loading…</p>
      )}

      {documents !== null && documents.length === 0 && (
        <p className="mt-8 text-sm text-brand-gray">
          No saved documents yet.{" "}
          <Link href="/" className="text-brand-blue hover:underline">
            Start drafting one
          </Link>
          .
        </p>
      )}

      {documents !== null && documents.length > 0 && (
        <ul className="mt-6 flex flex-col divide-y divide-brand-navy/10 border-y border-brand-navy/10">
          {documents.map((doc) => (
            <li key={doc.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
              <div>
                <p className="font-medium text-brand-navy">{doc.title}</p>
                <p className="text-xs text-brand-gray">
                  {doc.document_name} · updated {formatDate(doc.updated_at)}
                </p>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <Link href={`/documents/view/?id=${doc.id}`} className="text-brand-blue hover:underline">
                  View
                </Link>
                <button
                  type="button"
                  onClick={() => handleDelete(doc.id)}
                  disabled={deletingId === doc.id}
                  className="text-brand-danger hover:underline disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {deletingId === doc.id ? "Deleting…" : "Delete"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
