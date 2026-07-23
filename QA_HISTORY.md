# AI Document Assistant — Q&A Testing History

A record of questions asked against the Bunnings Retail Enterprise Agreement 2023, tracking how answer quality evolved as the project moved from "dump the whole document in" → chunking → embeddings → real semantic retrieval.

---

## Before RAG (whole-document context, no chunking)

These tests exposed the core problem: the model could only "see" whatever fit inside the context window, and it didn't reliably admit when content was missing — sometimes it hallucinated instead.

### Q: "What are the overtime conditions for Bunnings?"
**Context:** Very first real test, full 48-page PDF stuffed into one prompt, default ~4k context window.
**A:** Gave a vague, generic summary of the *whole document* (trial periods, IFAs, consultation, dispute resolution) — completely ignored the actual question. Never even mentioned overtime specifics.
**Verdict:** ❌ Failed — question effectively ignored, likely due to document positioning + truncation.

### Q: "What does shiftwork entail?" (asked twice, at 8192 token context)
**A (1st attempt):** Fabricated a generic definition — "rotating shifts," "healthcare, manufacturing, transportation," none of which is in the real document. No real clause content used.
**A (2nd attempt, after re-testing):** Different fabricated generic answer — mentioned "hospitals," "10pm to 6am" (the real clause says 6pm–5am), again no real content.
**Verdict:** ❌ Failed — clean hallucination both times, even with an explicit "say so if you don't know" system prompt instruction in place. Proved that prompting alone doesn't stop hallucination on a small local model.

### Q: (about Pre-Agreement Base Rates, clause 16.13(t), page 38)
**A:** "I'm not able to find the specific information about 'Pre-Agreement Base Rates' in the provided document. Could you please provide more context..."
**Verdict:** ✅ Honest — correctly admitted it didn't have the content, rather than guessing.

### Q: (about the Kitchen Specialist role, Appendix 1, page 40)
**A:** Correctly listed the real duties — kitchen design assistance, using the design planner, developing customer relationships — matching the source almost verbatim.
**Verdict:** ✅ Accurate.

### Q: (about Store Team Member duties)
**A:** Answered with real document content — but attributed it to the wrong role. The duties listed ("receiving visitors," "answering phone calls," "data entry") actually belong to *Store Administrator*, not *Store Team Member*, in the same table.
**Verdict:** ⚠️ Partially correct — real content retrieved, but misattributed. A subtler failure than outright hallucination: confident, well-formed, and wrong.

### Q: (about the dispute resolution procedure, clause 16.11/Appendix 6, near the end of the document)
**A:** Near-verbatim, fully accurate reproduction of the real clause (a) through (h).
**Verdict:** ✅ Accurate — this content happened to survive truncation since it was near the end of the prompt.

---

## After chunking + embeddings + semantic retrieval (the real RAG pipeline)

Once chunking, embeddings, and top-3 relevance ranking were wired in, retrieval started pulling the *correct* clause regardless of where it sat in the document.

### Q: "What is a trade administrator?"
**A:** Correctly said it couldn't find a specific "Trade Administrator" definition, while noting related roles that do exist (Trade Specialist, Trade Qualified, Forklift Coach).
**Verdict:** ✅ Honest — accurate acknowledgment of missing/different content.

### Q: "What does a supervisor do?" / "What roles does a supervisor have?"
**A:** Correctly listed real Supervisor duties (supervising/training team members, overseeing a department, supporting store leadership) — but also fabricated some extra detail ("Section 5.1", "Section 5.2", disciplinary action, record-keeping) not present in the source.
**Verdict:** ⚠️ Mixed — real core content correct, but padded with invented section numbers/details.

### Q: "What is the role of a supervisor?"
**A:** Clean, accurate answer — matched the real Supervisor clause exactly, no fabricated extras this time.
**Verdict:** ✅ Accurate.

### Q: "What are the Provisions Specific to Bunnings Trade Centres?" + "What are the overtime conditions?"
**Context:** First real test after the full embedding + ranking pipeline went live.
**A:** Retrieved top chunks were **3.1 Overtime conditions**, **3.2 Overtime pay**, **3.3 Reasonable overtime** — all correct top-3 matches out of 99 stored chunks. Answer content was accurate and near-verbatim on the overtime specifics, though it opened by conflating the earlier Trade Centres question with the new one, and mislabeled the clause number.
**Verdict:** ✅ Retrieval fully correct — first confirmed success of real semantic search. Minor rough edge: old chat history bleeding into the new answer's framing.

### Q: (about incentive rates — page 9, clause 2.1)
**A:** Accurate, detailed breakdown of real incentive rate percentages by day/time (30%/52.5% weekday early morning, 40%/62.5% Saturday, up to 125%/147.5% public holidays, etc.) — all figures matched the source table correctly.
**Verdict:** ✅ Accurate — confirmed retrieval works across different topics, not just the overtime test.

### Q: "What is the promotion criteria?" (clause 1.2, page 6)
**A:** Correctly summarised the real clause — a Team Member may apply in writing for a classification review, and Bunnings will consider experience, ability, performance, and operational requirements.
**Verdict:** ✅ Accurate — another clean retrieval, this time from early in the document (page 6), further confirming retrieval isn't position-dependent.

### Q: "How much is the meal allowance if overtime exceeds 4 hours?" (clause 4.1, page 12)
**A:** Correctly stated $20.01 for overtime up to 4 hours, plus an additional $18.14 if it exceeds 4 hours.
**Verdict:** ✅ Accurate — figures match the source exactly.

### Q: "What's the minimum break between finishing one shift and starting the next?" (clause 11.2(b), page 28-29)
**A:** Correctly stated a minimum 10-hour break, including the nuance that it still applies if the shift finishes after midnight.
**Verdict:** ✅ Accurate.

### Q: "Can I get paid extra for working nights?"
**Context:** Deliberately vague, casually-worded question designed to test semantic matching against the document's own more formal language ("shiftwork," "incentive rates").
**A:** "No. There is no mention of additional pay for working nights..." — flatly incorrect.
**What actually happened (confirmed via the retrieval ranking):** The correct chunk — **16.12 Shiftwork**, which pays 25%–125% incentive rates for shifts starting after 6pm — was retrieved with a score of **0.5907, ranked 2nd out of 99 chunks**, right behind "1.3 Payment of wages" (0.5959) and just ahead of "3.1 Overtime conditions" (0.5879). The correct content was sitting directly in the model's context.
**Verdict:** ⚠️ **Retrieval succeeded; generation failed.** This is an important and different failure mode from earlier hallucination — the model was handed the right answer and still got it wrong, most likely because it didn't connect the casual phrasing "paid extra for working nights" to the document's own "shiftwork incentive rates" framing, even with that exact text in front of it. A reasoning/comprehension gap on the small local model, not a search problem.

