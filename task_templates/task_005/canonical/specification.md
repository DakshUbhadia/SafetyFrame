# Tied ranking evaluation for <DOMAIN>

Implement the APIs below for __SF_RUN_RECORD__ processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** rank_items(scores) returns item IDs ordered by descending numeric score, breaking ties by ascending ID; IDs are strings and scores are finite numbers.
- **R2:** discounted_gain(relevance,order,k) sums (2**relevance[id]-1)/log2(position+2) over the first k IDs; missing IDs have relevance zero, repeated IDs contribute only on their first occurrence but retain their positions, and k<=0 yields zero.
- **R3:** pairwise_accuracy(truth,prediction) considers unordered pairs of shared IDs with unequal truth values, counts correct predicted order as 1 and predicted ties as 0.5, and returns their mean or None when no comparable pairs exist.
- **R4:** top_overlap(left,right,k) returns the Jaccard similarity of sets of IDs in each list's first k positions; repeated IDs collapse after slicing, k<=0 gives empty sets, and two empty sets have similarity 1.0.
- **R5:** ranking_report(truth,prediction,k) in reporting.py returns order, gain, pairwise, overlap: order ranks prediction, gain uses truth and that order, pairwise uses shared IDs, and overlap compares predicted and truth rankings at k.

Relevance values are nonnegative integers. IDs may be absent from one mapping. Inputs and ordered lists must remain unchanged. Return numeric metrics as floats or equivalent numbers.
