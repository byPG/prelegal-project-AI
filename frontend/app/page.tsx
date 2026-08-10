"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { ChatPanel } from "@/components/ChatPanel";
import { DocumentForm } from "@/components/DocumentForm";
import { DocumentPreview } from "@/components/DocumentPreview";
import { SaveDocumentButton } from "@/components/SaveDocumentButton";
import { ChatApiError, fetchDocument } from "@/lib/api";
import type { DocumentTemplate } from "@/types/document";

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

export default function Home() {
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [template, setTemplate] = useState<DocumentTemplate | null>(null);
  const [templateError, setTemplateError] = useState<{ documentId: string; message: string } | null>(
    null,
  );

  // null unless `template` actually corresponds to the currently-selected
  // documentId. The assistant can switch document types mid-conversation
  // (see handleTurnComplete), so while a newly-selected document's fetch
  // is in flight, the previous document's template must not keep being
  // rendered, edited, or downloaded as if it were still current.
  const currentTemplate = template && template.id === documentId ? template : null;
  const currentTemplateError =
    templateError && templateError.documentId === documentId ? templateError.message : null;
  const isLoadingTemplate = documentId !== null && currentTemplate === null && currentTemplateError === null;

  useEffect(() => {
    if (!documentId) return;

    let cancelled = false;

    fetchDocument(documentId)
      .then((doc) => {
        if (!cancelled) setTemplate(doc);
      })
      .catch((err) => {
        if (!cancelled) {
          setTemplateError({
            documentId,
            message: err instanceof ChatApiError ? err.message : "Couldn't load the document. Please try again.",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [documentId]);

  function handleFieldChange(key: string, value: string) {
    setFields((prev) => ({ ...prev, [key]: value }));
  }

  function handleTurnComplete(newDocumentId: string | null, fieldUpdates: Record<string, string | null>) {
    const documentChanged = newDocumentId != null && newDocumentId !== documentId;
    if (documentChanged) setDocumentId(newDocumentId);

    setFields((prev) => {
      const base = documentChanged ? {} : prev;
      const next = { ...base };
      for (const [key, value] of Object.entries(fieldUpdates)) {
        if (value != null) next[key] = value;
      }
      return next;
    });
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-line px-6 py-5 sm:px-10">
        <div className="mx-auto flex max-w-7xl flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
          <h1 className="font-display text-lg font-semibold tracking-tight text-ink">
            Prelegal Document Creator
          </h1>
          <p className="font-mono text-[0.68rem] uppercase tracking-[0.16em] text-ink-soft">
            Common Paper Standard Terms · Prototype
          </p>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-10 px-6 py-10 sm:px-10 lg:grid-cols-[380px_1fr] lg:items-start">
        <div className="flex flex-col gap-6 lg:sticky lg:top-8">
          <div className="border border-line bg-parchment-soft px-6 py-7">
            <p className="mb-1 font-mono text-[0.68rem] uppercase tracking-[0.2em] text-brass">
              Step 1
            </p>
            <h2 className="mb-6 font-display text-xl font-semibold text-ink">
              Talk to the assistant
            </h2>
            <ChatPanel documentId={documentId} fields={fields} onTurnComplete={handleTurnComplete} />
          </div>

          {currentTemplate && (
            <details className="group border border-line bg-parchment-soft px-6 py-7">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4">
                <span>
                  <span className="mb-1 block font-mono text-[0.68rem] uppercase tracking-[0.2em] text-brass">
                    Step 2
                  </span>
                  <span className="font-display text-xl font-semibold text-ink">
                    Edit the details directly
                  </span>
                </span>
                <svg
                  viewBox="0 0 20 20"
                  width="16"
                  height="16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="shrink-0 text-brass transition-transform duration-150 group-open:rotate-180"
                  aria-hidden
                >
                  <path d="M5 7.5 10 12.5 15 7.5" />
                </svg>
              </summary>
              <div className="mt-6">
                <DocumentForm template={currentTemplate} fields={fields} onChange={handleFieldChange} />
              </div>
            </details>
          )}

          {currentTemplate && (
            <div className="border border-line bg-parchment-soft px-6 py-7">
              <p className="mb-1 font-mono text-[0.68rem] uppercase tracking-[0.2em] text-brass">
                Step 3
              </p>
              <h2 className="mb-4 font-display text-xl font-semibold text-ink">
                Download your document
              </h2>
              <div className="flex flex-wrap items-center gap-3">
                <DownloadPdfButton template={currentTemplate} fields={fields} />
                <SaveDocumentButton documentTypeId={currentTemplate.id} template={currentTemplate} fields={fields} />
              </div>
              <p className="mt-4 text-xs leading-relaxed text-ink-soft">
                This tool fills in a template for reference. It is not legal advice — have
                counsel review the agreement before it is signed.
              </p>
            </div>
          )}
        </div>

        <div className="min-w-0">
          {currentTemplate ? (
            <DocumentPreview template={currentTemplate} fields={fields} />
          ) : (
            <div className="flex min-h-[320px] flex-col items-center justify-center gap-2 border border-dashed border-line bg-parchment-soft/60 px-8 py-16 text-center">
              {isLoadingTemplate ? (
                <p className="font-mono text-[0.75rem] uppercase tracking-[0.14em] text-ink-soft">
                  Loading document…
                </p>
              ) : currentTemplateError ? (
                <p className="text-sm text-rule">{currentTemplateError}</p>
              ) : (
                <p className="max-w-xs text-sm leading-relaxed text-ink-soft">
                  Tell the assistant what kind of agreement you need — the document preview will
                  appear here once it&rsquo;s figured out which one to create.
                </p>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
