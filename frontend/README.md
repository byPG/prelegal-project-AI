# Mutual NDA Creator

A prototype web app for generating a [Common Paper Mutual Non-Disclosure Agreement](https://commonpaper.com/standards/mutual-nda/1.0/). Fill in the cover page details, see the agreement fill in live, and download it as a PDF.

## Getting started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## How it works

- `app/page.tsx` holds the form state and lays out the form + live preview.
- `lib/mutual-nda-content.ts` holds the Standard Terms (adapted from `../templates/Mutual-NDA.md`) as structured segments, shared by both the on-screen preview and the PDF.
- `components/MutualNdaPreview.tsx` renders the live HTML preview.
- `components/MutualNdaPdfDocument.tsx` + `components/DownloadPdfButton.tsx` render the same content to a downloadable PDF via [`@react-pdf/renderer`](https://react-pdf.org/).

This is a prototype: everything runs client-side, nothing is persisted, and it is not a substitute for legal advice.
