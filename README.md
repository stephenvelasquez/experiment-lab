# Experiment Lab

Design, analyze, and report on A/B tests with statistical rigor. Built for product managers who own experimentation.

## Why this exists

Most PMs either (a) don't run experiments, (b) run them without power analysis, or (c) peek at results too early. This tool enforces discipline: design the experiment first, calculate the sample size, then analyze with proper significance testing.

## Quick start

```python
from experiment_lab import Experiment

exp = Experiment("Checkout Flow Redesign")

# Design phase: how many users do we need?
exp.design(
    baseline_rate=0.032,          # Current checkout conversion: 3.2%
    minimum_detectable_effect=0.1, # We want to detect a 10% relative lift
    significance_level=0.05,       # 5% false positive rate
    power=0.80,                    # 80% chance of detecting a real effect
)
```

**Output:**

```
┌────────────────────────────────────────────────────┐
│  Experiment: Checkout Flow Redesign                │
├────────────────────────────────────────────────────┤
│  Baseline:    3.20%                                │
│  MDE:         10% relative (3.52% absolute)        │
│  Required:    36,842 users per variant              │
│  Total:       73,684 users                          │
│  At 5K/day:   ~15 days to reach significance       │
└────────────────────────────────────────────────────┘
```

```python
# Analysis phase: did it work?
exp.analyze(
    control_users=38_200,
    control_conversions=1_222,
    treatment_users=38_100,
    treatment_conversions=1_371,
)
```

**Output:**

```
┌────────────────────────────────────────────────────┐
│  Results: Checkout Flow Redesign                   │
├────────────────────────────────────────────────────┤
│  Control:     3.20% (1,222 / 38,200)              │
│  Treatment:   3.60% (1,371 / 38,100)              │
│  Lift:        +12.5% relative                      │
│  p-value:     0.0023                                │
│  Significant: YES at α=0.05                        │
│  95% CI:      [+4.3%, +20.7%] relative lift        │
├────────────────────────────────────────────────────┤
│  RECOMMENDATION: Ship treatment                    │
└────────────────────────────────────────────────────┘
```

## Features

- **Power analysis** — Calculate required sample size before running
- **Duration estimation** — How many days at your traffic volume?
- **Significance testing** — Two-proportion z-test with confidence intervals
- **Multiple comparison correction** — Bonferroni and Holm adjustments
- **Guardrail metrics** — Flag if the experiment harms key metrics
- **Sequential testing** — Optional early stopping with alpha spending
- **Report generation** — Markdown reports ready for stakeholders

## Project structure

```
experiment-lab/
├── experiment_lab.py     # Core library
├── examples/
│   ├── checkout_redesign.py
│   └── pricing_test.py
├── tests/
│   └── test_experiment.py
├── requirements.txt
└── README.md
```

## Common mistakes this tool prevents

| Mistake | How it's prevented |
|---------|-------------------|
| Peeking at results too early | Duration calculator tells you when to look |
| No power analysis | `design()` is required before `analyze()` |
| Ignoring multiple comparisons | Auto-correction when >2 variants |
| Calling non-significant results "trends" | Binary: significant or not |
| No confidence interval on lift | Always reported |

## License

MIT
