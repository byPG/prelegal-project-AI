"use client";

import { MUTUAL_NDA_FIELDS, type MutualNdaFormData } from "@/types/mutual-nda";

interface MutualNdaFormProps {
  formData: MutualNdaFormData;
  onChange: (key: keyof MutualNdaFormData, value: string) => void;
}

const SECTIONS: {
  group: "party-one" | "party-two" | "terms";
  eyebrow: string;
  heading: string;
}[] = [
  { group: "party-one", eyebrow: "Party One", heading: "First party" },
  { group: "party-two", eyebrow: "Party Two", heading: "Second party" },
  { group: "terms", eyebrow: "Terms", heading: "Agreement terms" },
];

export function MutualNdaForm({ formData, onChange }: MutualNdaFormProps) {
  return (
    <form className="flex flex-col gap-10" onSubmit={(e) => e.preventDefault()}>
      {SECTIONS.map((section) => (
        <fieldset key={section.group} className="flex flex-col gap-5">
          <legend className="flex w-full items-baseline gap-3 pb-2">
            <span className="font-mono text-[0.68rem] uppercase tracking-[0.2em] text-brass">
              {section.eyebrow}
            </span>
            <span className="h-px flex-1 bg-line" aria-hidden />
          </legend>
          <div className="flex flex-col gap-5">
            {MUTUAL_NDA_FIELDS.filter((field) => field.group === section.group).map(
              (field) => (
                <label key={field.key} className="flex flex-col gap-1.5">
                  <span className="font-mono text-[0.7rem] uppercase tracking-[0.14em] text-ink-soft">
                    {field.label}
                  </span>
                  {field.type === "textarea" ? (
                    <textarea
                      rows={2}
                      value={formData[field.key]}
                      onChange={(e) => onChange(field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="resize-none border-b border-line bg-transparent py-1.5 font-sans text-[0.95rem] text-ink placeholder:text-ink-soft/40 focus:border-rule focus:outline-none"
                    />
                  ) : (
                    <input
                      type={field.type}
                      value={formData[field.key]}
                      onChange={(e) => onChange(field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="border-b border-line bg-transparent py-1.5 font-sans text-[0.95rem] text-ink placeholder:text-ink-soft/40 focus:border-rule focus:outline-none [color-scheme:light]"
                    />
                  )}
                </label>
              ),
            )}
          </div>
        </fieldset>
      ))}
    </form>
  );
}
