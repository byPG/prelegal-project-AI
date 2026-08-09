import { computeMarkers } from "@/lib/document-numbering";
import type { DocumentTemplate, InlineSegment } from "@/types/document";

interface DocumentPreviewProps {
  template: DocumentTemplate;
  fields: Record<string, string>;
}

function fieldValue(fields: Record<string, string>, key: string): string {
  return fields[key]?.trim() ?? "";
}

function FieldCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[0.62rem] uppercase tracking-[0.16em] text-brass">{label}</span>
      <span className={value ? "text-ink" : "italic text-ink-soft/50"}>{value || "—"}</span>
    </div>
  );
}

function InlineSegmentView({
  segment,
  template,
  fields,
}: {
  segment: InlineSegment;
  template: DocumentTemplate;
  fields: Record<string, string>;
}) {
  if (segment.type === "text") {
    const className =
      segment.variant === "bold"
        ? "font-semibold"
        : segment.variant === "header2"
          ? "font-display text-[1.05em] font-semibold text-ink"
          : segment.variant === "header3"
            ? "font-semibold"
            : undefined;
    return <span className={className}>{segment.text}</span>;
  }

  if (segment.type === "link") {
    return (
      <a
        href={segment.href}
        target="_blank"
        rel="noreferrer"
        className="underline decoration-dotted underline-offset-2"
      >
        {segment.text}
      </a>
    );
  }

  const value = fieldValue(fields, segment.field_key);
  if (value) {
    return (
      <span className="text-ledger-dark underline decoration-ledger-soft underline-offset-2">{value}</span>
    );
  }
  const field = template.fields.find((candidate) => candidate.key === segment.field_key);
  return (
    <span className="italic text-ink-soft/50 underline decoration-dashed decoration-ink-soft/40 underline-offset-2">
      [{field?.label ?? segment.field_key}]
    </span>
  );
}

export function DocumentPreview({ template, fields }: DocumentPreviewProps) {
  const markers = computeMarkers(template.body);

  return (
    <div className="relative overflow-hidden border border-line bg-parchment-soft pl-14 pr-8 py-10 shadow-[0_18px_40px_-24px_rgba(28,42,34,0.45)] sm:pl-16 sm:pr-12">
      <div className="absolute inset-y-0 left-8 w-px bg-rule/70 sm:left-10" aria-hidden />
      <div className="absolute inset-y-0 left-9 w-px bg-rule/25 sm:left-11" aria-hidden />

      <header className="mb-10 text-center">
        <p className="font-mono text-[0.68rem] uppercase tracking-[0.3em] text-brass">Cover Page</p>
        <h1 className="mt-2 font-display text-3xl font-semibold text-ink sm:text-4xl">{template.name}</h1>
      </header>

      <section className="mb-10 grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-3">
        {template.fields.map((field) => (
          <FieldCard key={field.key} label={field.label} value={fieldValue(fields, field.key)} />
        ))}
      </section>

      <div className="mb-8 flex items-baseline gap-3">
        <h2 className="font-display text-xl font-semibold text-ink">Standard Terms</h2>
        <span className="h-px flex-1 bg-line" aria-hidden />
      </div>

      <ol className="flex flex-col gap-5">
        {template.body.map((item, index) => (
          <li key={index} className="flex gap-3" style={{ paddingLeft: `${item.depth * 1.25}rem` }}>
            <span className="font-mono text-sm text-brass">{markers[index]}</span>
            <p className="min-w-0 flex-1 text-[0.95rem] leading-relaxed text-ink">
              {item.inline.map((segment, segIndex) => (
                <InlineSegmentView key={segIndex} segment={segment} template={template} fields={fields} />
              ))}
            </p>
          </li>
        ))}
      </ol>

      {template.attribution && (
        <footer className="mt-12 border-t border-line pt-4">
          <p className="font-mono text-[0.68rem] italic text-ink-soft/70">{template.attribution}</p>
        </footer>
      )}
    </div>
  );
}