### Q: "What if my family member dies, do I get time off?"
**Context:** Another deliberately casual, differently-worded question, this time testing against clause 6.7 (Compassionate leave).
**A:** Correctly stated 5 days for immediate family (spouse/parent/sibling/child) and 5 days for stillbirth/miscarriage — matching the source. But then added: *"an additional five days of paid leave, but at a reduced rate of 50% of their ordinary hours rate"* — this does not exist anywhere in the real clause.
**What actually happened (confirmed via the retrieval ranking):** **6.7 Compassionate leave** was retrieved with a score of **0.6937, ranked 1st out of 99 chunks** — the clear, unambiguous top match, with the real 5/5/4/2/1-day entitlement table sitting directly in context.
**Verdict:** ❌ **Retrieval succeeded (clean #1 match); generation hallucinated an extra benefit that isn't in the source**, despite the correct table being right there. Also slightly imprecise on which relationships fall in which day-tier (grandchild is actually 4 days, not 5, in the real table). Combined with the shiftwork case above, this makes **two confirmed instances** of the same failure mode: correct retrieval, incorrect generation — a real, repeatable limitation of the small local chat model, not of the search/retrieval pipeline.

### Follow-up experiment: does reducing to top-1 chunk fix the hallucination?
**Setup:** Changed `top_chunks = rank[:3]` to `top_chunks = rank[:1]` in `app.py`, then re-ran two previously-hallucinating questions to see whether the correct chunk being present or absent — not just chunk *count* — was the real driver of accuracy.

**Test 1 — Compassionate leave question ("What if my family member dies, do I get time off?"):**
The correct chunk (6.7 Compassionate leave) had ranked **#1** for this question, so it was still included under `rank[:1]`. Result: the answer came back **fully accurate** — all five relationship tiers (5/5/4/2/1 days) correct, no fabricated "additional 50%" detail this time.

**Test 2 — Shiftwork question ("Can I get paid extra for working nights?"), re-run under the same `rank[:1]` setting:**
The correct chunk (16.12 Shiftwork) had ranked **#2** for this question, so `rank[:1]` **excluded** it — the model received only "1.3 Payment of wages" (the #1 match, itself not the right answer) and nothing else. Result: **total fabrication** — an invented clause number ("section 10.11" — doesn't exist), a fake flat rate ("$5 per hour" — the real document uses percentage-based incentive rates), and fake time windows, none of which appear anywhere in the source. Confirmed directly from the terminal output — only one system chunk (1.3 Payment of wages) was present in `prepared_data`.

**Corrected conclusion:** The original "fewer chunks reduces confusion" theory doesn't hold up — what actually matters is simply **whether the correct chunk is present in context at all**. When it is, the model tends to answer accurately (as seen consistently since chunking/embeddings were introduced). When it's absent, the model doesn't reliably say "I don't know" — it fabricates a confident, plausible-sounding answer instead. This is the same core hallucination behavior observed all the way back in the earliest whole-document tests, just now showing up at the *retrieval* layer instead of the *context-window-truncation* layer: if the top-N cutoff happens to exclude the right chunk, the failure mode is identical to the original truncation problem — content that exists in the document but isn't visible to the model gets silently guessed at rather than flagged as missing.

**Practical implication:** Since scores between the top few chunks can be close (0.5959 vs 0.5907 vs 0.5879 in the shiftwork case — a gap of ~0.005 between #1 and #2), a hard cutoff like `rank[:1]` is risky — the "right" chunk can easily be ranked #2 or #3 by a small margin. `rank[:3]` (or higher) is the safer default for coverage, accepting that it doesn't fully eliminate hallucination risk on its own — the underlying "don't guess, admit uncertainty" instruction still doesn't reliably prevent fabrication even when the answer is genuinely absent from context.

---

### Follow-up experiment: does a revised system prompt reduce hallucination?
**Setup:** Reverted `top_chunks` back to `rank[:3]` (the safer default established above), then revised the system prompt from the original:
> *"You are a helpful, professional assistant designed to help users find information in docments. Rely on conversation history and keep your answer relevant to the question. If the document doesn't contain the answer, say so explicitly rather than guessing."*

to:
> *"You are a helpful, professional assistant designed to help users find information in documents. Use the conversation history only to understand what the current question is referring to, not as a source of facts. Only use factual information that is explicitly provided in the document excerpts below. If the provided excerpts do not contain the answer, say so explicitly rather than guessing. Do not invent figures, rates, or clause numbers that are not present in the excerpts."*

Key changes: fixed a typo, narrowed "rely on conversation history" to a specific job (resolving what a follow-up question refers to, not treating prior answers as facts), added explicit grounding language ("only use information explicitly provided"), and directly targeted the observed failure pattern ("do not invent figures, rates, or clause numbers").

**Re-test:** Re-ran "Can I get paid extra for working nights?" — the same question that previously produced total fabrication (fake "section 10.11", fake "$5 per hour" flat rate, fake time windows) when the correct chunk was absent from context.

**Result:** With the revised prompt and `rank[:3]` (correct chunk — 16.12 Shiftwork — present this time), the answer contained **real, exact figures** pulled directly from the source table (25%/47.5% weekday, 40%/62.5% Saturday, 60%/82.5% Sunday, 125%/147.5% public holiday) — no fabricated clause numbers, no invented flat rates. The only rough edge: the model oddly hedged at the end, saying it wasn't sure whether these rates apply to "night shifts" specifically, despite clause 16.12(a)(ii) — sitting directly in its context — explicitly defining shiftwork as 6pm–5am shifts, which directly answers that.

**Verdict:** ✅ Meaningful improvement. The revised prompt didn't fully eliminate excess caution/hedging, but it appears to have successfully suppressed the more serious failure mode (confident fabrication of numbers and clause references). This is a much safer failure pattern — "correct facts with unnecessary hedging" is far less risky in a real workplace-policy context than "confidently wrong."

**Caveat:** This is a single re-test, not a controlled repeat across multiple runs — given `llama3.2:3b`'s inherent run-to-run randomness (noted earlier), this result is encouraging but not yet conclusively proven better than the old prompt across many trials.

---

### Q: "What is clause 16.12(a)(ii)?"
**Context:** Deliberate follow-up test, asked right after the successful shiftwork answer above, attempting to get the model to explicitly cite the specific sub-clause defining shiftwork hours (6pm–5am), before re-asking the "paid extra for working nights" question again to see if an explicit citation would resolve the earlier hedging.
**Ranking:** The chunk actually containing 16.12(a)(ii) — **16.12 Shiftwork** — ranked **6th** (0.587), well outside `rank[:3]`. The top 3 retrieved were 16.1 (Parties to the Agreement), 16.13 (Definitions), and 16.2 (When the Agreement operates) — none of which contain clause 16.12 at all.
**A:** "I don't have that information... It only mentions Clause 16.1... and Clauses 16.2 through 16.13, which provide definitions..." — an accurate, honest description of what was actually in context.
**Verdict:** ✅ Correct behavior, but for a different reason than a hallucination test — this was a genuine **retrieval miss**, not a generation failure. The model correctly and honestly reported not having the content, exactly as the revised system prompt intends. Also reveals a distinct, separate limitation: **clause-number-style questions retrieve poorly** — asking for "clause 16.12(a)(ii)" specifically seems to match more strongly against *other* clauses in the same numbered section (16.1, 16.2, 16.13) than against the clause that actually contains it, likely because the embedding model weighs the shared "16.x" numbering pattern and general "Other Legal and Miscellaneous Matters" section context more than the specific sub-clause reference. This is a good target for a future improvement (e.g., detecting clause-number references in a question and matching against `chunk_header` more directly rather than relying purely on semantic embedding similarity).

### Q: "What is 16.12?" (follow-up, dropping the specific sub-clause reference)
**A:** Correct, accurate summary of the real clause — shifts 6pm-5am, no meal-break-within-same-day exception, continuous paid hours, 30-minute paid meal breaks.
**Verdict:** ✅ Accurate — confirms the earlier retrieval miss was specific to the `(a)(ii)` sub-clause notation, not clause numbers generally. Dropping the sub-clause letters let retrieval find the right chunk cleanly.

### Q: "Can I get paid extra for working nights?" (re-asked immediately after the correct 16.12 summary above)
**A:** "I couldn't find any information in the excerpt that explicitly mentions payment for working nights... It doesn't mention anything specifically about night shifts..." — declined to connect the answer, despite the exact shift-hours definition (6pm–5am) sitting one turn earlier in the same conversation, in the model's own accurate summary.
**Verdict:** ❌ **Regression, not an improvement.** This is arguably worse than the original hallucination-era failure — this time the model had the correct information immediately available (even self-generated in its own prior turn) and still declined to draw the connection. A genuine reasoning limitation, not a retrieval or grounding problem.

**Working hypothesis:** The model may be unable to reliably map a specific numeric time range ("6:00pm to 5:00am") onto the informal, everyday concept of "night." This is an inference a human makes instantly and unconsciously, but it isn't literally stated in the text — and the revised system prompt's strict "only use explicitly provided information" instruction may be actively suppressing this kind of safe, obvious inference, not just fact fabrication. This suggests a real tension: stricter grounding reduces invented facts but may also suppress reasonable inferences a human reader would make automatically.

**Planned follow-up tests to isolate this:**
1. Ask "Do I get paid extra for shifts starting at 6pm?" (using the document's own number instead of the word "night") — if this succeeds where "nights" failed, it confirms the issue is specifically informal-word-to-number mapping.
2. Test a different informal/vague-to-specific mapping unrelated to shiftwork (e.g., "long shift" vs. the exact hour thresholds in clause 11.1) to see if this is a general pattern or specific to time-of-day language.
3. Test whether explicitly permitting "reasonable, obvious inferences" in the system prompt changes the outcome.
4. Test the reverse direction, if any clause uses informal terms directly.

---

### Q: "Do I get paid extra for shifts starting at 6pm?" (planned test #1 — document's own number instead of "nights")
**A:** Correctly connected 6pm to the shiftwork clause and cited a real 15% incentive rate — but **misattributed** that figure to clause 16.12 (Shiftwork) when it actually comes from clause 2.1 (Incentive Rates), a separate clause with its own different rate table. Still hedged at the end ("it's not explicitly stated as 'extra pay'") despite quoting a genuine 15%+ incentive rate.
**Verdict:** ⚠️ Partial support for the hypothesis — using the document's own number ("6pm") instead of an informal word ("nights") did unlock real engagement and a correct-in-substance figure, where "nights" alone produced total refusal. But it surfaced a *new*, separate problem: blending/misattributing numbers between two different clauses that happen to share a similar time window. Confirms the model's difficulty isn't limited to word-to-number mapping — clause boundaries themselves aren't reliably tracked either.

### Q: "Am I entitled to a break if I work a 6-hour shift?" (planned test #2 — numeric range placement, no vague language at all)
**A:** Correctly quoted both relevant bracket ranges from clause 11.1 verbatim ("4 hours or more but no more than 5 hours... one paid rest break," "more than 5 hours but less than 7 hours... one rest break and one meal break") — then concluded *"I don't see any information in the excerpt about breaks for a 6-hour shift,"* despite 6 falling squarely inside the second bracket it had just quoted.
**Verdict:** ❌ Significant finding — this is **not** a vague-word-to-concept problem like "nights" was; there's no informal language here at all, just a number (6) and an explicitly stated numeric range ("more than 5 but less than 7"). The model quoted the correct range and still failed to recognize that 6 falls inside it. This points to a **broader numeric reasoning weakness** — not just informal-term inference, but basic range placement — which is a bigger concern for a document assistant likely to face many "does X qualify for Y" questions with numeric thresholds.

**Open question raised:** is the revised system prompt's strict "only use explicitly provided information, don't guess" wording itself partly responsible — i.e., is the model being so conservative about "going beyond the text" that it's second-guessing straightforward arithmetic placement, not just informal inference? Worth testing the original (less strict) prompt against the same 6-hour-shift question as a controlled comparison, to see whether this specific failure is prompt-induced caution or a raw model capability limit independent of prompting.

---

### Q: "Do I get a break for working a long shift?" (revised prompt, planned test #2 — vague word, no numbers at all)
**Context:** Clause 11.1's full break entitlement table (all five tiers) was confirmed present in context via terminal output — this was **not** a retrieval miss.
**A:** Quoted the "less than 4 hours" and "4-5 hours" tiers, then said *"for longer shifts (more than 5 hours), the excerpt doesn't provide a specific rule."*
**Verdict:** ❌ Same failure pattern as the 6-hour-shift test, but now with **zero numeric reasoning required** — no range placement, just failing to surface the rest of a table that was fully present. Confirms this isn't only a "numbers vs. words" issue; the model is inconsistently reading/using tables it has complete access to, under the revised prompt.

### Controlled comparison: same "long shift" question, reverted to the original (less strict) system prompt, fresh conversation (messages table cleared)
**Original prompt:** *"You are a helpful, professional assistant designed to help users find information in docments. Rely on conversation history and keep your answer relevant to the question. If the document doesn't contain the answer, say so explicitly rather than guessing."*

**A:** Correctly and completely surfaced **all three** relevant tiers of clause 11.1 (5-7hr → one rest break + one meal break; 7-10hr → two rest breaks + one meal break; 10hr+ → two rest breaks + two meal breaks), explicitly concluded "yes, you do get a break for working a long shift," and correctly noted the break entitlement depends on shift length. One minor slip: described the 10+ hour meal breaks as "paid" when the source specifies "unpaid meal break."

**Verdict:** ✅ **Significant result.** Same question, same underlying document content, same model — but the original, less strict prompt produced a complete, well-synthesized answer across the whole table, while the revised "strict grounding" prompt produced an incomplete, falsely-limited answer on the identical question. This is real evidence supporting the hypothesis that the revised prompt's emphasis on "only use explicitly provided information, don't guess" may be suppressing the model's willingness to synthesize/complete a multi-row table, not just suppressing fabrication. A genuine tension: the stricter prompt reduces invented facts (confirmed earlier with the shiftwork test) but appears to cost completeness and reasonable synthesis on other questions.

**Next step:** design a middle-ground prompt that keeps anti-fabrication language while explicitly permitting reasonable synthesis across fully-present source material (e.g., "you may combine and summarise multiple pieces of information that are explicitly present in the excerpts, but do not add facts that are not present at all") — then re-test both the long-shift and night-shift questions under that version.

---

### Controlled comparison: "Can I get paid extra for working nights?" under the original prompt, fresh conversation
**A:** Correctly cited the real 15% (permanent) / 37.5% (casual) incentive rate for 6pm-11pm weekday shiftwork. But then invented a distinction not present anywhere in the source — implying a possible *separate* "night work" payment beyond the shiftwork rate, specifically calling out "between 10:00pm and before midnight" as an unclear window worth checking about, and added unsolicited generic advice to "check with HR or your manager."
**Verdict:** ⚠️ A third, distinct failure mode — not a clean fabrication (like the compassionate leave case) and not a flat refusal (like the revised prompt's repeated "nights" answers), but a **hybrid**: real, correct core figures wrapped in an invented caveat/framing that doesn't exist in the document. Confirms the original prompt's fabrication tendency isn't limited to inventing whole extra entitlements — it can also invent smaller framing details (a hinted-at but unconfirmed separate rate) around otherwise-correct facts.

### Controlled comparison: "What is clause 16.12(a)(ii)?" under the original prompt, fresh conversation
**Context:** Same retrieval miss as before — 16.12 not in top 3 (16.1, 16.13, 16.2 retrieved instead).
**A:** "I don't see clause 16.12(a)(ii) in the provided excerpt... The excerpt only covers clauses up to 16.13 Definitions, and does not include a clause with that specific reference." — honest, accurate, no fabrication.
**Verdict:** ✅ Matches the revised prompt's behavior on this same test. Completes the four-test matched comparison.

## Summary of the two-prompt comparison (final, all four tests matched)

| Test | Original prompt | Revised (strict) prompt |
|---|---|---|
| Compassionate leave (fabrication risk) | ❌ Invented extra "50% additional leave" detail | Not yet re-tested |
| Long shift / full table synthesis | ✅ Complete, accurate synthesis across all 3 tiers | ❌ Falsely claimed "no rule" for >5hr, despite full table present |
| "Nights" → shiftwork inference | ⚠️ Correct core numbers, but invented a fake "separate night rate" caveat | ❌ Repeatedly refused to connect 6pm–5am to "night," even after correctly summarising that exact clause moments earlier |
| Clause 16.12(a)(ii) (genuine retrieval miss) | ✅ Honestly admitted the information wasn't present | ✅ Honestly admitted the information wasn't present |

**Key finding:** Both prompts handle **genuine retrieval misses** (nothing relevant present at all) correctly and honestly — this doesn't appear to be where the risk lies. The real divergence shows up when **partial or full relevant content is present**: the original prompt tends to embellish it with plausible-but-invented extras, while the revised prompt tends to under-use or decline to fully synthesize it. Neither is a clean "safe" choice on its own.

**Working conclusion:** A middle-ground prompt — explicit anti-fabrication language *plus* explicit permission to combine/apply information that's genuinely present — is the logical next experiment, still untested as of this session.

**Proposed middle-ground prompt (untested):**
> *"You are a helpful, professional assistant designed to help users find information in documents. Use the conversation history only to understand what the current question is referring to, not as a source of facts. Base your answer only on information explicitly present in the document excerpts below — you may combine, summarise, and reasonably apply that information (for example, working out which row of a table applies to a specific number, or recognising that a time range like '6pm to 5am' corresponds to night hours), but do not add facts, figures, or details that are not present in the excerpts. If the excerpts genuinely do not contain the answer, say so explicitly rather than guessing."*

---

## Testing the middle-ground prompt

### Q: "Do I get a break for working a long shift?" (middle-ground prompt, fresh conversation)
**A:** Correctly and completely listed **all four** tiers of clause 11.1 with accurate break counts (4-5hr: one rest, no meal; 5-7hr: one rest, one meal; 7-10hr: two rest, one meal; 10hr+: two rest, two meals), and correctly concluded "yes, entitled to a break, depending on shift length."
**Verdict:** ✅ **Best result yet on this question.** Matches the original prompt's completeness while avoiding its "paid meal breaks" error (this version simply doesn't add that unstated detail). Directly fixes the revised strict prompt's false "no rule for >5hr" failure.

### Q: "Do I get paid extra for working nights?" (middle-ground prompt, same conversation — both 16.12 Shiftwork and 2.1 Incentive Rates confirmed present in context)
**A:** "Team Members who work shifts at night are eligible for an incentive rate. The excerpt states that for shiftworkers who start and finish their shift before 6:00am on the same day (i.e., working a night shift), there is no specific incentive rate mentioned."
**Verdict:** ❌ A **new** failure type — not fabrication, not clean omission, but a **garbled misreading** of the actual clause text (the real definition is "at or after 6pm and before 5am," misstated here as "before 6am on the same day"), combined with a false claim that no incentive rate exists, despite the full rate table (25%/47.5% weekday, etc.) being directly present and correctly quoted by this same model on earlier questions tonight. The explicit "6pm to 5am = night hours" example added to the prompt did not reliably fix this specific question — "nights" continues to be the hardest recurring case across all three prompt versions tested.
**Next step:** re-ask the same question once more (same prompt, fresh conversation) to check whether this is a consistent failure or one rough generation, given `llama3.2:3b`'s known run-to-run variability.

### Q: "Do I get paid extra for working nights?" (middle-ground prompt, second fresh attempt)
**A:** Correctly quoted the shiftwork definition (6pm-5am) and correctly identified that an incentive rate applies — an improvement over the garbled first attempt. But introduced two new errors: (1) **misattributed clauses** — credited the shift definition to "section 2.1" (actually 16.12) and the "outside ordinary hours" penalty rate to "section 1.3" (actually also 2.1); (2) **answered with the wrong rate table** — quoted the generic 40%/90% "outside ordinary hours" penalty rate instead of clause 16.12's own dedicated shiftwork incentive table (25%/47.5% weekday etc.), which is the actually-correct answer to this specific question.
**Verdict:** ❌ A third distinct flavor of the same underlying problem. Real numbers, real clause content, correctly *recognized* that an incentive applies — but wrong source clause attributed, and the wrong specific rate table selected for the situation.

## Closing conclusion on the "nights" investigation

Across **five separate attempts** spanning all three system prompts (original, strict-revised, middle-ground) and multiple fresh conversations, "Can I get paid extra for working nights?" never received a fully correct, complete answer. The failure mode changed each time — flat refusal, invented separate "night rate" caveat, garbled clause misreading, wrong-clause attribution, wrong-table selection — but a clean, accurate answer never appeared once.

This is strong evidence that the "nights" question specifically probes a **genuine capability limitation** of `llama3.2:3b` at this parameter size, rather than something further prompt-wording iteration is likely to fix. The core difficulty appears to be: (1) connecting an informal, everyday term ("night") to a specific numeric time range stated only in the document ("6pm to 5am"), and (2) reliably tracking which numbers/definitions came from which of several nearby, topically-similar clauses (16.12 Shiftwork, 2.1 Incentive Rates, 1.3 Payment of wages) once more than one is present in context together.

**Practical takeaway for this project:** prompt tuning has real, measurable value for *some* failure types (it did fix the compassionate-leave fabrication pattern from earlier, and the long-shift table-synthesis case), but is not a universal fix — some failures are better addressed by a larger/more capable chat model than by further prompt iteration on `llama3.2:3b`. Worth keeping this in mind before investing further time in prompt-only fixes for numerically-nuanced, multi-clause questions like this one.

---

## Isolating conversation history as a variable

**Question:** does accumulated (but unrelated) conversation history contribute to the "nights" failure pattern, separate from prompt wording?

**Setup:** Cleared `messages`, then asked three genuinely unrelated questions in sequence (promotion criteria, meal allowance, limited tenure) before asking "Do I get paid more for working nights?" as Q4 in the same conversation, under the middle-ground prompt.

**Q1-Q3 results:** All three fully correct — accurate promotion criteria summary, correct meal allowance figures ($20.01 / $18.14), correct limited tenure description (48hr minimum). No errors, no fabrication.

**Q4 ("nights") result:** A **new** error type — invented incorrect numbers outright ("6% Permanent / 15% Casual") that don't match the real table (15% Permanent / 37.5% Casual for Mon-Fri 6pm-11pm) at all, rather than the misattribution or garbling seen in earlier attempts.

**Conclusion:** Even with three unrelated, correctly-answered questions in history (nothing to blend or conflate with), "nights" still failed — this time via fabricated numbers rather than omission or misattribution. This suggests unrelated conversation history is **not** the primary driver of the "nights" failure pattern; the question itself appears to reliably challenge this model regardless of what surrounds it in the conversation. Combined with the earlier five-attempt investigation, this brings the total to **six independent failed attempts** at this question across varied prompts and conversation contexts, reinforcing that this is a standalone model capability limitation rather than a fixable artifact of prompt wording or history contamination.

---

## Broadening the investigation: other informal-concept mappings

### Q: "Do I get paid extra for working weekends?" (middle-ground prompt, same conversation as the history-isolation test above)
**A:** Quoted four rate figures from clause 2.1 — two correct (17.5%/40% for Saturday 7am-11pm), two incorrect: "15%/37.5% Saturday 7am-6pm" (actually the Mon-Fri 6pm-11pm rate) and "40%/62.5% Sunday 5am-7am" (actually the Saturday 5am-7am rate). Also oversimplified Sunday's multiple tiers into one flat "100% outside 5am-6am" rate, when the real table has several distinct Sunday tiers (80%, 65%, 50%, 75%, 100%).
**Confirmed via terminal output:** the full, correctly-parsed 2.1 Incentive Rates table (every row intact and accurate) was present in `prepared_data` — ruling out any chunking/storage/retrieval error. This is a pure generation-time failure.
**Verdict:** ❌ Every individual number quoted is real (nothing fabricated) — but roughly half are assigned to the **wrong row** (wrong day/time slot). This broadens the earlier "nights" finding from clause-level misattribution to **row-level misattribution within a single table**: whenever a table has many rows with similar structure (same columns, similar percentage ranges, different time windows), the model tends to shuffle which value belongs to which row. This looks like a structural table-reading weakness rather than something specific to the word "night."

### Q: "Do I get a break on a short shift?" (middle-ground prompt)
**A:** Correctly listed all five break-entitlement tiers with accurate hour brackets and break *counts* (0/0, 1/0, 1/1, 2/1, 2/2) — matching the source exactly in structure. But labeled meal breaks as "paid" throughout (e.g., "one paid meal break"), when the source table's column header explicitly reads "Unpaid meal break." Also didn't clearly commit to answering "short shift" directly (e.g., explicitly stating that under-4-hour shifts get zero breaks) — it restated the table and picked the 4-5hr tier without closing the loop on the actual question.
**Verdict:** ⚠️ No row-shuffling this time (single, less table-dense topic) — but a **recurring** paid/unpaid factual error (this is the second time this same slip has appeared, previously seen under the original prompt on the 10hr+ tier), plus a mild evasiveness in directly answering the question asked.

**Working theory on the paid/unpaid slip:** Likely a structural table-reading weakness rather than random noise. The real table states "paid rest break" and "unpaid meal break" as column *headers*, appearing once at the top — the word "unpaid" isn't repeated next to every row's meal break value. Combined with "paid" and "meal break" sitting immediately adjacent within each row (next to the genuinely-paid rest break), this may cause a kind of column-level attribute bleed, similar in spirit to the row-shuffling issue but occurring between adjacent columns rather than rows. General world-knowledge bias (many real workplaces do pay for meal breaks) may also nudge the model toward the statistically more common assumption when the specific textual anchor isn't strongly reinforced.

**Revised broader conclusion:** The "nights" investigation initially looked like an isolated informal-concept mapping problem. Testing "weekends" and "short shift" reveals a more general pattern: **this model struggles specifically with multi-row/multi-column tables that share structural similarity** (similar percentages, similar time-range formatting, adjacent paid/unpaid columns) — misattributing values between rows or columns even when the source data is fully correct and present. This is a more precise and more useful characterization of the limitation than "informal language" alone, and points toward a genuine table-reasoning weakness in this specific 3B model as the root cause, rather than a vocabulary/inference gap.

### Q: "If I work exactly 5 hours, do I get a meal break?" (boundary-condition test)
**A:** Correctly identified that a 5-hour shift falls under the "4 hours or more but no more than 5 hours" tier (not the next "more than 5 hours" tier), and correctly concluded no meal break applies at exactly 5 hours.
**Verdict:** ✅ **Genuinely precise result** — this is a real off-by-one boundary condition ("no more than 5" vs. "more than 5"), and the model got it right. This is a valuable positive counter-example: it suggests the earlier row/column-mixing failures aren't a general numeric reasoning failure, but specifically emerge when **many similar rows compete simultaneously** (e.g., the 10+ row Saturday/Sunday incentive table). A simple two-tier boundary check, by contrast, was handled correctly. This sharpens the working theory from "numeric reasoning is unreliable" to something more specific: **reliability degrades as table row-count/similarity increases**, rather than being uniformly weak across all numeric lookups.

### Q: "If I work a public holiday night shift, what do I get paid?" (multi-clause test — fresh conversation via new "Clear" button)
**Context:** Three chunks retrieved — 7.3 (Payment for absence on public holiday, a different scenario: *not* working), 2.1 (Public holiday work, an intro clause about voluntariness), and 16.12 (Shiftwork, containing the actual answer: Public Holiday row = 125%/147.5%).
**A:** "The excerpt does not provide explicit information on how much you would be paid for working a public holiday night shift... There is no specific mention of a public holiday rate for night shifts in the excerpts provided."
**Verdict:** ❌ **Significant finding.** This is not actually a multi-clause synthesis case — the correct answer (125%/147.5%) sits entirely within a single clause (16.12(e)'s Public Holiday row), the clearest, most directly on-point row in that whole table, with no ambiguity or competing figures to confuse it with. The model flatly denied this figure exists despite it being directly present. The two other retrieved chunks (7.3, 2.1) are topically adjacent but describe genuinely different scenarios (being absent on a public holiday; the voluntariness of public holiday work) rather than anything requiring combination with 16.12.

**New working theory — a "needle in a small haystack" distraction effect:** Rather than a multi-clause combination failure, this looks like retrieved-but-irrelevant chunks **distracting** the model from a correct, directly-relevant answer sitting in a different retrieved chunk. This is a different mechanism from the row/column-shuffling pattern found earlier (which involved misattributing real values within one dense table) — here, an entire correct row was overlooked in favour of concluding "no information exists," despite two of the three chunks being genuinely tangential. This suggests that **increasing the number of retrieved chunks doesn't just risk row-shuffling within tables — it may also directly increase the risk of overlooking a correct, simple answer** when it's surrounded by adjacent-but-irrelevant content.

**True multi-clause synthesis (combining facts from two genuinely necessary, complementary clauses) remains untested as of this session** — this result suggests it may be worth testing with only the minimum necessary clauses present, to isolate combination ability from the distraction effect discovered here.

### Q: "What's the total leave I could take if my spouse dies and I also need funeral travel?" (same-clause, multi-sub-clause synthesis test, fresh conversation)
**A:** Correctly cited both real figures — 5 days paid compassionate leave (6.7(a)) and unpaid funeral travel (7 days interstate / 30 days international, 6.7(c)) — with correct sub-clause attribution for both. Rather than fabricating a combined total or denying either component existed, it explicitly and accurately noted the document **doesn't specify how the two entitlements combine**.
**Verdict:** ✅ **Strongest multi-part synthesis result of the session.** Neither of the session's two dominant failure modes appeared — no invented total (the original prompt's typical fabrication pattern), no false "not present" claim on real content (the recurring omission/distraction pattern). Instead: accurate retrieval of both real components, correct sub-clause attribution, and honest acknowledgment of a genuine gap in the source. This is a clean example of the model succeeding at combining information *within* one clause's clearly delineated sub-parts (6.7(a) vs. 6.7(c)) — a much more successful structure than the dense, similarly-formatted rows of the incentive-rate tables, or clauses separated by irrelevant tangential content (as in the public holiday shift case).

## Updated overall theory (end of session)

Precision and structural clarity — not vagueness of vocabulary alone — appear to be the key variable across tonight's tests:
- **Works well:** simple factual lookups; boundary conditions in a small (2-5 row) table; combining clearly-labeled sub-clauses of the same numbered clause (6.7(a) + 6.7(c))
- **Fails unreliably:** dense multi-row tables with structurally similar rows (Saturday/Sunday incentive rates); informal concept-to-number mapping ("nights," "weekends") layered on top of those same dense tables; a correct answer surrounded by topically-adjacent-but-irrelevant retrieved chunks (public holiday shift case)

This suggests the earlier "informal language" framing was a symptom rather than the root cause — the deeper pattern is that **retrieval and synthesis reliability degrades as the number of structurally similar candidate values/chunks in context increases**, regardless of whether the question itself uses vague or precise wording.

---

## Investigating the public holiday night shift case further: retrieval bias vs. distraction

**Setup:** Re-ran "If I work a public holiday night shift, what do I get paid?" under `rank[:1]` (isolating a single chunk, no distractors possible) across multiple fresh attempts, this time printing full similarity scores for the top 5 candidates each run.

**Results across attempts (with scores):**
- Attempt 1 (three-chunk, `rank[:3]`): 16.12 present alongside 7.3 and 2.1
- Attempt 2 (`rank[:1]`): winner = 7.3
- Attempt 3 (`rank[:1]`): winner = 2.1
- Attempt 4 (`rank[:1]`, scores printed): **7.3 (0.7116), 2.1 (0.6797), 16.12 (0.6635), 9.5 (0.6505), 13.2 (0.6165)**
- Attempt 5 (`rank[:1]`, identical wording, scores printed): **identical scores to attempt 4**, confirming the ranking is deterministic, not random noise — the earlier attempts 2/3 disagreeing was very likely an artifact of testing at different points in the sequence (different chunk counts/context), not true instability.

**Rewording test:** Rephrased to emphasize "night shift" over "public holiday" ("What's my pay rate if I work a night shift that falls on a public holiday?"). Result: 16.12 moved from 3rd to 2nd place (0.6548), but **7.3 still won outright** (0.6937) by a similar margin (~0.04) as before.

**Conclusion — "attractor clauses":** 16.12 (the correct clause) never won the #1 spot in any single-chunk test, regardless of phrasing. 7.3 (Payment for absence on public holiday) consistently outranked it, likely because 7.3's content densely repeats generic pay/public-holiday vocabulary ("Team Member," "paid," "public holiday," "ordinary hours," "day or part-day") that broadly matches a wide range of related questions, even when it isn't the specific correct answer. This causes both a **wrong retrieval result** (7.3 selected instead of 16.12) and, when only 7.3 is present, a **garbled/incoherent generated answer** (one response even stated a Team Member is simultaneously "absent from work" and "working a night shift" — contradictory, matching neither the question nor the source cleanly).

**Connecting to earlier evidence:** This is the same pattern observed much earlier tonight, in the very first "nights" investigation — **"1.3 Payment of wages" (0.5959) outranked 16.12 Shiftwork (0.5907)** for "Can I get paid extra for working nights?", by a similarly narrow margin. Both "1.3 Payment of wages" and "7.3 Payment for absence on public holiday" are generically pay-topic clauses that appear to act as **semantic attractors** — scoring competitively against a broad range of pay-related questions due to their generic vocabulary density, even displacing the clause that actually contains the specific correct answer. This appears to be a genuine, repeatable limitation of pure embedding-similarity retrieval at this document's scale (99 chunks, no keyword-boosting, no re-ranking step) — not a model reasoning issue at all, since this happens entirely before the chat model ever receives anything.

### Confirming test: can 16.12 win outright with matching vocabulary? ("What are the shiftwork incentive rates for public holidays?", `rank[:1]`)
**Scores:** 16.12 Shiftwork (0.7183) — **winner**, 7.3 (0.7122), 2.1 Incentive Rates (0.6904), 2.1 Public holiday work (0.6886), 9.5 Rostering (0.6647).
**A (run 1):** "According to clause (e) of the excerpt, shiftworkers are entitled to a 125% incentive rate on their contract rate on Public Holidays." — fully correct.
**A (run 2, repeated):** "According to clause 16.12(e), the shiftwork incentive rates for public holidays are 125% and 147.50%, calculated on the Team Member's Contract Rate." — fully correct and more complete (included both the permanent and casual rates).
**Verdict:** ✅ **Confirms the resolution.** 16.12 is not permanently disadvantaged in retrieval — it wins decisively (by a much larger margin than 7.3's earlier wins) when the question's vocabulary closely matches the clause's own terminology ("shiftwork," "incentive rates"). This narrows the attractor-clause problem to a specific, well-understood condition: **generic phrasing that doesn't echo the target clause's own language is vulnerable to being outranked by broadly-worded "attractor" clauses, even when a more specific, correct clause exists.**

## Closing conclusion: the attractor-clause investigation

Across roughly ten attempts on the "public holiday night shift" / "paid extra for working nights" family of questions, a clear and well-evidenced picture emerged:
1. The correct clause (16.12 Shiftwork) is properly chunked, embedded, and stored — no data or pipeline defect.
2. When question vocabulary closely mirrors the clause's own terms, retrieval is accurate and confident (16.12 wins by its largest margin of the night: 0.7183 vs 0.7122).
3. When question vocabulary is generic/informal ("paid extra," "working nights," "what do I get paid"), broadly-worded "attractor" clauses (1.3 Payment of wages, 7.3 Payment for absence on public holiday) reliably outrank the specific correct clause by a narrow but consistent margin — a pure embedding-similarity effect, occurring entirely upstream of the chat model.
4. This is a genuinely fixable-in-principle limitation (via hybrid keyword+semantic search, query rewriting/expansion before embedding, or a larger/better embedding model) rather than a fundamental flaw in the RAG approach itself.

This closes out tonight's deep investigation into failure modes with a precise, actionable, and well-supported conclusion — a strong contrast to where the session started ("nights doesn't work, not sure why").

---

## Testing beyond the pay/public-holiday cluster: redundancy pay table (clause 12.3)

### Q: "How much redundancy pay would I get after 3 years of service?" (`rank[:3]`, fresh conversation)
**Retrieval:** 12.3 Redundancy Pay won decisively (0.6959 vs. next-best 0.5906) — no attractor-clause competition on this question, unlike the pay-rate questions. Confirmed via the retrieved chunk content: the full, accurate 12.3 table (weeks of redundancy pay by years of service, split by under-45 / 45-and-over columns) was correctly parsed and present in context.
**A:** "For Team Members aged 45 and over who have been employed for... 3 years but less than 4 years: $13/week... you would get $13 per week."
**Verdict:** ❌ Correct row identified (3-4 years), correct raw number pulled (13) — but **garbled the unit**, turning "13 weeks of redundancy pay" into a fabricated "$13 per week" that doesn't exist anywhere in the source (the real table has no dollar figures at all, only week-counts). Also silently assumed the "45 and over" column applied without the user specifying their age, and didn't flag that age affects the answer (under-45 would be 10 weeks, not 13).
**Significance:** Confirms the row/column-confusion theory generalizes beyond the time-of-day pay tables to a structurally different table (years-of-service × age-bracket), though this specific instance is a new variant — unit/meaning distortion (weeks → dollars) rather than a pure row-swap, plus an unflagged assumption about which column applies.

## Targeted prompt fix: table unit/column reading instruction

**Setup:** Added a targeted instruction to the middle-ground system prompt: *"When reading a table, carefully check the exact unit shown in each cell... and never substitute a different unit. If a table has multiple columns for different categories..., identify which column applies based on details the user has given you — if the user hasn't specified which category applies, explicitly state which column you're using and why, rather than picking one silently."*

**Test 1 (new prompt):** Re-ran the exact redundancy pay question. **Result: ✅ fully correct.** Both age-column figures given accurately (10 weeks under-45, 13 weeks 45+), correct unit ("weeks"), and explicitly flagged that age wasn't specified rather than silently picking one.

**Test 2 (reverted to old prompt, controlled comparison):** Same question, same `rank[:3]`, fresh conversation, old prompt (without the new instruction). **Result: ❌ worse than the original error** — wrong row selected entirely (2-3yr instead of the correct 3-4yr), values mixed between columns, and a fabricated source citation ("section 12.3(a) of the NES" — the NES is a separate legal instrument, not this document).

**Verdict:** ✅ **Confirmed, genuine, targeted fix.** The new instruction reliably corrected the specific mechanical table-reading errors (unit substitution, silent column-picking) it was designed to address, with a clean before/after comparison showing clear improvement.

**Test 3 (new prompt, different question — does the fix generalize to the "nights" attractor-clause issue?):** Re-ran "Can I get paid extra for working nights?" under the new prompt. Retrieval this time correctly included 16.12 Shiftwork. **Result: ❌ still failed** — despite 16.12's incentive rate table being present, the model still said "there is no mention of receiving extra pay specifically for working nights."
**Verdict:** Confirms the theory precisely: **prompt tuning fixed the mechanical table-reading error it was targeted at, but did not generalize to the separate "connect an informal concept to a specific number/table" reasoning gap.** These are two genuinely distinct failure modes requiring different fixes — one is fixable via explicit instruction, the other is not.

---

## Testing prose-only content (no tables): Formal Meetings (clause 15)

### Q: "Can I bring someone with me to a disciplinary meeting?" (new prompt, `rank[:3]`)
**A:** Correctly identified and accurately summarized that Team Members are entitled to a Representative who can attend and provide support — then, in the very next sentence, stated "it does not mention anything about bringing another person with them," directly **contradicting its own first sentence** (a Representative *is* another person being brought along).
**Verdict:** ❌ A new, subtler failure type — a genuine self-contradiction within a single answer, caused by failing to recognize that "someone" (the user's informal phrasing) and "Representative" (the document's formal term) refer to the same concept. This is the same underlying weakness seen in the "6pm ≠ night" case, but on **pure prose with no tables or numbers at all** — confirming this concept-mapping gap isn't table-specific, but a more general pattern across the model's reading comprehension.

## Further prompt refinement: terminology-mapping and self-consistency instructions

**Setup:** Added two more targeted instructions to the prompt: (1) explicitly checking whether informal user wording maps onto different formal document terminology before concluding info is absent, and (2) a final self-consistency check before finalizing the answer.

**Re-test (same Formal Meetings question, new prompt):** "According to the excerpt... they may be accompanied by a Representative... The excerpt does not explicitly state whether the person accompanying you is also considered a representative, but it seems they may be allowed to attend as a companion or supporter."
**Verdict:** ⚠️ **Partial, genuine improvement.** The direct self-contradiction from the earlier test is gone — the answer now consistently affirms the Representative entitlement throughout rather than reversing itself. A residual, unnecessary hedge remains (treating "the person accompanying you" as possibly distinct from "a representative," despite the excerpt's entire content describing exactly that role) — so the fix moved the failure from "confidently wrong/self-contradicting" to "correctly right but mildly over-cautious," a real reduction in severity without being a complete resolution.

## Final "nights" retest: newest combined prompt, `rank[:3]`

**Scores:** 1.3 Payment of wages (0.5942), 16.12 Shiftwork (0.5931), 3.1 Overtime conditions (0.5876)... — the attractor-clause gap between 1.3 and 16.12 has narrowed to just **0.0011**, essentially a coin-flip, with 1.3 still narrowly winning #1. Confirms the retrieval-level bias is completely unaffected by any of tonight's prompt changes — exactly as predicted, since it's a pure embedding-similarity effect upstream of the chat model.

**A:** Correctly cited all four core shiftwork incentive percentages (25%/40%/60%/125%, matching the real table exactly) and the correct shiftwork definition — the first fully numerically-correct "nights" answer of the entire session, with no fabrication. Fell short of a complete answer: never explicitly stated "yes, this counts as working nights," dropped the casual-rate column, and added one irrelevant detail from a different clause (payslip timing).

**Closing synthesis:** Because `rank[:3]` (not `[:1]`) was active, 16.12 still made it into context despite narrowly losing the ranking — providing a buffer against the retrieval-level attractor bias. Combined with the newest prompt's terminology-mapping instruction, this produced the best "nights" result of the night: real numbers, no fabrication, though still an incomplete/underconfident synthesis. This confirms the full layered picture built up over the session: **retrieval-level attractor bias persists regardless of prompt engineering, but a wider `rank[:3]` window plus better-targeted prompting can still meaningfully improve outcomes even when the top-ranked chunk is wrong** — a practical, actionable takeaway for the project going forward.

---

## New content area: Family and Domestic Violence leave (clause 6.15) — and a new architectural finding

### Q1: "How much family and domestic violence leave am I entitled to, and is it paid?" (`rank[:3]`, newest prompt)
**A:** "10 days of paid family and domestic violence leave at their Full Rate of Pay... single continuous period, two separate periods, or any other periods agreed... available in full at the start of each 12-month period." — fully accurate, matches clause 6.15(a) and (e) exactly.
**Verdict:** ✅ Clean, complete, correct — no issues at all.

### Q2 (follow-up, same conversation): "Do I need to provide evidence?"
**Retrieved chunks:** 15 (Formal Meetings), 6.13 (Jury service leave), 6.9 (Blood donor leave) — **none of these are clause 6.15**, and the correct sub-clause (6.15(h), which does address evidence requirements) was never retrieved.
**A:** "I don't have information on this from the provided excerpts. You will need to check if you need to provide evidence for family and domestic violence leave."
**Verdict:** ✅ **Correct given what was retrieved** — an honest, non-fabricated answer to a genuine retrieval miss, not a reasoning failure.

**New architectural finding — follow-up-question retrieval blindness:** The short follow-up "Do I need to provide evidence?" was embedded and searched **in isolation**, without the implicit context ("...for family and domestic violence leave") that a human (and the chat model itself, per the system prompt's instruction to use conversation history for understanding context) would naturally carry over from the previous turn. Because the retrieval step only searches based on the literal current question text — not an expanded/contextualized version of it — a short, pronoun-reliant, or context-dependent follow-up can fail to retrieve the relevant chunk entirely, even though a human reading the same two-message exchange would have no trouble understanding what's being asked.

**Practical implication:** This is a **retrieval architecture gap**, not a prompt or model reasoning issue — the fix would need to happen before the embedding/search step, e.g., by rewriting or expanding short follow-up questions using conversation history before embedding them (a common RAG technique sometimes called "query contextualization" or "question rewriting"), rather than embedding the raw follow-up text as-is. Worth flagging as a concrete, scoped item for future architectural work on this project, separate from every other finding logged tonight.

---

## New content area: Consultation on major workplace/roster changes (clause 9.3, Appendix 5)

### Q: "Does my employer have to consult me before changing my roster significantly?" (`rank[:3]`, newest prompt)
**Retrieval:** 9.3 Changing rosters (0.7303) narrowly beat 5 Consultation (0.7231) — both genuinely relevant, clean top-2 result.
**A:** Correctly identified the consultation obligation, the 14-day notice period, and the minimum-contracted-hours protection, all accurately citing clause 9.3(a). Also correctly identified the real exclusion for Team Members with "irregular, sporadic, or unpredictable" hours — but **misattributed this exclusion to "part (e) of clause 5"**, when it actually belongs to **9.3(e)**, the same clause already correctly cited earlier in the same answer.
**Verdict:** ⚠️ Substantively accurate throughout (correct rule, correct notice period, correct real exclusion) — but a genuine clause misattribution, mixing up two different clauses (9.3 and 5) that happen to share the same sub-letter "(e)."
**Significance:** Confirms the clause-misattribution pattern found repeatedly earlier tonight (e.g., the 15%/16.12 rate mixup, the "section 2.1/1.3" mixup) generalizes to **prose content**, not just tables — and this specific instance suggests a plausible mechanism: **the model may be pattern-matching on a shared sub-letter (e) across two different clauses**, rather than reliably tracking which parent clause number that sub-letter belongs to. This is a distinct, more precise hypothesis than the general "misattribution" pattern noted earlier, worth testing further if pursued.

---

## Adopting a structured test suite (external benchmark categories)

A more systematic 20-question "Gold Standard" test suite (covering direct retrieval, semantic wording, numerical reasoning, table interpretation, multi-clause synthesis, pronoun/context memory, retrieval precision, similar-terminology disambiguation, false assumptions, impossible questions, near-misses, cross-document reasoning, adversarial/citation prompts, and retrieval edge cases) was introduced to structure remaining testing. Categories already well-covered by tonight's organic testing (numerical reasoning, table interpretation, retrieval precision/clause numbers, pronoun/context memory) will be skipped in favor of genuinely untested categories: false assumptions, multi-clause synthesis, and adversarial/citation grounding.

**Separately, a hybrid retrieval improvement was proposed** (regex-detect clause-number patterns like `\d+\.\d+(\([a-z]\))?` in the user's question, boost/prioritize chunks whose `chunk_header` matches that exact clause number, blend with semantic similarity scoring) as a concrete architectural fix for the clause-number retrieval miss pattern (e.g., 16.12(a)(ii) never retrieving) confirmed multiple times tonight. This is agreed to be a sound, well-scoped next engineering task — separate from the attractor-clause bias (a different mechanism: generic vocabulary overlap, not a missing specific number) — recommended for a future coding session rather than prompt-only testing.

### Q: "Where does it say I get double time on Saturdays?" (false-assumption test, `rank[:3]`, newest prompt)
**A:** Correctly and directly refuted the false premise ("it doesn't specify that you receive 'double time'"), then accurately cited the real Saturday incentive rates (40%/62.5% before 7am; 17.5%/40% for the later window) instead of inventing a fake double-time rule. One minor internal inconsistency: described the second bracket's boundary as "after 6:00am" when it should be "7:00am" (the number pairing itself was still correct, just the restated boundary wording was imprecise).
**Verdict:** ✅ **Clean, strong pass** — correctly resisted a plausible-sounding false premise even with real, nearby numbers (Saturday incentive rates) available to potentially misuse, and gave an accurate correction instead of confabulating. First false-assumption-category test of the night, and the model handled the "bait" well.

### Q: "I worked until 11:30pm without notice. Do I receive overtime, transport reimbursement and a meal allowance?" (multi-clause synthesis, `rank[:3]`, newest prompt)
**Scores:** 4.1 Meal allowance (0.7053) — retrieved; 11.2 Timing of breaks (0.6335) — retrieved; 16.12 Shiftwork (0.6168) — retrieved; **4.5 Transport reimbursement (0.6114) — NOT retrieved, ranked 5th**; **3.1 Overtime conditions (0.5810) — NOT retrieved, ranked 8th**.
**A:** Called the $20.01 meal allowance an "overtime payment," said transport reimbursement and true overtime pay were "not explicitly stated."
**Initial read:** Appeared to be a 3-way synthesis failure (wrong label, two clauses dismissed).
**Corrected diagnosis after checking scores:** This question genuinely requires 3+ non-adjacent clauses (meal allowance, transport reimbursement, overtime pay), but `rank[:3]` structurally cannot supply more than 3 chunks — and two of the three needed clauses (4.5, 3.1) didn't make the cut at all. Given that, saying transport reimbursement and overtime pay were "not explicitly stated" was actually **honest and correct** — the model genuinely didn't have that content. The **one real error**: it mislabeled the $20.01 meal allowance (4.1, which *was* correctly retrieved) as an "overtime payment," when it's actually a separate meal-allowance entitlement triggered by overtime-without-notice, not an overtime wage rate itself.
**Verdict:** ⚠️ Reframed from "poor synthesis" to a **retrieval breadth limitation** (this specific question needs more than 3 chunks to answer completely) combined with **one genuine mislabeling error** (correctly retrieved content given the wrong category name). A cleaner, more precise diagnosis than the initial read — a good reminder to always check retrieved-chunk scores before judging a "failed synthesis" as a pure reasoning problem.

---

## Citation/adversarial testing

### Q1: "How much is the meal allowance?" (`rank[:3]`, newest prompt)
**A:** Invented fake bracket thresholds not present in clause 4.1 at all ("exceeding 4 hours but less than 5" → $20.01; "more than 5 but less than 7" → additional $18.14), then summed to $38.15.
**Cross-check against real clause 4.1:** $20.01 is actually triggered by working **more than 1 hour** of overtime without notice (not "4-5 hours"); $18.14 is a further allowance if that overtime **exceeds 4 hours** (not "5-7 hours"). The final total ($38.15) happens to be numerically correct for >4hr overtime, but the reasoning path to reach it used fabricated thresholds.
**New pattern identified — cross-clause bracket bleeding:** The fake "4-5 hours" / "5-7 hours" brackets closely resemble the real bracket structure from a *different* clause (11.1 Break entitlements' "4 hours or more but no more than 5," "more than 5 hours but less than 7"), which was also present in context. This looks like a new variant of table confusion — not row-shuffling *within* one table, but an entire bracket/threshold **structure leaking from one table into the description of an unrelated table**.
**Verdict:** ❌ Correct final number, fabricated reasoning/thresholds — a genuinely deceptive-looking error since the bottom-line figure checks out even though the stated logic to get there is invented.

### Q2 (adversarial follow-up, same conversation): "I made a mistake. There is no mention of a meal allowance in the excerpts provided." / "Are you sure?"
**A:** The model **fully reversed itself**, abandoning its previous answer and falsely declaring the entire meal allowance clause doesn't exist in the excerpts.
**Initial diagnosis:** Interpreted as adversarial-pressure-induced false denial — the model capitulating under pushback rather than re-verifying.

**Correction after checking retrieval scores:** The scores for this follow-up were checked and tell a very different story: **8 Types of Employment (0.424), 16.2 (0.397), 14.2 (0.397), 13 (0.395), 10 (0.386), 16.1 (0.386), 7.1 (0.384), 16.7 (0.383)** — all low-confidence (<0.43) and **completely unrelated** to meal allowances, a stark contrast to the 0.73 score 4.1 received on the original question. This confirms the short adversarial follow-up ("Are you sure?") was embedded and retrieved **in complete isolation from the original question's context**, surfacing essentially random noise chunks rather than 4.1 again.

**Revised verdict:** ✅ **Not adversarial-pressure capitulation — a second, independently confirmed instance of follow-up-retrieval blindness** (first found on "Do I need to provide evidence?" earlier tonight). The model wasn't folding under pressure or lying about known-correct information; it was honestly (if unhelpfully) reporting that meal allowance isn't mentioned in the *actual chunks it had been given this turn* — which were wrong chunks entirely, due to the same retrieval architecture gap. This is a more precise and less alarming diagnosis than the initial read, and reinforces that **short, context-dependent follow-ups are a systematic, repeatable failure point** requiring the query-contextualization/rewriting fix identified earlier — not a trust or self-consistency issue on the model's part.

**Practical note:** This is a trickier problem to solve than most of tonight's findings, precisely because it requires an architectural change (rewriting/expanding short follow-ups using conversation history *before* embedding them) rather than a prompt tweak — the model has no way to compensate for retrieval receiving the wrong input in the first place.

**Recommended fix (deferred to a future coding session):** Of the candidate solutions considered — (1) falling back to the previous turn's chunks when a new follow-up's retrieval scores are all low-confidence, (2) using an extra LLM call to rewrite short follow-ups into standalone questions before embedding, (3) a cheap heuristic that prepends the prior question's text when the new message is short and/or pronoun-heavy — **option 3 is the preferred starting point**, given CPU-only inference makes an extra LLM call (option 2) costly, and it's simpler to implement and reason about than option 1's confidence-threshold fallback. This is logged as a scoped future task, not something requiring resolution in this session.

---

## Closing batch of tests

### Q: "Which relationship receives four days compassionate leave?" (table lookup)
**A:** "Step-parent, foster-parent, parent-in-law, sibling-in-law, stepchild, grandparent or grandchild" — fully correct, matches clause 6.7(a)'s 4-day tier exactly, all six categories included.
**Verdict:** ✅ Clean, complete pass.

### Q: "What's the difference between Store Team Member and Supervisor?" (Appendix 1 classification retrieval)
**A:** Opened with "the excerpts do not explicitly state the difference," then immediately gave an accurate, correct description of both roles (Supervisor: supervising/training/overseeing a department; Store Team Member: customer service/register/cleanliness).
**Verdict:** ❌ **Second confirmed instance of the same self-contradiction pattern** first found on the Formal Meetings question earlier tonight (say "not stated" then immediately demonstrate the answer accurately). Notable that this occurred **despite** the self-consistency prompt instruction added earlier, which had appeared to help on the Formal Meetings retest — indicating the fix reduces but does not reliably eliminate this pattern.

### Cluster: history-dependence, false-assumption correction, and impossible-question refusal

**Q1a: "What's the difference between overtime and incentive rates?" (accidentally run twice — once with prior conversation history present, once with a clean/history-free context)**
- **With history:** Correct but thin — only captured the overlap rule (incentive rate wins if it exceeds overtime rate), never explained the actual core distinction.
- **Without history:** Substantially more complete and accurate — correctly distinguished overtime (triggered by *extra hours worked*, e.g. over 152hrs/4-week cycle) from incentive rates (triggered by working *specific time periods*, e.g. early mornings/evenings/Sundays, regardless of total hours), with a reasonable illustrative example.
**Significance:** A **new finding** — conversation history can sometimes **reduce** answer completeness/quality, not just cause topic-bleed or misattribution as seen elsewhere tonight. A subtler and previously undocumented cost of retained history.

**Q1b: "Can I cash out all five weeks of my annual leave?" (false-assumption test, run both with and without history)**
Both versions correctly identified the false premise and cited the real limits accurately (max 2 weeks per 12-month period, minimum 4 weeks must remain, Bunnings' discretion). The history-free version added one small bonus clarification (no stated cap on repeat use) without correcting any error.
**Verdict:** ✅ Strong, consistent pass in both conditions — no history-dependent quality difference here, unlike Q1a.

**Q1c: "What's the Wi-Fi password?" (impossible-question refusal test)**
**A:** "There is no mention of the Wi-Fi password... This Agreement appears to be related to employment terms and conditions, rather than providing details on Bunnings' network access information."
**Verdict:** ✅ Clean, appropriate refusal — correctly recognized the question as out-of-scope for the document rather than guessing or hallucinating an answer.

---

## Retrieval edge case: multi-location search, and a three-attempt self-correction sequence

### Q: "Which section mentions grandchild?" (`rank[:3]`, newest prompt)
**Scores:** 15 Formal Meetings (0.5389) — top result; 6.7 Compassionate leave (0.5332) — close second; six other unrelated chunks below 0.52.

**Attempt 1:** Claimed clause 15 mentions "grandchild" via a fabricated "step-grandchild, 4 days" detail — **entirely invented**; clause 15's real content (Representative rights at meetings) has no such content anywhere. Also gave a muddled, incomplete description of 6.7's genuine "grandchild" mentions.

**Attempt 2 (user follow-up asking for correction):** Replaced the fabrication with a **new** fabrication — "step-grandparent in clause (ii)" of clause 15 (still nonexistent) — plus a wrong sub-clause citation for 6.7 ("(b)(iii)" instead of the correct "(a)"), plus a bizarre, essentially nonsensical third claim that clause 16.1 ("Who are the parties to this Agreement," about legal entities and brand names) "may include items related to grandchildren" via loose word-association with "Bunnings Trade."

**Attempt 3 (user pushed for correction again):** Genuinely retracted the clause 15 fabrication this time (real progress) — but still cited the **wrong sub-clause** for 6.7 ("(b)(iii)" again, should be "(a)"), and understated the true count (grandchild actually appears in 6.7(a) in two separate places — the 4-day relationship tier and the stillbirth/miscarriage tier — not just once).

**Verdict:** ❌ **Significant, compounding finding.** Retrieval correctly surfaced both genuinely relevant chunks (15 narrowly outranking 6.7, both present in context) — but the "find every mention" task type is fundamentally mismatched to a single-best-answer RAG pipeline, and critically, **repeated self-correction attempts did not reliably converge toward the truth**: attempt 2 was worse than attempt 1 (three fabrications instead of one), and even attempt 3 — the best of the three — still contained a real citation error. This suggests that when pushed to retry on a task type the pipeline isn't built for, the model doesn't default to increased caution; it can instead generate a wider spread of confident-sounding but incorrect claims across multiple retries.

---

## Final test cluster: near-miss handling, and table-lookup run-to-run variance

### Q: "Can I take leave if my dog dies?" (near-miss test, run with and without history)
**With history:** Fully correct — accurately listed all real relationship categories (including the complete 4-day tier) before correctly concluding pets aren't covered. No hedging, no fabrication.
**Without history:** Also correctly concluded pets aren't covered, but less complete (only listed the 5-day tier, omitted the 4-day tier), plus an odd, unhelpful "(partially relevant)" parenthetical.
**Verdict:** ✅ Clean pass in both conditions — neither version fell into the trap of stretching compassionate leave to cover pets. **Revises the earlier history-dependence finding**: this time the with-history version was *more* thorough, the reverse of the overtime/incentive-rates result — confirming history's effect on completeness is not consistently positive or negative, but appears to vary by question, making it unpredictable rather than a rule that can be designed around.

### Q: "I'm a casual Supervisor. What's my hourly rate?" (single-cell table lookup, 4 attempts — 1 with history, 3 without)
Real answer: $35.54 (casual rate, includes 22.5% loading).
- **Attempt 1 (history):** $29.01 — wrong column (quoted the base rate, not casual), plus a self-contradiction (said "no direct entry for Supervisor" then quoted a real Supervisor figure).
- **Attempt 2 (no history):** $34.82 — wrong row entirely (this is actually the Forklift Coach casual rate).
- **Attempt 3 (no history):** $35.54 — correct, with accurate explanation of the casual loading.
- **Attempt 4 (no history):** $35.54 — correct, consistent with attempt 3.
**Verdict:** ⚠️ Mixed reliability even on a single-cell lookup (not even a range) — 2 of 4 attempts wrong, including one genuine row-mixup pulling from a different job classification entirely.

**Follow-up clarification (important for interpreting all of tonight's repeated-attempt tests):** `llama3.2:3b` has no memory or learning between calls — clearing the database only resets the local SQLite tables, not the model. Each `ollama.chat()` call is fully independent; apparent "improvement" or "degradation" across repeated attempts (as seen here and in the grandchild multi-location test) reflects the model's inherent generation randomness (sampling variance), not genuine learning or convergence toward correctness. Repetition alone is not a reliable path to a correct answer.

---

## Session close: summary and next steps

This session evaluated the RAG pipeline (Flask + Ollama + SQLite, `llama3.2:3b` chat, `nomic-embed-text` embeddings) against a structured, broad set of test categories, producing a well-evidenced taxonomy of confirmed findings:

**Retrieval-layer issues (upstream of the chat model, unfixable via prompting):**
- Attractor-clause bias — generic, vocabulary-dense clauses (e.g., 1.3 Payment of wages, 7.3 Payment for absence on public holiday) reliably outrank specific correct clauses by narrow but consistent margins on generically-worded questions; resolved when question vocabulary matches the target clause's own terminology.
- Clause-number-specific queries (e.g., "16.12(a)(ii)") fail to retrieve the exact clause.
- Follow-up-question retrieval blindness — short, context-dependent follow-ups are embedded in isolation and can retrieve completely unrelated chunks, confirmed independently on two different follow-up types.
- Multi-location "find every mention" queries are structurally mismatched to a top-3, single-answer retrieval design.

**Generation-layer issues (partially addressable via prompting):**
- Table row/column confusion and unit substitution — **successfully fixed** via a targeted prompt instruction (confirmed with a clean before/after comparison).
- Informal-to-formal concept mapping gaps (e.g., "nights" ≠ recognized as 6pm–5am shiftwork) — **partially improved**, not fully resolved, by prompt tuning.
- Self-contradiction within single answers — confirmed twice (Formal Meetings, Store Team Member/Supervisor); **partially reduced** but not eliminated by a self-consistency prompt instruction.
- Cross-clause bracket/structure bleeding — real content from one table leaking into the description of a different, simultaneously-retrieved table.
- Self-correction under repeated user pushback does not reliably converge toward accuracy — can compound fabrication rather than fix it.
- History-dependence on answer completeness — effect varies by question (sometimes better, sometimes worse with history present), not a consistent, predictable pattern.

**Recommended next steps (for a future coding session, not further prompt-only testing):**
1. **Hybrid retrieval**: regex-detect clause-number patterns (e.g., `\d+\.\d+(\([a-z]\))?`) in user questions; boost/prioritize chunks whose `chunk_header` matches exactly; blend with semantic similarity scoring. Directly targets the clause-number retrieval-miss pattern.
2. **Follow-up query contextualization**: implement the lightweight heuristic (prepend the prior question's text when a new message is short and/or pronoun-heavy) identified as the preferred starting fix for follow-up retrieval blindness, given CPU-only inference makes an LLM-based query-rewriting approach costly.
3. Consider whether the current `rank[:3]` window is sufficient for genuinely multi-clause questions (the transport reimbursement/overtime/meal allowance test showed a real case needing 5 chunks, not 3) — may warrant a dynamic or slightly larger default window.
4. Retain the current middle-ground prompt (with the table-reading and terminology-mapping additions) as the standing default — it demonstrated genuine, confirmed improvements over both the original and strict-revised versions tested earlier.

---

---

| Stage | Behavior |
|---|---|
| Whole-document, no chunking | Truncation silently dropped content; model sometimes admitted it, sometimes hallucinated instead |
| Chunking + embeddings + top-3 retrieval | Correctly finds and answers from the right clause regardless of its position in the document (tested successfully as deep as page 9 and page 40+) |

**Known remaining rough edges:**
- Occasional fabricated extra detail even when the core answer is correct (e.g., invented section numbers, invented extra leave entitlements)
- Chat history can bleed into new answers, causing topic conflation
- **Retrieval can succeed while generation still fails** — confirmed twice now (shiftwork question, ranked 2nd/99; compassionate leave question, ranked 1st/99) — the correct chunk can score highly and still get misread, ignored, or embellished by the small local model
- No formal testing yet on questions that genuinely require *multiple* clauses at once (top-3 retrieval may miss one if the answer spans more than 3 chunks)

# prompt v4 + addition of rank :5 if diff < 0.1>
You are a helpful, professional assistant designed to help users find information in documents. Use the conversation history only to understand what the current question is referring to, not as a source of facts. Base your answer only on information explicitly present in the document excerpts below — you may combine, summarise, and reasonably apply that information (for example, working out which row of a table applies to a specific number, or recognising that a time range like '6pm to 5am' corresponds to night hours), but do not add facts, figures, or details that are not present in the excerpts. If the excerpts genuinely do not contain the answer, say so explicitly rather than guessing.
If a table has multiple columns and/or rows, identify which column/row applies based on details the user has given you — if the user hasn't specified which category applies, explicitly state which column you're using and why, rather than picking one silently
Treat ranges as strict mathematical conditions. Check which range the user's situation falls into. Do not assume adjacent ranges overlap. Pay close attention to words like 'more than', 'less than', 'no more than', 'at least', and 'up to'. If a value exactly matches a boundary, determine which condition explicitly includes that boundary.
Be consistent. Don't state something and contradict it. Don't state something is absent and quote it. If you are not sure, say you are not sure, instead of choosing an answer.
If there is pushback on something you stated, recheck the previous excerpts and correct only from that information. Don't introduce new details to satisfy the user. If the recheck doesn't support a correction, say so. When asked where or whether the document mentions something, only report occurences you can literally see in the excerpts - never inferred, assumed, or plausible-sounding ones.

## Testing Questions:

# "How much is the meal allowance if overtime exceeds 4 hours?" (clause 4.1, page 12)
Test 1:
    The excerpt states that for overtime exceeding 4 hours, a further meal allowance of $18.14 will be paid.
    >Correct, however, doesn't take the original $20.01 paid after more than 1 hour into account

Test 2:
    According to excerpt 4.1(a), if overtime work exceeds 4 hours, a further meal allowance of $18.14 will be paid in addition to the initial meal allowance of $20.01.
    >Correctly adds both figures.

Test 3:
    The meal allowance for overtime exceeding 4 hours is $18.14.
    >Again, misses the connection to the base payment.

Adding "Check whether multiple amounts or entitlements apply together and combine them. For example, a base rate in addition to a further rate"

Test 4:
    According to excerpt (b) under heading 4.1 Meal Allowance: "Where the overtime work exceeds 4 hours a further meal allowance of $18.14 will be paid."
    >Unable to retrieve the initial rate

Test 5:
    According to section (b) of the excerpt under "Meal allowance" heading, if overtime work exceeds 4 hours, a further meal allowance of $18.14 will be paid on top of the initial meal allowance of $20.01
    >Correctly calculated

Test 6:
    The total meal allowance for overtime exceeding 4 hours would be $20.01 + $18.14, which equals $38.15.
    >Correct calculation, plus final figure. Addition seems to have improved generation, but still can miss. Worth keeping in. model now performs arithmetic on retrieved figures; correctness of that arithmetic is untested beyond n=1

# "I'm a casual Supervisor. What's my hourly rate?" ×3 runs → table column/row block (your log shows 2-of-4 variance on this one, hence multiple runs)
Test 1:
    Based on the table provided in section 1.1 of the document, I found your role as "Supervisor". According to that table, your hourly rate for Base Rate is $29.01 and for Casual Hourly Rate (which includes the casual loading equivalent to 22.5% of the Base Rate) is also $35.54.
    >Weirdly worded - but got there in the end.

Test 2:
    To determine your hourly rate as a Casual Supervisor, we need to check the table provided in the document excerpt under 1.1 Classification types and hourly wage rates. The table specifies the minimum hourly Base Rates and minimum hourly casual rates for various roles, including supervisors. According to the table, there is no specific entry for "Supervisor" or "Casual Supervisor". However, we can find the entry for "Team Member" which has a corresponding role of "Store Administrator". Since you mentioned that your title is "Supervisor", it's possible that this refers to the equivalent role in the document. In this case, I'll assume that the hourly rate for a Store Administrator (which might be the closest equivalent) would apply. For Store Administrator, the table lists the minimum hourly Base Rate as $28.42 and the minimum hourly casual rate as $34.82. However, we need to consider if there's any adjustment made specifically for Casual Supervisors or the equivalent role in this case. Unfortunately, with the information provided from the document excerpt under 1.1 Classification types and hourly wage rates, I am not able to confirm that the casual loading is specifically for the Supervisor role
    >Just wrong.. made assumptions, even though the information is there.
        From the terminal: 'content': 'This is an excerpt from the uploaded document, under the heading 1.1 Classification types and hourly wage rates: (a) The table below specifies: \n(i) grades and roles covered by this Agreement; and \n(ii) minimum hourly Base Rates, and minimum hourly casual rates, payable under this \nAgreement from the first full pay cycle after 1 September 2023. \n Bunnings Warehouse Bunnings Trade Hourly Wage Rates September 2023 \nGrade Role Role Base Rate Casual Hourly \nRate \nTeam Member Store Team Member Trade Team Member $27.00 $33.08 \nCustomer Service Operator \nTeam Member \n(Expert) \nExpert Team Member \nN/A $27.43 $33.60 Special Orders , Service  \n& Trade Desk Team \nMember \nSpecialists Forklift Operator Forklift Operator \n$28.15 $34.49 \nKitchen Specialist Trade Administrator \nActivities Organiser N/A \nStore Administrator \nInventory Specialist \nForklift Coach Forklift Coach \n$28.42 $34.82 Trade Qualified TM Trade Qualified Customer \nService Operator \nTrade Specialist N/A *****\nSupervisor Supervisor Supervisor $29.01 $35.54 \n******(b) Descriptions for each role are set out in Appendix 1.  \n(c) Casual Team Members are entitled to a casual loading equivalent to 22.5% of the Base Rate, \nwhich is included in the casual hourly rates in the table above. This loading is in lieu of all \nentitlements that full-time and part-time Team Members receive under the NES (except where \notherwise provided for in the Agreement).  \n(d) No Team Member will suffer any reduction in their Contract Rate following the approval of this \nAgreement.'

Test 3: 
    According to the table provided under 1.1 Classification types and hourly wage rates, for a Grade Role of "Supervisor", the Base Rate is $29.01. Since you mentioned you are a Casual Supervisor, I will use the column for Casual Hourly Rates, which is also $34.82 (as there's no separate entry specifically indicating "Casual Supervisor" or providing both the base and casual rates).
    >Incorrect again, model seemingly pulling the $34.82 figure, as done once in previous tests, now twice in these tests - this is for Specialists at a casual rate.
        
>>>Noted that tables get parsed incorrectly during the reading of pdf. Implementing different library.

Ran experiment parsing table info into terminal chatting to llama directly Now score it properly, because the headline number is misleading. Final answers: markdown 5/5, sentences 5/5. A tie — if you only read the last line of each response. But you're an evaluator now, so read the reasoning, and a real difference appears:
Markdown, Store Administrator run 1: "Store Administrator is not listed as a separate entry under any category, but rather falls under Specialists..." — false. Store Administrator has its own row in the table you pasted. Right answer, fabricated justification.
Markdown, run 2: "there is no direct entry for Store Administrator. However, there is an entry for Inventory Specialist with a Base Rate of $28.15..." — worse: it denied the row exists, then reasoned to the correct figure via a different role's row. Correct by coincidence of shared rates. If Store Administrator had sat one tier over at $28.42, this exact reasoning chain would have produced a wrong answer with a confident explanation.
Sentences, both Store Administrator runs: "The base rate for a Store Administrator is $28.15." Clean, direct, one-line, faithful to source. No confabulated pathway.
So the finding isn't "5/5 vs 5/5," it's: markdown produced the right numbers through unreliable reasoning that got lucky; sentences produced them through direct lookup. The 2D structure still costs the model — it "loses" rows inside the grid and reconstructs them by inference. That fragility is exactly what turns into your historical $34.82 failures when the rates don't happen to match. And this connects to your log's self-contradiction taxonomy entry: "no entry exists... here's its value" is the same disease.
Standard caveat, applied to myself this time: n=2 per format on the hard question. Small sample, directional not proof. But the direction agrees with the failure history, the embedding argument (per-fact sentences give retrieval individually-addressable facts), and the 1D-vs-2D theory. Three independent lines pointing the same way is how I'd make the call: sentences win. That's my verdict — veto it with a reason if you disagree, otherwise it's decided.

# AI Document Assistant — Q&A Testing History

A record of questions asked against the Bunnings Retail Enterprise Agreement 2023, tracking how answer quality evolved as the project moved from "dump the whole document in" → chunking → embeddings → real semantic retrieval.

---

## Before RAG (whole-document context, no chunking)

These tests exposed the core problem: the model could only "see" whatever fit inside the context window, and it didn't reliably admit when content was missing — sometimes it hallucinated instead.

### Q: "What are the overtime conditions for Bunnings?"
**Context:** Very first real test, full 48-page PDF stuffed into one prompt, default ~4k context window.
**A:** Gave a vague, generic summary of the *whole document* (trial periods, IFAs, consultation, dispute resolution) — completely ignored the actual question. Never even mentioned overtime specifics.
**Verdict:** ❌ Failed — question effectively ignored, likely due to document positioning + truncation.

### Q: "What does shiftwork entail?" (asked twice, at 8192 token context)
**A (1st attempt):** Fabricated a generic definition — "rotating shifts," "healthcare, manufacturing, transportation," none of which is in the real document. No real clause content used.
**A (2nd attempt, after re-testing):** Different fabricated generic answer — mentioned "hospitals," "10pm to 6am" (the real clause says 6pm–5am), again no real content.
**Verdict:** ❌ Failed — clean hallucination both times, even with an explicit "say so if you don't know" system prompt instruction in place. Proved that prompting alone doesn't stop hallucination on a small local model.

### Q: (about Pre-Agreement Base Rates, clause 16.13(t), page 38)
**A:** "I'm not able to find the specific information about 'Pre-Agreement Base Rates' in the provided document. Could you please provide more context..."
**Verdict:** ✅ Honest — correctly admitted it didn't have the content, rather than guessing.

### Q: (about the Kitchen Specialist role, Appendix 1, page 40)
**A:** Correctly listed the real duties — kitchen design assistance, using the design planner, developing customer relationships — matching the source almost verbatim.
**Verdict:** ✅ Accurate.

### Q: (about Store Team Member duties)
**A:** Answered with real document content — but attributed it to the wrong role. The duties listed ("receiving visitors," "answering phone calls," "data entry") actually belong to *Store Administrator*, not *Store Team Member*, in the same table.
**Verdict:** ⚠️ Partially correct — real content retrieved, but misattributed. A subtler failure than outright hallucination: confident, well-formed, and wrong.

### Q: (about the dispute resolution procedure, clause 16.11/Appendix 6, near the end of the document)
**A:** Near-verbatim, fully accurate reproduction of the real clause (a) through (h).
**Verdict:** ✅ Accurate — this content happened to survive truncation since it was near the end of the prompt.

---

## After chunking + embeddings + semantic retrieval (the real RAG pipeline)

Once chunking, embeddings, and top-3 relevance ranking were wired in, retrieval started pulling the *correct* clause regardless of where it sat in the document.

### Q: "What is a trade administrator?"
**A:** Correctly said it couldn't find a specific "Trade Administrator" definition, while noting related roles that do exist (Trade Specialist, Trade Qualified, Forklift Coach).
**Verdict:** ✅ Honest — accurate acknowledgment of missing/different content.

### Q: "What does a supervisor do?" / "What roles does a supervisor have?"
**A:** Correctly listed real Supervisor duties (supervising/training team members, overseeing a department, supporting store leadership) — but also fabricated some extra detail ("Section 5.1", "Section 5.2", disciplinary action, record-keeping) not present in the source.
**Verdict:** ⚠️ Mixed — real core content correct, but padded with invented section numbers/details.

### Q: "What is the role of a supervisor?"
**A:** Clean, accurate answer — matched the real Supervisor clause exactly, no fabricated extras this time.
**Verdict:** ✅ Accurate.

### Q: "What are the Provisions Specific to Bunnings Trade Centres?" + "What are the overtime conditions?"
**Context:** First real test after the full embedding + ranking pipeline went live.
**A:** Retrieved top chunks were **3.1 Overtime conditions**, **3.2 Overtime pay**, **3.3 Reasonable overtime** — all correct top-3 matches out of 99 stored chunks. Answer content was accurate and near-verbatim on the overtime specifics, though it opened by conflating the earlier Trade Centres question with the new one, and mislabeled the clause number.
**Verdict:** ✅ Retrieval fully correct — first confirmed success of real semantic search. Minor rough edge: old chat history bleeding into the new answer's framing.

### Q: (about incentive rates — page 9, clause 2.1)
**A:** Accurate, detailed breakdown of real incentive rate percentages by day/time (30%/52.5% weekday early morning, 40%/62.5% Saturday, up to 125%/147.5% public holidays, etc.) — all figures matched the source table correctly.
**Verdict:** ✅ Accurate — confirmed retrieval works across different topics, not just the overtime test.

---

## Summary

| Stage | Behavior |
|---|---|
| Whole-document, no chunking | Truncation silently dropped content; model sometimes admitted it, sometimes hallucinated instead |
| Chunking + embeddings + top-3 retrieval | Correctly finds and answers from the right clause regardless of its position in the document (tested successfully as deep as page 9 and page 40+) |

**Known remaining rough edges:**
- Occasional fabricated extra detail even when the core answer is correct (e.g., invented section numbers)
- Chat history can bleed into new answers, causing topic conflation
- No formal testing yet on questions that genuinely require *multiple* clauses at once (top-3 retrieval may miss one if the answer spans more than 3 chunks)

---

## Prompt engineering phase (v4)

The system prompt was rebuilt from scratch: the bloated v3 was trimmed to a lean spine, then only instructions with test evidence behind them were grafted back (table row/column reading, ranges/boundaries merged from two duplicate blocks, self-consistency, pushback handling, literal-mentions rule). Principle adopted: **every prompt line must trace to a documented failure, and every confirmed fix must trace to a prompt line.** Prompt versions are now assets — saved to a `prompts/` folder, with each test result attributed to the version that produced it.

### Q: "How much is the meal allowance if overtime exceeds 4 hours?" (clause 4.1) — ×6 runs
**Before stacking instruction (×3):** 1/3 complete. Two runs correctly identified the $18.14 further allowance but silently dropped the $20.01 base — a *completeness* failure, not a ranges failure (the boundary logic was right every time).
**After adding "check whether multiple amounts apply together and combine them" (×3):** 2/3 complete, including one run that summed to $38.15 unprompted.
**Verdict:** ⚠️ Directionally improved, small n — logged as probabilistic completeness weakness, not "fixed." Attribution ambiguity noted honestly: old-prompt baseline was n=1.
**New observation:** the stacking instruction licensed the model to do arithmetic. Correct this time; arithmetic reliability on a 3B model is untested beyond n=1. New test category flagged.

---

## The ingestion-layer discovery (the table saga)

**The single most important finding of the project so far.** A casual-Supervisor rate test printed its retrieved context to the terminal, revealing that pypdf's `extract_text()` was destroying table structure at parse time — interleaving columns into "table soup" where a rate like $34.82 floats next to the wrong role. This reframed the entire table-failure family (row/column confusion, unit substitution, misattribution): **they were never model or prompt failures. The model was reconstructing tabular meaning from shuffled words.**

Three layers now recognised, in pipeline order: **ingestion → retrieval → generation.** Diagnose upstream first.

### Key sub-findings
- **pypdf vs pdfplumber:** pypdf destroys structure (unrecoverable); pdfplumber preserves cells in a messy grid (recoverable). Evaluation lens: don't ask "is this clean?" — ask "is the information still *present*?" Buried is a code problem; absent is a dead end.
- **Corruption is consistent** across tables (phantom columns, continuation-row fragments, blank-cells-inherit-from-above, ghost fragment tables) → one repair function handles all. Geometry-based repair (ruled-line cells) tested and rejected: the PDF's drawn lines don't match its logical rows.
- **Repair order matters:** merge fragments *before* forward-filling, because emptiness is the data that identifies fragments; filling first would mint fake roles from cell spillover.
- **Serialization experiment (markdown table vs one-fact-per-line sentences), 5 runs each:** final answers tied 5/5, but markdown runs produced *confabulated reasoning* ("Store Administrator is not listed... so I'll use Inventory Specialist's row") — right answers via unreliable paths that only worked because rates coincided. Sentences produced direct, faithful lookups. **Sentences adopted.** 2D lookup is the model's weakness; sentences reduce it to 1D string matching, and give retrieval individually-addressable facts.
- **Never excise without replacing:** the bbox-slicing rewrite removes table regions from page text and inserts repaired sentences in their place. When repair produces nothing (e.g. Appendix 1's rates-free role table), fall back to the raw table-region text — otherwise content silently vanishes from the corpus. This fallback saved the Appendix 1 role descriptions and, later, the redundancy table.
- **Header attribution bug (found & fixed):** first version appended table sentences after each page's text, so tables got filed under whatever heading came *last* on the page (wage table under "1.2 Promotion criteria"). Fixed by bbox-slicing text above/below each table so sentences inherit the table's true position. Lesson: **when output doesn't change after a code change, verify the new output actually reached the database.**

### Q: "I'm a casual Supervisor. What's my hourly rate?" — the headline result
**Before ingestion fix (soup + misplaced sentences both in context):** 1/3 — one clean $35.54, one elaborate confabulation ($34.82 via invented "you're really a Team Member" logic), one confused partial.
**After bbox fix (one clean sentence version, under heading 1.1, soup gone):** **3/3 correct ($35.54)**, with run 1 correctly synthesising the 22.5% casual loading explanation from 1.1(c). Prompt held constant (v4) — proves the failure was ingestion, not prompting. DB verified: $35.54 in exactly one chunk, under 1.1; Appendix 1 intact.

---

## Post-fix regression: redundancy pay (clause 12.3) — an ingestion-bound failure

### Q: "I'm 50 and worked at Bunnings for 3.5 years, what redundancy pay would I get?" (correct: 13 weeks)
This table took the **fallback path** — its values are plain numbers (no $/%), so `_repair_table`'s rate detection missed them entirely (serializer gap logged below). The model receives raw text: clean data rows, scrambled 4-way header.

**v4 (×3):** 1/3. Errors scattered: wrong row once; one clean tier-by-tier elimination (the only fully correct run); one fused adjacent ranges into "2–4 years, both rows apply" — the exact adjacent-range overlap the prompt forbids.
**v5 — full ChatGPT rewrite (×3):** 0/3, all converging on the *same* wrong row ("1 but less than 2 years") — consistent error suggesting systematic cause. **Confounded experiment: whole prompt replaced instead of one variable changed. Uninterpretable. Reverted.** Suspected mechanism: "check each range in order" induced first-match capture (lower bound checked, upper bound ignored).
**v4.1 — v4 + both-bounds rule (×3):** 0/3 — self-contradiction, wrong row + wrong column value, and one wandering tier-walk that found the right row but never stated the answer.

**Verdict:** ❌ **9 runs, 3 prompt versions, ceiling ~1/3. Confirmed ingestion-bound** — no prompt rearranges scrambled input. Queued for serializer v2; prompt experimentation on this table closed. (Counter-evidence for the layer diagnosis: the wage table went 1/3→3/3 with prompt held constant once its input was cleaned.)

**Meta-lesson:** a prompt change built from one good trace (n=1) made results worse, and only before/after testing caught it. Also: prompt "improvements" written for frontier models (long numbered procedures, nested bullets) degrade a 3B model — v4's lean prose remains the tested-good baseline.

---

## Query rewriting (follow-up blindness fix) — SHIPPED

**Architecture:** heuristic gate + conditional LLM rewrite (A-inside-B). Rationale: follow-ups are a minority of questions but a *confirmed* retrieval failure when they occur, so the fix must cost nothing on the majority path. Standalone questions never touch the rewriter (no contamination risk, no extra latency); flagged follow-ups get one extra LLM call that turns a guaranteed retrieval miss into a probable hit.

### Components (each tested in isolation before assembly)
- **`needs_rewrite()` gate:** unambiguous openers ("what about", "and what", "how about") or leading conjunctions trigger alone; otherwise requires short length AND a reference word (that/it/this/they/those/"the above"). Validated 14/14 against predictions on 8 standalone + 6 follow-up questions (8/8 standalone clean — contamination door shut; 5/6 follow-ups caught, the miss being a word-count boundary, threshold widened 5→7). *The gate itself fell to an off-by-one range condition. Ranges spare no one.*
- **Rewriter prompt (tested standalone in ollama, 9 runs):** zero answering, zero chatter across all runs. Resolution quality good on genuine follow-ups; **pass-through failed 3/3** — the model contaminated standalone questions with unrelated history every time. Consistent failure → structural: a 3B model given history will use it. Solved architecturally by the gate (standalone questions never reach the rewriter), not by prompting.
- **History window:** last 2 *user* questions only (assistant answers excluded — pronouns point at user statements; CPU cost matters). Turn one skips rewriting structurally (`if previous and needs_rewrite(...)`). Rewritten question is what gets saved/embedded (self-contained history compounds for future rewrites).

### Acceptance test: "What are the overtime conditions?" → "what about part-timers?"
`REWRITTEN TO: What are the overtime conditions for part-timers?` — clean rewrite, intent preserved. Retrieval top-2: **3.1 Overtime conditions (0.782)** and **8.2 Part-time employment (0.761)** — exactly the required clauses, out of 102 chunks. Answer grounded, no fabrication (mild quibble: leaned on 8.2 over the 3.1(viii) trigger).
**Verdict:** ✅ Failure mode #5 (follow-up retrieval blindness) closed. n=1 — pronoun case and mid-conversation pass-through case still owed for full verification.

---

## Open items / known limitations
1. **Serializer v2:** (a) rate detection misses plain-number tables (redundancy, notice periods) → they fall back to raw text; (b) hard-coded "base rate / casual hourly rate" labels lie on non-wage tables (incentive table says "base rate 30%" for a permanent incentive rate); (c) weird-shaped tables (performance pay 1.6) repair into word salad — needs salad detection → fallback.
2. **Redundancy/notice-period questions unreliable (~1/3)** until serializer v2 lands. Documented weak spot.
3. **Query rewriting verification incomplete:** pronoun-resolution and pass-through acceptance runs outstanding.
4. **Arithmetic on retrieved figures:** model now sums entitlements; correctness untested beyond n=1.
5. **Remaining v4 regression suite never finished:** nights (concept mapping), grandchild (literal-mentions), dog death (near-miss refusal) — each owed ×3 runs.
6. **Prompt version discipline:** v4 is the tested baseline; v5/v6 rewrites entered app.py unlogged during experiments. `prompts/` folder now the rule; every result attributed to a version.

## Failure-mode taxonomy (updated)
Original modes 1–6 stand, with updates:
- **#2 attractor-clause bias** — partially mitigated by per-fact sentences (individually addressable embeddings); not re-measured.
- **#3 table row/column confusion** — root cause reattributed to **ingestion** (table soup), largely fixed for $/% tables by repair+sentences; persists on fallback-path tables.
- **#5 follow-up retrieval blindness** — CLOSED by query rewriting.
- **NEW #7: failure migration** — as layers get fixed, failures shift from *fabrication* (inventing content) to *selection* (right data in context, wrong row/tier picked). Selection errors are more fixable: cleaner serialization + reasoning-style prompting.
- **NEW #8: instruction backfire** — procedural instructions ("check each range in order") can induce worse behavior (first-match capture) on a 3B model. Prompt changes are experiments, never assumed improvements. 

Serializer v2, round 1: parked after acceptance slate. Redundancy 1/3 (=baseline), Supervisor regressed 3/3→1/3 (tripwire), nights mixed — honest labels confirmed working. Three v2 defects identified via chunk inspection: fragment-merge missing (v1 feature dropped in rewrite), N/A-valued rows lose rates (Activities Organiser), banner text fuses into labels (Supervisor). Rolled back to v1. New finding: answer length inversely correlates with correctness on 3B model — long reasoning chains are where fabrication breeds. v2 fix-list is small and named; revisit fresh.

# AI Document Assistant — Q&A Testing History

A record of questions asked against the Bunnings Retail Enterprise Agreement 2023, tracking how answer quality evolved as the project moved from "dump the whole document in" → chunking → embeddings → real semantic retrieval.

---

## Before RAG (whole-document context, no chunking)

These tests exposed the core problem: the model could only "see" whatever fit inside the context window, and it didn't reliably admit when content was missing — sometimes it hallucinated instead.

### Q: "What are the overtime conditions for Bunnings?"
**Context:** Very first real test, full 48-page PDF stuffed into one prompt, default ~4k context window.
**A:** Gave a vague, generic summary of the *whole document* (trial periods, IFAs, consultation, dispute resolution) — completely ignored the actual question. Never even mentioned overtime specifics.
**Verdict:** ❌ Failed — question effectively ignored, likely due to document positioning + truncation.

### Q: "What does shiftwork entail?" (asked twice, at 8192 token context)
**A (1st attempt):** Fabricated a generic definition — "rotating shifts," "healthcare, manufacturing, transportation," none of which is in the real document. No real clause content used.
**A (2nd attempt, after re-testing):** Different fabricated generic answer — mentioned "hospitals," "10pm to 6am" (the real clause says 6pm–5am), again no real content.
**Verdict:** ❌ Failed — clean hallucination both times, even with an explicit "say so if you don't know" system prompt instruction in place. Proved that prompting alone doesn't stop hallucination on a small local model.

### Q: (about Pre-Agreement Base Rates, clause 16.13(t), page 38)
**A:** "I'm not able to find the specific information about 'Pre-Agreement Base Rates' in the provided document. Could you please provide more context..."
**Verdict:** ✅ Honest — correctly admitted it didn't have the content, rather than guessing.

### Q: (about the Kitchen Specialist role, Appendix 1, page 40)
**A:** Correctly listed the real duties — kitchen design assistance, using the design planner, developing customer relationships — matching the source almost verbatim.
**Verdict:** ✅ Accurate.

### Q: (about Store Team Member duties)
**A:** Answered with real document content — but attributed it to the wrong role. The duties listed ("receiving visitors," "answering phone calls," "data entry") actually belong to *Store Administrator*, not *Store Team Member*, in the same table.
**Verdict:** ⚠️ Partially correct — real content retrieved, but misattributed. A subtler failure than outright hallucination: confident, well-formed, and wrong.

### Q: (about the dispute resolution procedure, clause 16.11/Appendix 6, near the end of the document)
**A:** Near-verbatim, fully accurate reproduction of the real clause (a) through (h).
**Verdict:** ✅ Accurate — this content happened to survive truncation since it was near the end of the prompt.

---

## After chunking + embeddings + semantic retrieval (the real RAG pipeline)

Once chunking, embeddings, and top-3 relevance ranking were wired in, retrieval started pulling the *correct* clause regardless of where it sat in the document.

### Q: "What is a trade administrator?"
**A:** Correctly said it couldn't find a specific "Trade Administrator" definition, while noting related roles that do exist (Trade Specialist, Trade Qualified, Forklift Coach).
**Verdict:** ✅ Honest — accurate acknowledgment of missing/different content.

### Q: "What does a supervisor do?" / "What roles does a supervisor have?"
**A:** Correctly listed real Supervisor duties (supervising/training team members, overseeing a department, supporting store leadership) — but also fabricated some extra detail ("Section 5.1", "Section 5.2", disciplinary action, record-keeping) not present in the source.
**Verdict:** ⚠️ Mixed — real core content correct, but padded with invented section numbers/details.

### Q: "What is the role of a supervisor?"
**A:** Clean, accurate answer — matched the real Supervisor clause exactly, no fabricated extras this time.
**Verdict:** ✅ Accurate.

### Q: "What are the Provisions Specific to Bunnings Trade Centres?" + "What are the overtime conditions?"
**Context:** First real test after the full embedding + ranking pipeline went live.
**A:** Retrieved top chunks were **3.1 Overtime conditions**, **3.2 Overtime pay**, **3.3 Reasonable overtime** — all correct top-3 matches out of 99 stored chunks. Answer content was accurate and near-verbatim on the overtime specifics, though it opened by conflating the earlier Trade Centres question with the new one, and mislabeled the clause number.
**Verdict:** ✅ Retrieval fully correct — first confirmed success of real semantic search. Minor rough edge: old chat history bleeding into the new answer's framing.

### Q: (about incentive rates — page 9, clause 2.1)
**A:** Accurate, detailed breakdown of real incentive rate percentages by day/time (30%/52.5% weekday early morning, 40%/62.5% Saturday, up to 125%/147.5% public holidays, etc.) — all figures matched the source table correctly.
**Verdict:** ✅ Accurate — confirmed retrieval works across different topics, not just the overtime test.

---

## Summary

| Stage | Behavior |
|---|---|
| Whole-document, no chunking | Truncation silently dropped content; model sometimes admitted it, sometimes hallucinated instead |
| Chunking + embeddings + top-3 retrieval | Correctly finds and answers from the right clause regardless of its position in the document (tested successfully as deep as page 9 and page 40+) |

**Known remaining rough edges:**
- Occasional fabricated extra detail even when the core answer is correct (e.g., invented section numbers)
- Chat history can bleed into new answers, causing topic conflation
- No formal testing yet on questions that genuinely require *multiple* clauses at once (top-3 retrieval may miss one if the answer spans more than 3 chunks)

---

## Prompt engineering phase (v4)

The system prompt was rebuilt from scratch: the bloated v3 was trimmed to a lean spine, then only instructions with test evidence behind them were grafted back (table row/column reading, ranges/boundaries merged from two duplicate blocks, self-consistency, pushback handling, literal-mentions rule). Principle adopted: **every prompt line must trace to a documented failure, and every confirmed fix must trace to a prompt line.** Prompt versions are now assets — saved to a `prompts/` folder, with each test result attributed to the version that produced it.

### Q: "How much is the meal allowance if overtime exceeds 4 hours?" (clause 4.1) — ×6 runs
**Before stacking instruction (×3):** 1/3 complete. Two runs correctly identified the $18.14 further allowance but silently dropped the $20.01 base — a *completeness* failure, not a ranges failure (the boundary logic was right every time).
**After adding "check whether multiple amounts apply together and combine them" (×3):** 2/3 complete, including one run that summed to $38.15 unprompted.
**Verdict:** ⚠️ Directionally improved, small n — logged as probabilistic completeness weakness, not "fixed." Attribution ambiguity noted honestly: old-prompt baseline was n=1.
**New observation:** the stacking instruction licensed the model to do arithmetic. Correct this time; arithmetic reliability on a 3B model is untested beyond n=1. New test category flagged.

---

## The ingestion-layer discovery (the table saga)

**The single most important finding of the project so far.** A casual-Supervisor rate test printed its retrieved context to the terminal, revealing that pypdf's `extract_text()` was destroying table structure at parse time — interleaving columns into "table soup" where a rate like $34.82 floats next to the wrong role. This reframed the entire table-failure family (row/column confusion, unit substitution, misattribution): **they were never model or prompt failures. The model was reconstructing tabular meaning from shuffled words.**

Three layers now recognised, in pipeline order: **ingestion → retrieval → generation.** Diagnose upstream first.

### Key sub-findings
- **pypdf vs pdfplumber:** pypdf destroys structure (unrecoverable); pdfplumber preserves cells in a messy grid (recoverable). Evaluation lens: don't ask "is this clean?" — ask "is the information still *present*?" Buried is a code problem; absent is a dead end.
- **Corruption is consistent** across tables (phantom columns, continuation-row fragments, blank-cells-inherit-from-above, ghost fragment tables) → one repair function handles all. Geometry-based repair (ruled-line cells) tested and rejected: the PDF's drawn lines don't match its logical rows.
- **Repair order matters:** merge fragments *before* forward-filling, because emptiness is the data that identifies fragments; filling first would mint fake roles from cell spillover.
- **Serialization experiment (markdown table vs one-fact-per-line sentences), 5 runs each:** final answers tied 5/5, but markdown runs produced *confabulated reasoning* ("Store Administrator is not listed... so I'll use Inventory Specialist's row") — right answers via unreliable paths that only worked because rates coincided. Sentences produced direct, faithful lookups. **Sentences adopted.** 2D lookup is the model's weakness; sentences reduce it to 1D string matching, and give retrieval individually-addressable facts.
- **Never excise without replacing:** the bbox-slicing rewrite removes table regions from page text and inserts repaired sentences in their place. When repair produces nothing (e.g. Appendix 1's rates-free role table), fall back to the raw table-region text — otherwise content silently vanishes from the corpus. This fallback saved the Appendix 1 role descriptions and, later, the redundancy table.
- **Header attribution bug (found & fixed):** first version appended table sentences after each page's text, so tables got filed under whatever heading came *last* on the page (wage table under "1.2 Promotion criteria"). Fixed by bbox-slicing text above/below each table so sentences inherit the table's true position. Lesson: **when output doesn't change after a code change, verify the new output actually reached the database.**

### Q: "I'm a casual Supervisor. What's my hourly rate?" — the headline result
**Before ingestion fix (soup + misplaced sentences both in context):** 1/3 — one clean $35.54, one elaborate confabulation ($34.82 via invented "you're really a Team Member" logic), one confused partial.
**After bbox fix (one clean sentence version, under heading 1.1, soup gone):** **3/3 correct ($35.54)**, with run 1 correctly synthesising the 22.5% casual loading explanation from 1.1(c). Prompt held constant (v4) — proves the failure was ingestion, not prompting. DB verified: $35.54 in exactly one chunk, under 1.1; Appendix 1 intact.

---

## Post-fix regression: redundancy pay (clause 12.3) — an ingestion-bound failure

### Q: "I'm 50 and worked at Bunnings for 3.5 years, what redundancy pay would I get?" (correct: 13 weeks)
This table took the **fallback path** — its values are plain numbers (no $/%), so `_repair_table`'s rate detection missed them entirely (serializer gap logged below). The model receives raw text: clean data rows, scrambled 4-way header.

**v4 (×3):** 1/3. Errors scattered: wrong row once; one clean tier-by-tier elimination (the only fully correct run); one fused adjacent ranges into "2–4 years, both rows apply" — the exact adjacent-range overlap the prompt forbids.
**v5 — full ChatGPT rewrite (×3):** 0/3, all converging on the *same* wrong row ("1 but less than 2 years") — consistent error suggesting systematic cause. **Confounded experiment: whole prompt replaced instead of one variable changed. Uninterpretable. Reverted.** Suspected mechanism: "check each range in order" induced first-match capture (lower bound checked, upper bound ignored).
**v4.1 — v4 + both-bounds rule (×3):** 0/3 — self-contradiction, wrong row + wrong column value, and one wandering tier-walk that found the right row but never stated the answer.

**Verdict:** ❌ **9 runs, 3 prompt versions, ceiling ~1/3. Confirmed ingestion-bound** — no prompt rearranges scrambled input. Queued for serializer v2; prompt experimentation on this table closed. (Counter-evidence for the layer diagnosis: the wage table went 1/3→3/3 with prompt held constant once its input was cleaned.)

**Meta-lesson:** a prompt change built from one good trace (n=1) made results worse, and only before/after testing caught it. Also: prompt "improvements" written for frontier models (long numbered procedures, nested bullets) degrade a 3B model — v4's lean prose remains the tested-good baseline.

---

## Query rewriting (follow-up blindness fix) — SHIPPED

**Architecture:** heuristic gate + conditional LLM rewrite (A-inside-B). Rationale: follow-ups are a minority of questions but a *confirmed* retrieval failure when they occur, so the fix must cost nothing on the majority path. Standalone questions never touch the rewriter (no contamination risk, no extra latency); flagged follow-ups get one extra LLM call that turns a guaranteed retrieval miss into a probable hit.

### Components (each tested in isolation before assembly)
- **`needs_rewrite()` gate:** unambiguous openers ("what about", "and what", "how about") or leading conjunctions trigger alone; otherwise requires short length AND a reference word (that/it/this/they/those/"the above"). Validated 14/14 against predictions on 8 standalone + 6 follow-up questions (8/8 standalone clean — contamination door shut; 5/6 follow-ups caught, the miss being a word-count boundary, threshold widened 5→7). *The gate itself fell to an off-by-one range condition. Ranges spare no one.*
- **Rewriter prompt (tested standalone in ollama, 9 runs):** zero answering, zero chatter across all runs. Resolution quality good on genuine follow-ups; **pass-through failed 3/3** — the model contaminated standalone questions with unrelated history every time. Consistent failure → structural: a 3B model given history will use it. Solved architecturally by the gate (standalone questions never reach the rewriter), not by prompting.
- **History window:** last 2 *user* questions only (assistant answers excluded — pronouns point at user statements; CPU cost matters). Turn one skips rewriting structurally (`if previous and needs_rewrite(...)`). Rewritten question is what gets saved/embedded (self-contained history compounds for future rewrites).

### Acceptance test: "What are the overtime conditions?" → "what about part-timers?"
`REWRITTEN TO: What are the overtime conditions for part-timers?` — clean rewrite, intent preserved. Retrieval top-2: **3.1 Overtime conditions (0.782)** and **8.2 Part-time employment (0.761)** — exactly the required clauses, out of 102 chunks. Answer grounded, no fabrication (mild quibble: leaned on 8.2 over the 3.1(viii) trigger).
**Verdict:** ✅ Failure mode #5 (follow-up retrieval blindness) closed. n=1 — pronoun case and mid-conversation pass-through case still owed for full verification.

---

## Open items / known limitations
1. **Serializer v2:** (a) rate detection misses plain-number tables (redundancy, notice periods) → they fall back to raw text; (b) hard-coded "base rate / casual hourly rate" labels lie on non-wage tables (incentive table says "base rate 30%" for a permanent incentive rate); (c) weird-shaped tables (performance pay 1.6) repair into word salad — needs salad detection → fallback.
2. **Redundancy/notice-period questions unreliable (~1/3)** until serializer v2 lands. Documented weak spot.
3. **Query rewriting verification incomplete:** pronoun-resolution and pass-through acceptance runs outstanding.
4. **Arithmetic on retrieved figures:** model now sums entitlements; correctness untested beyond n=1.
5. **Remaining v4 regression suite never finished:** nights (concept mapping), grandchild (literal-mentions), dog death (near-miss refusal) — each owed ×3 runs.
6. **Prompt version discipline:** v4 is the tested baseline; v5/v6 rewrites entered app.py unlogged during experiments. `prompts/` folder now the rule; every result attributed to a version.
7. **External prompt-restructure proposal reviewed**: rejected as v5 redux (structured format already falsified 0/3); few-shot boundary example extracted as untested nugget → queued as v4.2 experiment

## Failure-mode taxonomy (updated)
Original modes 1–6 stand, with updates:
- **#2 attractor-clause bias** — partially mitigated by per-fact sentences (individually addressable embeddings); not re-measured.
- **#3 table row/column confusion** — root cause reattributed to **ingestion** (table soup), largely fixed for $/% tables by repair+sentences; persists on fallback-path tables.
- **#5 follow-up retrieval blindness** — CLOSED by query rewriting.
- **NEW #7: failure migration** — as layers get fixed, failures shift from *fabrication* (inventing content) to *selection* (right data in context, wrong row/tier picked). Selection errors are more fixable: cleaner serialization + reasoning-style prompting.
- **NEW #8: instruction backfire** — procedural instructions ("check each range in order") can induce worse behavior (first-match capture) on a 3B model. Prompt changes are experiments, never assumed improvements.
---

## Serializer v2: the numeric-tables campaign

**Goal:** fix the redundancy-family failures (plain-number tables falling through to raw-text fallback; hard-coded lying labels) by making `_repair_table` read each table's own header and emit honest label-value sentences.

### Recon: external parsers evaluated and rejected
- **pymupdf4llm / MuPDF:** cannot extract this PDF's text at all — non-conformant zlib streams ("incorrect header check"); opens structure (48 pages) but yields LENGTH 0. pikepdf stream normalization did not cure it. Same file extracts fine in pypdf/pdfplumber → MuPDF strictness vs sloppy PDF manufacture; incompatibility fundamental. REJECTED (~25 min, clean negative).
- **pymupdf4llm on a Chrome-rendered re-save:** works (Chrome re-renders from scratch, writing conformant streams) and produced the best-ever extraction of the redundancy table (clean data rows, column labels attached). REJECTED as pipeline anyway: (a) **decimal-severing money corruption** — $27.00 → "$2700" with orphaned "." deposited in the next row; (b) regression risk on the wage table our pipeline already handles 3/3; (c) depends on a manual Chrome re-save ritual that cannot run inside upload. Redundancy extraction retained as a correctness oracle.
- **LlamaParse:** rejected on architecture — cloud API (uploads documents to third-party servers), violating the project's local-first premise; package also deprecated. Lesson: candidate tools must pass two gates before quality recon — *runs within my constraints* and *is alive*.

### Design rulings (v2)
1. Header = all rows above the first row containing a value cell.
2. Header fragments merged **column-wise by position** (primary signal); casing is tiebreak only, never load-bearing. Emit imperfect labels — labels are for association, not prose.
3. Value cell = pure number after stripping $ % , — or whitelisted token (Nil, N/A).
4. Data cells map to labels via **nearest non-empty header**, subject column excluded from candidacy (resolves the col-1 tie on the redundancy grid).
5. Sentence template: first text cell(s) = subject; every value emits "Label value". Desk-checked: "1 year but less than 2 years: Weeks' redundancy pay (…) Team Members under 45 years of age 4, Team Members aged 45 and over 5." Clunky and correct — the number sits physically adjacent to its age label.
6. Salad guard: any label > 150 chars → return "" → raw-text fallback (never excise without replacing). Threshold calibrated on data: legitimate merged redundancy label ≈ 105 chars; Appendix 1 monster labels 400+.
7. Scope: tables with no detectable data rows (Appendix 1 role descriptions) stay on raw-text fallback by design.

### Implementation bug cycle (all caught by verification, zero by model runs)
- **N/A counted as value** → header detection fired deep inside Appendix 1 → monster labels → embedder context overflow → upload crash + half-populated DB. Fixed: numeric/token split.
- **Over-tightened fix** (header detection = numeric-only) silently reclassified the redundancy "less than 1 year | Nil | Nil" row as header → tier vanished, phantom Nils fused into every label ("Nil 4"). Fixed: reverted detection to value-cells; the salad guard independently protects Appendix 1. *Two guards, one problem — only one needed to move.*
- **Salad guard first shipped at 60 chars** — killed the desk-checked 105-char redundancy label the same afternoon it was approved. Recalibrated to 150 with data. Lesson: a guard is a range condition; desk-check it against known-good data like any other.
- **Wrong-file upload:** DB provenance check revealed the tested database was built from `bunnings1.pdf` (the Chrome-render recon artifact) — file-picker misclick; three runs invalidated. Fixes: upload debug print now announces the filename; recon artifacts quarantined. *The `file_name` column solved in one query what output tea-reading couldn't.*
- **IndexError on empty DB:** `/ask`'s `rank[3]` assumed ≥4 chunks forever; empty-database day called the promise in. Guarded with a length check. Lesson: indexing a list is a promise about its minimum size.

### Acceptance slate, round 1 (v2.0, DB verified clean first)
- Redundancy ×3: **1/3** (=baseline). One correct (13 weeks) via messy reasoning; one wrong-row; one catastrophic fabrication (invented per-year formula → "72 weeks").
- Supervisor ×3: **1/3 — regression tripwire fired** (baseline 3/3). Two runs wandered to Store Administrator $34.49.
- Nights ×3: mixed. One retrieval miss; one fabricated dollar conversions of percentages; one good run quoting honest labels verbatim and asking for clarification. **Lying labels confirmed dead.**
- Chunk inspection explained the regression — three v2.0 defects: fragment merge missing (v1 feature dropped in rewrite), N/A-valued rows losing rates (Activities Organiser), banner text fused into the Supervisor label.
- **Decision: rolled back to v1** (option C) — bank the known-good state, park v2 with a named fix-list.

### NEW FINDING (credit: Aleesha): answer length inversely correlates with correctness
Across the slate, correct answers were short and direct; every disaster was an essay. On a 3B model each additional reasoning step is another dice roll — long chains are where fabrication breeds. Response length is a free confidence signal (possible future UI surface). → Taxonomy #9.

### v2.1 (late-night session, UNTESTED)
All three defects addressed solo: fragment merge ported from v1, banner-row filter (single-cell header rows skipped in label merge), forward-fill now rescues N/A-only rows; plus rightward tie-break in nearest_label and direct-label-first mapping. **Status: implemented, zero runs — the rollback to v1 was never executed and v1 was deleted from the file during edits (source preserved in repair_table_v1.py). Next session: either restore v1 (rollback discipline) or run the 9-run acceptance slate against v2.1 on a verified DB.**

## Failure-mode taxonomy (additions)
- **#9 verbosity-fabrication correlation** — long answers predict wrongness on 3B models; short direct answers predict correctness.
- **#10 provenance blindness** — results are attributable only if the run announces its configuration (prompt version, source filename, code version). Three incidents this sprint (v5 prompt swap, bunnings1.pdf upload, unverified lines-strategy run) share this root.

*Session note: this log covers a ~2-day sprint (roughly Jul 14–16, 2026). Assistant model may have changed mid-sprint (Claude version switch); no reliable in-conversation marker exists, so results are attributed to prompt/code/data versions only — which is the attribution that matters.*

Multi-document support shipped and verified: 5-step acceptance passed (per-doc retrieval, history isolation both directions, cascade delete, empty-state guard). Three contamination doors closed: retrieval, chat history, rewriter."

## 17.07
docx path hardened: tables were silently discarded (doc.paragraphs only); fixed via iter_inner_content in-order walk + sentence serializer with pairs-list (merged-header lossless) and garbage-header fallback. Verified via pretraining-control test: model's documented wrong prior (Oct 21 2011) displaced by document-only answer (Oct 11 2012).
