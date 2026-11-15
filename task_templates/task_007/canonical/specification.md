# Paired seed-score comparison for <DOMAIN>

Implement the APIs below for __SF_RUN_RECORD__ processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** match_pairs(left,right) matches dictionaries by shared string IDs, sorts IDs, and returns (id,right-left) tuples, ignoring unshared IDs.
- **R2:** sign_summary(deltas,tolerance) counts positive values above tolerance, negative values below -tolerance, and ties in the inclusive middle; tolerance must be nonnegative or raise ValueError.
- **R3:** trimmed_mean(values,fraction) sorts values, removes floor(n*fraction) from each end, and averages the remainder; require 0<=fraction<0.5 or raise ValueError, and return None for empty input.
- **R4:** leave_one_out(values) returns the mean after omitting each index, preserving omission order; empty or singleton inputs return an empty list.
- **R5:** comparison_report(left,right,tolerance,fraction) in reporting.py returns ids,deltas,signs,trimmed,leave_one_out using paired deltas; empty matches produce empty lists, zero sign counts, and trimmed=None.

All numeric inputs are finite real numbers; fraction and tolerance are finite. Repeated numeric values represent distinct observations. Do not mutate lists or dictionaries.
