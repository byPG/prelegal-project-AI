# Prelegal Document Creator

A prototype web app for generating legal agreements from [Common Paper](https://commonpaper.com/) templates via a conversational AI assistant. Chat about what you need, watch the document fill in live, and download it as a PDF.

## Getting started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Requires the backend running separately (see `../backend/README.md`) with `NEXT_PUBLIC_API_BASE_URL` set — see `lib/api.ts`.

## How it works

- `app/page.tsx` holds which document type and field values are currently active, and lays out chat + form + live preview + download.
- `components/ChatPanel.tsx` drives the conversation; the backend (`../backend/app/templates.py`) parses all 11 `../templates/*.md` files and figures out from the conversation which document the user needs.
- `components/DocumentPreview.tsx`, `components/DocumentForm.tsx`, and `components/DocumentPdfDocument.tsx` are generic renderers driven entirely by the parsed template structure the backend serves at `GET /api/documents/{id}` — there's no per-document-type frontend code.
- `lib/document-numbering.ts` derives clause numbering (1. / 1.1. / a. / i.) from each item's nesting depth.

This is a prototype: nothing is persisted server-side beyond the current conversation, and it is not a substitute for legal advice.
