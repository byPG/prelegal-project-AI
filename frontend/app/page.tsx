"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { ChatPanel } from "@/components/ChatPanel";
import { MutualNdaForm } from "@/components/MutualNdaForm";
import { MutualNdaPreview } from "@/components/MutualNdaPreview";
import { BLANK_MUTUAL_NDA_FORM_DATA, type MutualNdaFormData } from "@/types/mutual-nda";

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
  const [formData, setFormData] = useState<MutualNdaFormData>(BLANK_MUTUAL_NDA_FORM_DATA);

  function handleChange(key: keyof MutualNdaFormData, value: string) {
    setFormData((prev) => ({ ...prev, [key]: value }));
  }

  function handleFieldsUpdate(update: Partial<MutualNdaFormData>) {
    setFormData((prev) => {
      const next = { ...prev };
      for (const key of Object.keys(update) as (keyof MutualNdaFormData)[]) {
        const value = update[key];
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
            Mutual NDA Creator
          </h1>
          <p className="font-mono text-[0.68rem] uppercase tracking-[0.16em] text-ink-soft">
            Common Paper Standard Terms v1.0 · Prototype
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
            <ChatPanel fields={formData} onFieldsUpdate={handleFieldsUpdate} />
          </div>

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
              <MutualNdaForm formData={formData} onChange={handleChange} />
            </div>
          </details>

          <div className="border border-line bg-parchment-soft px-6 py-7">
            <p className="mb-1 font-mono text-[0.68rem] uppercase tracking-[0.2em] text-brass">
              Step 3
            </p>
            <h2 className="mb-4 font-display text-xl font-semibold text-ink">
              Download your document
            </h2>
            <DownloadPdfButton formData={formData} />
            <p className="mt-4 text-xs leading-relaxed text-ink-soft">
              This tool fills in a template for reference. It is not legal advice — have
              counsel review the agreement before it is signed.
            </p>
          </div>
        </div>

        <div className="min-w-0">
          <MutualNdaPreview formData={formData} />
        </div>
      </main>
    </div>
  );
}
