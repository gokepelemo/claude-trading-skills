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

- A structured input bundle (market data, trade logs, journal snippets) is available and ranked, falsifiable hypotheses are needed.
- Converting loose observations or postmortem findings into testable strategy hypotheses with explicit kill criteria.
- Producing `strategy.yaml` + `metadata.json` exports compatible with `edge-finder-candidate/v1` for downstream edge-pipeline stages.

Do not use for live signal generation or order execution — this skill only produces experiment designs, not trades.

## Prerequisites

- No API keys required (pure calculation from provided inputs).
- Python 3 available.
- An input JSON bundle conforming to `schemas/input_bundle.schema.json` (see `examples/example_input.json`).

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

Saved to the `--output-dir` (default `reports/`):

- `raw_hypotheses.json` — pass 1 output: generated hypothesis cards conforming to `schemas/raw_hypotheses.schema.json`.
- Ranked output bundle — pass 2 output: critiqued, ranked hypothesis cards conforming to `schemas/output_bundle.schema.json` (see `examples/example_output.json`).
- With `--export-strategies`: `strategy.yaml` + `metadata.json` for each `pursue` hypothesis, compatible with `edge-finder-candidate/v1`.

## References

- `references/hypothesis_types.md`
- `references/evidence_quality_guide.md`

## Resources

- `prompts/` — `system_prompt.md`, `developer_prompt_template.md`, `critique_prompt_template.md`
- `schemas/` — `input_bundle`, `hypothesis_card`, `raw_hypotheses`, `output_bundle` JSON schemas
- `examples/` — `example_input.json`, `example_output.json`, `sample_input.json`
- `scripts/run_hypothesis_ideator.py` and `scripts/pipeline/` — evidence extraction, normalization, ranking, output formatting, strategy export
