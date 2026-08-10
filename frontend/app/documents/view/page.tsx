"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { DocumentPreview } from "@/components/DocumentPreview";
import { ChatApiError, deleteSavedDocument, fetchDocument, fetchSavedDocument } from "@/lib/api";
import { useAuth } from "@/lib/AuthProvider";
import type { DocumentTemplate } from "@/types/document";
import type { SavedDocumentDetail } from "@/types/savedDocument";

const DownloadPdfButton = dynamic(
  () => import("@/components/DownloadPdfButton").then((mod) => mod.DownloadPdfButton),
  {
    ssr: false,
    loading: () => (
      <div className="inline-flex items-center gap-2.5 rounded-full bg-ledger/60 px-6 py-3 font-mono text-[0.75rem] uppercase tracking-[0.14em] text-parchment-soft/70">
        Preparing…
      </div>
    ),
  },
);

function SavedDocumentView() {
  const { status, token } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const id = Number(searchParams.get("id"));

  const [savedDocument, setSavedDocument] = useState<SavedDocumentDetail | null>(null);
  const [template, setTemplate] = useState<DocumentTemplate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/login/");
  }, [status, router]);

  useEffect(() => {
    if (status !== "authenticated" || !token) return;
    if (!Number.isFinite(id)) {
      setError("Invalid document link.");
      return;
    }
    let cancelled = false;

    fetchSavedDocument(token, id)
      .then((doc) => {
        if (cancelled) return;
        setSavedDocument(doc);
        return fetchDocument(doc.document_type_id).then((tmpl) => {
          if (!cancelled) setTemplate(tmpl);
        });
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ChatApiError ? err.message : "Couldn't load this document.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [status, token, id]);

  async function handleDelete() {
    if (!token || !savedDocument) return;
    if (!window.confirm("Delete this document? This can't be undone.")) return;
    setIsDeleting(true);
    try {
      await deleteSavedDocument(token, savedDocument.id);
      router.push("/documents/");
    } catch (err) {
      setError(err instanceof ChatApiError ? err.message : "Couldn't delete this document.");
      setIsDeleting(false);
    }
  }

  if (status !== "authenticated") return null;

  return (
    <main className="mx-auto max-w-4xl px-6 py-10 sm:px-10">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link href="/documents/" className="text-sm text-brand-blue hover:underline">
            ← My documents
          </Link>
          {savedDocument && (
            <h1 className="mt-1 font-display text-2xl font-semibold text-brand-navy">
              {savedDocument.title}
            </h1>
          )}
        </div>
        {savedDocument && template && (
          <div className="flex items-center gap-3">
            <DownloadPdfButton template={template} fields={savedDocument.fields} />
            <button
              type="button"
              onClick={handleDelete}
              disabled={isDeleting}
              className="text-sm text-brand-danger hover:underline disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isDeleting ? "Deleting…" : "Delete"}
            </button>
          </div>
        )}
      </div>

      {error && <p className="text-sm text-brand-danger">{error}</p>}
      {!error && !template && <p className="text-sm text-brand-gray">Loading…</p>}
      {template && savedDocument && <DocumentPreview template={template} fields={savedDocument.fields} />}
    </main>
  );
}

export default function SavedDocumentViewPage() {
  return (
    <Suspense fallback={<main className="mx-auto max-w-4xl px-6 py-10 sm:px-10">Loading…</main>}>
      <SavedDocumentView />
    </Suspense>
  );
}
