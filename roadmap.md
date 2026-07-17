# Clause — Project Roadmap

*Local document assistant: upload workplace agreements and other documents, ask questions, get cited answers. Runs entirely on-device (Flask + Ollama + SQLite), CPU-only.*

This file is the forward-looking plan. What exists and how it was verified lives in [`README.md`](README.md) and [`QA_HISTORY.md`](QA_HISTORY.md).

---

## Shipped

**Core RAG pipeline**
- PDF/TXT/DOCX ingestion with validated uploads (extension gate, sanitized filenames)
- Table repair layer: pdfplumber cell-grid extraction, fragment merging, forward-fill, ghost filtering, one-fact-per-line serialization (v2→v1 hybrid currently live — see Open Rulings)
- Clause-based chunking, nomic-embed-text embeddings, cosine ranking
- Clause-number boost and margin-expansion tiebreak in retrieval
- Query rewriting for follow-up questions: heuristic gate (validated 14/14) + conditional LLM rewrite

**Multi-document support**
- `docs` table with enforced foreign keys and cascade deletion
- Per-document retrieval, chat history, and rewriter context (three contamination doors verified closed)
- Duplicate-upload rejection; per-document delete; document selector UI

**Interface (Clause)**
- Two-panel chat UI with per-document history switching
- Answers cited with source clauses ("from: 1.1 …")
- Length-based reliability hint (empirical finding: answer length inversely correlates with correctness on 3B models)
- Tab-title loading indicator; guarded destructive actions
- Role-based CSS variable palette ("Archive" theme)

**Lab infrastructure**
- QA_HISTORY: 10-mode failure taxonomy, all experiments logged including rollbacks
- Provenance instrumentation: per-ask banner (doc, question, prompt), retrieval ranking, final chunk selection, full payload capture to `last_ask.txt`, upload filename announcement

## Deliberately abandoned

- **Personal memory system** (original Phase 1): the project pivoted from "assistant that remembers the user" to "assistant that reads documents." No memory tables were built; the earlier roadmap's checkmarks were aspirational. If revisited, it is a new project, not a phase of this one.
- **Cloud parsing services** (LlamaParse): rejected on architecture — violates the local-first premise.
- **MuPDF-based extraction** (pymupdf4llm): incompatible with this document class's non-conformant streams; evidence in QA_HISTORY.

## Open rulings (decisions owed, not features)

1. **Serializer**: v2→v1 fallback hybrid is live by accident of a branch merge. Rule: keep deliberately (and log) or revert to pure v1. One flagship pass on record; not yet tested against the full slate.
2. **Sources in history**: live answers carry citations; reloaded history does not (sources are not stored in `messages`). Accept as limitation or schedule the schema change.

## Next

**Near-term (designed, awaiting a session)**
- **Adaptive-k retrieval**: when rank[0] dominates by a score gap, send fewer chunks — latency win on CPU. Experiment protocol written (definitional vs combinational question sets, latency + completeness scoring).
- **Upload atomicity**: wrap document insert + chunk loop in one transaction so interrupted uploads leave nothing behind (currently they leave stubs the duplicate gate then defends).
- **Automated test suite**: pytest for the pure functions — `needs_rewrite` (existing 14-question set), `_repair_table` fixtures from known grids, `is_allowed_file` edge cases. Converts one-time manual validation into permanent regression protection.

**Medium-term**
- **Model selection UI**: dropdown for the chat model, enabling an 8B audition (llama3.1:8b) against the known model-bound failures without code edits.
- **Deterministic range selection**: detect tiered-range questions, parse the serialized tiers, do the boundary comparison in Python — removes the model's ~1/3-reliable dice from redundancy-style questions entirely. The designed fix for the project's one remaining named failure.
- **Serializer v2.2** (if the ruling keeps v2 in play): column-position banner filter, unit-suffixed value detection ("4.4 weeks"), salad-detection fallback.

**Long-term / production hygiene**
- Environment variables for config; structured logging (the print-banner system, graduated)
- Database migrations (schema changes currently require file deletion — acceptable for a lab, not for users)
- Error handling pass over routes; deployment story if Clause ever leaves localhost

## Long-term vision

A trustworthy local document assistant: private by architecture, honest about uncertainty, and able to show its work — every answer cited, every limitation documented, every claim about its own reliability backed by a logged experiment.
