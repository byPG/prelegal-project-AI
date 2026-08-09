export interface DocumentField {
  key: string;
  label: string;
}

// Field names mirror the backend's JSON exactly (snake_case, e.g.
// `field_key`) rather than converting to camelCase — the whole API is
// snake_case (see `document_id` in ChatTurnResponse below), so a
// translation layer would just be a place for the two to drift apart.
export type InlineSegment =
  | { type: "text"; text: string; variant: "plain" | "bold" | "header2" | "header3" }
  | { type: "field"; field_key: string }
  | { type: "link"; text: string; href: string };

export interface BodyItem {
  depth: number;
  inline: InlineSegment[];
}

export interface DocumentSummary {
  id: string;
  name: string;
  description: string;
}

export interface DocumentTemplate extends DocumentSummary {
  fields: DocumentField[];
  body: BodyItem[];
  attribution: string | null;
}
