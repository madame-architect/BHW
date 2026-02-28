# Bibliography Hardening Workbench (MVP)

End-to-end web app to harden bibliography metadata via a human-in-the-loop pipeline.

## Features
- Import BibTeX `.bib` or Zotero RDF `.rdf`.
- Canonical JSON schema with provenance + diagnostics.
- Pipeline steps:
  1. Required fields validation (`title`, `type`, `url`)
  2. URL validation and redirect canonicalization
  3. DOI ensure/validation
  4. Metadata enrichment (DOI CSL + Crossref fallback)
  5. Type/publisher normalization
  6. Accessed date policy for web-like items
  7. Duplicate detection (DOI exact + fuzzy title clustering)
- Proposal system per automated change using JSON Patch.
- Review UI: stepper, issue list, item table, diff accept/reject.
- Duplicate merge UI.
- Export as input format (`.bib` or `.rdf`) plus audit JSON and CSV/Markdown table.

## Canonical schema
`id, inputKey, type, title, authors[], issued, accessed, url, doi, publisher, containerTitle, identifiers{}, tags[], provenance[], diagnostics[]`.

## Run with Docker Compose
```bash
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend: http://localhost:8000/docs

## Local development
### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Tests
```bash
cd backend
PYTHONPATH=. pytest
```

## Notes
- Zotero RDF export includes `dc:date` whenever `dcterms:dateSubmitted` is present to avoid Zotero import edge case misinterpretation.
- Resolver cache is sqlite-backed (`resolver_cache.sqlite`).
