# Last-mile presentation changes

These post-collection updates implement the supplied last-mile plan's repository
presentation work. They restate existing outcomes and add no model calls,
confirmatory endpoints, statistical tests, or selectively rerun trajectories.

Implemented:

- README leads with 145/145 implemented claims, including 20/20 failed artifact
  requirements, the existing direct claim-versus-ground-truth figure, and the
  descriptive 13/29 affected trajectories (44.8%).
- Framing is labeled inconclusive; accounting is nominal but sensitivity-
  dependent; DeepSeek is operationally confounded.
- FINAL_RESULTS.md provides a short results route with precise denominators and
  links to unchanged scored datasets and analysis.
- Current navigation distinguishes completed collection/analysis/manuscript
  content from pending PDF packaging and submission. Historical sprint notes
  remain historical; the scientific report body is unchanged after its opening.
- GitHub description and ten topics match github_metadata.json. The independently
  fetched values and prior metadata are in github_metadata_receipt.json.
- SUBMISSION.md contains the exact title, prepared summary, recommended track,
  optional unconfirmed team name, PDF filename, and remaining submission checks.

The author confirmed that submission is still pending on November 16, 2026.
There is no final report PDF or submission receipt to upload or confirm. No
submitted-PDF authority, template compliance, or page-limit compliance is claimed.

Validation: the original freeze verifies; all seven report tables, five prompt
blocks, 27 narrative claims, the 177-word abstract, and upstream analysis digests
pass the existing report verifier. Headline counts match the unchanged dataset;
all 141 local links checked in the six navigation/report documents exist.
The existing claim figure was visually inspected. GitHub About changes were
read back from the API. These checks do not constitute independent research
review, incognito-browser inspection, or a clean-environment release check.

During publication, the remote main branch had gained the author's merge of
Study 2 (cc22f2f). The presentation commit was rebased onto that merge, preserving
it. Study 2's branch remains at 7705011 with its original freeze and preservation
hashes, and the preservation tag is unchanged.

Main now includes the frozen protocol plus newer navigation text. Its strict
audit preservation check therefore intentionally rejects the presentation edits.
Run collection on followup/self-assessment-audit. On main, use
`python scripts/verify_presentation.py`: it checks the original scientific hashes,
the merged audit protocol, all report evidence, and every preserved file apart
from seven explicitly recorded documentation-only amendments. Original hashes
are retained in documentation_amendments.json; no freeze was rewritten.

Metadata preview and application are separate:

```powershell
.venv/Scripts/python scripts/update_repository_metadata.py
.venv/Scripts/python scripts/update_repository_metadata.py --apply
```

The application command uses existing GitHub credentials without writing them
to the metadata receipt. No submission form is contacted by this script.
