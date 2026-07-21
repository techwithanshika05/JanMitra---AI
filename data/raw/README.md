# raw/

Drop unprocessed source material here: scraped scheme pages, downloaded
policy PDFs, exported FAQ spreadsheets, etc. Nothing in this folder is
assumed clean — cleaning/normalization happens in `app/rag/ingest.py`
(and, in a full build, a `clean.py` script) before anything reaches
`../prepared/`.

For this MVP, `../prepared/schemes.json` and `../prepared/faqs.json` are
committed directly as the ready-to-ingest output of that cleaning stage,
so the app is demoable without needing to run a scraper first.
