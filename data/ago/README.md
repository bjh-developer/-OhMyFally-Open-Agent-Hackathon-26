# AGO excerpts (S4)

Verbatim excerpts from the Auditor-General's annual reports (Singapore), chunked at paragraph boundaries
(about 120 to 330 words each). Nothing here is paraphrased; whitespace from PDF line wrapping is collapsed
and nothing else is changed. They back the `ago_chunks` table and the memo's AGO citations.

- `index.csv`: `chunk_id, report, fy, section, page, url`. `page` is the page number printed in the report,
  followed by the PDF page index; `url` is the report PDF with `#page=<PDF page>`.
- `<chunk_id>.txt`: the chunk text. `section` in the index is a short label we wrote to describe the chunk, not AGO wording.
- Source: <https://www.ago.gov.sg/publications/annual-reports/> (PDFs for FY2021/22 to FY2024/25).
  Reports cover the entities AGO audited; they say nothing about GeBIZ suppliers, and findings are about the audited bodies' processes.
- Coverage is limited to lapses in tender evaluation, contract variations, debarred contractors, quotation integrity and
  vendor concentration. AGO's wording is quoted as is; the memo must still say "anomaly for review".
