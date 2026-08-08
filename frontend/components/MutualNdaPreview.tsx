import {
  MUTUAL_NDA_ATTRIBUTION,
  MUTUAL_NDA_CLAUSES,
  type ContentSegment,
} from "@/lib/mutual-nda-content";
import { formatLegalDate } from "@/lib/format";
import type { MutualNdaFormData } from "@/types/mutual-nda";

interface MutualNdaPreviewProps {
  formData: MutualNdaFormData;
}

function fieldDisplayValue(formData: MutualNdaFormData, field: keyof MutualNdaFormData) {
  const raw = formData[field];
  if (!raw) return "";
  return field === "effectiveDate" ? formatLegalDate(raw) : raw;
}

function Segment({
  segment,
  formData,
}: {
  segment: ContentSegment;
  formData: MutualNdaFormData;
}) {
  if (segment.type === "text") {
    return segment.bold ? <strong className="font-semibold">{segment.value}</strong> : segment.value;
  }

  const value = fieldDisplayValue(formData, segment.field);
  if (value) {
    return (
      <span className="text-ledger-dark underline decoration-ledger-soft underline-offset-2">
        {value}
      </span>
    );
  }
  return (
    <span className="italic text-ink-soft/50 underline decoration-dashed decoration-ink-soft/40 underline-offset-2">
      {segment.fallback}
    </span>
  );
}

function CoverField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[0.62rem] uppercase tracking-[0.16em] text-brass">
        {label}
      </span>
      <span className={value ? "text-ink" : "italic text-ink-soft/50"}>
        {value || "—"}
      </span>
    </div>
  );
}

export function MutualNdaPreview({ formData }: MutualNdaPreviewProps) {
  return (
    <div className="relative overflow-hidden border border-line bg-parchment-soft pl-14 pr-8 py-10 shadow-[0_18px_40px_-24px_rgba(28,42,34,0.45)] sm:pl-16 sm:pr-12">
      <div className="absolute inset-y-0 left-8 w-px bg-rule/70 sm:left-10" aria-hidden />
      <div className="absolute inset-y-0 left-9 w-px bg-rule/25 sm:left-11" aria-hidden />

      <header className="mb-10 text-center">
        <p className="font-mono text-[0.68rem] uppercase tracking-[0.3em] text-brass">
          Cover Page
        </p>
        <h1 className="mt-2 font-display text-3xl font-semibold text-ink sm:text-4xl">
          Mutual Non-Disclosure Agreement
        </h1>
      </header>

      <section className="mb-8 grid grid-cols-1 gap-6 border-y border-line py-6 sm:grid-cols-2">
        <div className="flex flex-col gap-3">
          <span className="font-mono text-[0.62rem] uppercase tracking-[0.2em] text-ink-soft">
            Party One
          </span>
          <CoverField label="Legal Name" value={formData.partyOneName} />
          <CoverField label="Address" value={formData.partyOneAddress} />
        </div>
        <div className="flex flex-col gap-3 sm:border-l sm:border-line sm:pl-6">
          <span className="font-mono text-[0.62rem] uppercase tracking-[0.2em] text-ink-soft">
            Party Two
          </span>
          <CoverField label="Legal Name" value={formData.partyTwoName} />
          <CoverField label="Address" value={formData.partyTwoAddress} />
        </div>
      </section>

      <section className="mb-10 grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-3">
        <div className="col-span-2 sm:col-span-3">
          <CoverField label="Purpose" value={formData.purpose} />
        </div>
        <CoverField label="Effective Date" value={fieldDisplayValue(formData, "effectiveDate")} />
        <CoverField label="MNDA Term" value={formData.mndaTerm} />
        <CoverField label="Term of Confidentiality" value={formData.termOfConfidentiality} />
        <CoverField label="Governing Law" value={formData.governingLaw} />
        <CoverField label="Jurisdiction" value={formData.jurisdiction} />
      </section>

      <div className="mb-8 flex items-baseline gap-3">
        <h2 className="font-display text-xl font-semibold text-ink">Standard Terms</h2>
        <span className="h-px flex-1 bg-line" aria-hidden />
      </div>

      <ol className="flex flex-col gap-6">
        {MUTUAL_NDA_CLAUSES.map((clause) => (
          <li key={clause.number} className="flex gap-4">
            <span className="font-mono text-sm text-brass">{clause.number}.</span>
            <p className="text-[0.95rem] leading-relaxed text-ink">
              <strong className="font-semibold">{clause.title}. </strong>
              {clause.segments.map((segment, index) => (
                <Segment key={index} segment={segment} formData={formData} />
              ))}
            </p>
          </li>
        ))}
      </ol>

      <footer className="mt-12 border-t border-line pt-4">
        <p className="font-mono text-[0.68rem] italic text-ink-soft/70">
          {MUTUAL_NDA_ATTRIBUTION}
        </p>
      </footer>
    </div>
  );
}
