export interface SavedDocumentSummary {
  id: number;
  document_type_id: string;
  document_name: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface SavedDocumentDetail extends SavedDocumentSummary {
  fields: Record<string, string>;
}
