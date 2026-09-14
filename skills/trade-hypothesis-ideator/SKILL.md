---
name: trade-hypothesis-ideator
description: >
  Generate falsifiable trade strategy hypotheses from market data, trade logs,
  and journal snippets. Use when you have a structured input bundle and want
  ranked hypothesis cards with experiment designs, kill criteria, and optional
  strategy.yaml export compatible with edge-finder-candidate/v1.
---

# Trade Hypothesis Ideator

Generate 1-5 structured hypothesis cards from a normalized input bundle, critique and rank them, then optionally export `pursue` cards into `strategy.yaml` + `metadata.json` artifacts.

## When to Use

- When you have a structured input bundle (market data, trade logs, journal snippets) and want falsifiable trade strategy hypotheses
- Before committing research time to a strategy idea — to get ranked hypothesis cards with kill criteria first
- When feeding candidate strategies into the edge-finder pipeline (`edge-finder-candidate/v1` export)

## Prerequisites

- Normalized input bundle JSON matching `schemas/input_bundle.schema.json` (see `examples/example_input.json`)
- Python 3.10+

## Workflow

1. Receive input JSON bundle.
2. Run pass 1 normalization + evidence extraction.
3. Generate hypotheses with prompts:
   - `prompts/system_prompt.md`
   - `prompts/developer_prompt_template.md` (inject `{{evidence_summary}}`)
4. Critique hypotheses with `prompts/critique_prompt_template.md`.
5. Run pass 2 ranking + output formatting + guardrails.
6. Optionally export `pursue` hypotheses via Step H strategy exporter.

## Scripts

- Pass 1 (evidence summary):

```bash
python3 skills/trade-hypothesis-ideator/scripts/run_hypothesis_ideator.py \
  --input skills/trade-hypothesis-ideator/examples/example_input.json \
  --output-dir reports/
```

- Pass 2 (rank + output + optional export):

```bash
python3 skills/trade-hypothesis-ideator/scripts/run_hypothesis_ideator.py \
  --input skills/trade-hypothesis-ideator/examples/example_input.json \
  --hypotheses reports/raw_hypotheses.json \
  --output-dir reports/ \
  --export-strategies
```

## Output

- Pass 1: `evidence_summary.json` — normalized evidence and prompt-ready text
- Pass 2: `output_bundle.json` and `hypothesis_report.md` — ranked, guardrail-validated hypothesis cards
- With `--export-strategies`: `strategies/<candidate_id>/` (`strategy.yaml` + `metadata.json`) and `strategy_exports.json` manifest for `pursue` hypotheses

## Resources

- `references/hypothesis_types.md`
- `references/evidence_quality_guide.md`
