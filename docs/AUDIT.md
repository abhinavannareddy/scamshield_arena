# Audit of this project's own claims

Parts of this project were drafted with an AI assistant (Claude) and then checked. This page records what was checked, what held up, what did not, and what changed as a result. A claim is only listed as confirmed if it was re-run or re-computed from the code in this repository.

## Method

1. Re-ran `python -m arena.evaluate`. The output is identical to the committed `results.json`, so the headline table is reproducible.
2. Read every README claim and traced it to a number in `results.json`, `results_extra.json`, or the code.
3. Looked for ways the test could be easier than it sounds (leakage, shared content, mismatched false-alarm rates).
4. Rewrote text that was stronger than the evidence.

## Claims checked

| Claim | Result | Evidence |
|---|---|---|
| Keyword rules catch 62% on wording A and about 1% after wording changes | Confirmed | `results.json`: 0.623, 0.006 |
| Payment context only holds steady at 85% to 88% | Confirmed | 0.845 to 0.881 across tests |
| Text model drops 12 points on switched wording, retraining recovers it | Confirmed | 0.988 to 0.870, then 0.989 after retraining |
| Retrained model catches 92% on wording C | Confirmed | 0.916 |
| "False alarms about 3%" for every cell | **Partly wrong** | Realised rates range from 0.0% to 3.6% (see below) |
| Wording C and the tech-support type are "never seen" | **Overstated** | See finding 2 |
| False-alarm gaps between groups are "small" | **Needs a number** | 1.9% to 2.8%, which is 47% higher for small businesses |
| "I first built an easier version and got 100% on unseen wording" | Not checkable | That earlier version is not in this repository, so the claim is the author's account only |

## Findings

### 1. The 3% false-alarm target is not what every cell actually got

The threshold is set on validation data (wordings A and B). On other test sets the realised false-alarm rate differs:

| Guardian | A | B | C | New type |
|---|---|---|---|---|
| Keyword rules | 2.7% | 0.0% | 0.0% | 0.0% |
| Payment context only | 2.9% | 2.9% | 2.9% | 3.1% |
| Text + context (retrained) | 3.4% | 3.6% | 1.0% | 0.8% |

Two consequences. The keyword rules "stay quiet" because they fire on nothing. And the text model's score on wording C was measured at a stricter 1% false-alarm rate than the payment-only guardian's 2.9%, so the comparison on C slightly understates the text model. The trade-off figure in `docs/img/tradeoff.png` shows catch rate across a range of false-alarm settings, which is the fairer way to compare. **Change made:** README now states "about 3% on validation data" and links the realised table.

### 2. The "new scam type" is less new than it sounds

Tech support is held out of training, but its tactics are not. Authority, urgency, secrecy and moving money all appear in the trained types, and `remote_access` phrases appear in training too, as an optional tactic of bank impersonation. So the model has seen the ingredients and only the mix is new. Its 90% catch rate, inside the 89% to 93% range of the trained types, is consistent with that. **Change made:** README and FINDINGS now say "new mix of known warning signs", not "never seen".

### 3. Precision at real-world base rates is not measured

Test sets are 40% scams. Real payments are overwhelmingly honest, so most holds there would be honest customers (worked example in FINDINGS.md). The README no longer implies a high catch rate means few wasted call-backs.

### 4. Everything is template text

A small vocabulary and three fixed paraphrase sets is a very easy language problem compared with real messages. The numbers show how a method behaves when wording shifts. They do not predict performance on real conversations.

### 5. One seed set, no confidence intervals

Results are averaged over 5 seeds with no interval. Differences of a point or two (for example, 90% against 88%) should not be read as real.

## AI-content review

Text in the README and docs was reviewed for:

- **Unsupported claims.** Four phrases were softened or tied to a number (items above).
- **Invented detail.** There are no real names, brands, citations or datasets in the project. Test `test_no_real_identifiers_in_text` checks generated conversations for long digit runs, "@" and links.
- **Tone.** Marketing-style phrases and stacked adjectives were replaced with plain statements, and sentences were shortened.
- **Disclosure.** The README states that an AI assistant helped build this and that every figure can be regenerated.

## Open items

- Add confidence intervals (more seeds or bootstrap).
- Test with messier, human-written conversations, with consent and privacy review.
- Test a scam type that shares no tactics with the training types.
