"use client";

import type { DocumentTemplate } from "@/types/document";

interface DocumentFormProps {
  template: DocumentTemplate;
  fields: Record<string, string>;
  onChange: (key: string, value: string) => void;
}

export function DocumentForm({ template, fields, onChange }: DocumentFormProps) {
  return (
    <form className="flex flex-col gap-5" onSubmit={(e) => e.preventDefault()}>
      {template.fields.map((field) => (
        <label key={field.key} className="flex flex-col gap-1.5">
          <span className="font-mono text-[0.7rem] uppercase tracking-[0.14em] text-ink-soft">
            {field.label}
          </span>
          <input
            type="text"
            value={fields[field.key] ?? ""}
            onChange={(e) => onChange(field.key, e.target.value)}
            className="border-b border-line bg-transparent py-1.5 font-sans text-[0.95rem] text-ink placeholder:text-ink-soft/40 focus:border-rule focus:outline-none"
          />
        </label>
      ))}
    </form>
  );
}
