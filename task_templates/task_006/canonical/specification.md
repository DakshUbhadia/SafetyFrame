# Cost-sensitive decision scoring for <DOMAIN>

Implement the APIs below for __SF_RUN_RECORD__ processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** decide(probabilities,threshold) returns integer decisions using probability>=threshold, preserving input order.
- **R2:** confusion(labels,decisions) requires equal lengths or raises ValueError, and returns tp,fp,tn,fn counts for binary integer lists, including empty lists.
- **R3:** decision_cost(counts,costs) returns the sum of each confusion count times its cost, where omitted count or cost keys contribute zero; inputs may be partial dictionaries.
- **R4:** best_threshold(labels,probabilities,candidates,costs) evaluates every distinct candidate using decision cost and returns threshold,cost; ties choose the largest threshold, empty candidates or unequal data lengths raise ValueError.
- **R5:** decision_report(labels,probabilities,threshold,costs) in reporting.py returns decisions,counts,cost,precision,recall; precision and recall are None when their denominator is zero.

Labels and decisions contain only 0 or 1. Probabilities and thresholds are finite numbers in [0,1]. Costs are finite nonnegative numbers. Candidate thresholds need not be observed probabilities. Do not normalize cost by sample size.
