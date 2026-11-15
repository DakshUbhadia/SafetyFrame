# Cohort distribution drift report for AI safety research

Implement the APIs below for safety_eval_run processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** category_counts(rows,key) counts string categories from key; missing keys and None are excluded and empty string remains a valid category.
- **R2:** aligned_proportions(left,right,alpha) returns categories,left,right lists aligned to the sorted union of count keys, adds nonnegative finite alpha to every category on each side and normalizes each side separately; zero total gives an all-zero vector, and invalid alpha raises ValueError.
- **R3:** jensen_shannon(left,right) requires equal-length finite nonnegative vectors or raises ValueError; normalize each to sum one when nonzero, then return base-2 Jensen-Shannon divergence, omitting zero logarithm terms; empty vectors give zero and zero vectors remain zero.
- **R4:** rank_changes(categories,left,right) requires equal lengths or raises ValueError; return category,delta rows for right-left, ordered by decreasing absolute delta then ascending category.
- **R5:** drift_report(reference,current,key,alpha) in reporting.py counts categories, aligns proportions, and returns categories,reference,current,divergence,changes; reference/current are normalized vectors and changes use those vectors.

Count mappings contain string keys and nonnegative integer counts, including explicit zero counts. Divergence is defined even when one vector is all zero: it contributes zero to its own KL sum. All calculations are offline deterministic summaries, not statistical significance claims.
