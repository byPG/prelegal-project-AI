"use client";

import { PDFDownloadLink } from "@react-pdf/renderer";
import { DocumentPdfDocument } from "@/components/DocumentPdfDocument";
import type { DocumentTemplate } from "@/types/document";

interface DownloadPdfButtonProps {
  template: DocumentTemplate;
  fields: Record<string, string>;
}

function SealIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      aria-hidden
    >
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <path d="M12 3v2.4M12 18.6V21M21 12h-2.4M5.4 12H3" strokeLinecap="round" />
    </svg>
  );
}

export function DownloadPdfButton({ template, fields }: DownloadPdfButtonProps) {
  const fileName = `${fields.partyOneName || "Party-One"}-${fields.partyTwoName || "Party-Two"}-${
    template.name
  }.pdf`.replace(/\s+/g, "-");

  return (
    <PDFDownloadLink
      document={<DocumentPdfDocument template={template} fields={fields} />}
      fileName={fileName}
      className="group inline-flex items-center gap-2.5 rounded-full bg-ledger px-6 py-3 font-mono text-[0.75rem] uppercase tracking-[0.14em] text-parchment-soft shadow-[0_10px_24px_-12px_rgba(30,56,35,0.65)] transition-all duration-150 ease-out hover:bg-ledger-dark active:scale-95 active:-rotate-1"
    >
      {({ loading }) => (
        <>
          <span className="text-brass-soft transition-transform duration-150 group-active:scale-90">
            <SealIcon />
          </span>
          {loading ? "Preparing document…" : "Seal & download PDF"}
        </>
      )}
    </PDFDownloadLink>
  );
}
