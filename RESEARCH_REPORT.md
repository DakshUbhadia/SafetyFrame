# Research report — completed manuscript, submission pending

The manuscript content and final analysis are complete. See the
[final results overview](FINAL_RESULTS.md), [full manuscript](report/report.md),
and [prepared submission materials](SUBMISSION.md). No final report PDF or
submission confirmation is recorded. The author confirmed that submission is
still pending on November 16, 2026. Template, PDF and release checks remain
Sprint 11 work; no submission or page-limit compliance is implied below.

The remaining notes describe the completed Sprint 10 content and its provenance.

The [complete report draft](report/report.md) is authored as **Daksh Ubhadia,
Independent researcher**, confirmed by the user. It covers Introduction,
Related Work, Methods, Results, Discussion, Limitations and Conclusion, with a
177-word abstract and three main figures. Runtime details, descriptive condition
means, detailed self-assessment ratios, Model B diagnostics and repair figures
are retained in the appendices.

Following user-supplied editorial feedback, Results now present Model A framing,
self-assessment, requirement-accounting interaction, Model B and repair. This
post-result narrative change does not change the prespecified estimands or
promote a descriptive metric into a new confirmatory primary hypothesis. The conclusions
retain inconclusive framing evidence, sensitivity to operational handling,
inaccurate completion claims and Model B's substantial reasoning-budget limit.
No inference calls or changes to study scores were made.

The title now represents all three channels: **SafetyFrame-Eval: Safety Framing,
Requirement Accounting, and Self-Assessment in AI Coding**. The abstract and
main text highlight that 13/29 completed accounting trajectories had failed
artifact requirements while all 145 final checklist entries claimed implemented.
The new Figure 2 shows 20 failed requirements, 20 implemented claims on those
failures and zero incomplete/uncertain acknowledgements. Its
[numerical input](report/claim_figure_data.json) derives directly from the unchanged
Model A dataset. The conclusion remains narrow and the timing discrepancy stays
disclosed.

## Appendices and provenance

The draft includes exact frozen shared prompts and composition, all task IDs,
families and titles, scoring/parsing rules, additional failure/repair tables,
deviations/incidents, numerical provenance and the required Limitations and
Dual-Use / Ethical Considerations appendix. Raw response and reasoning text
remain outside the released scored datasets.

The Sprint 10 source review found a timing discrepancy: the registration says
hidden scoring occurs after both turns; the frozen code scores locally after
each response while constructing Turn-2 feedback from public results only.
This is disclosed in Methods, Appendix D and [incidents.json](report/incidents.json).
The original registration and frozen implementation remain unchanged.

## Verify the draft

```powershell
.\.venv\Scripts\python.exe scripts/verify_report.py
```

The verifier checks seven evidence-rendered tables, five exact prompt blocks,
source-derived narrative quantities, the abstract length, local links and all
reviewed analysis digests. It records
[claim traceability](report/claim_traceability.json) and
[verification evidence](report/report_verification.json). These checks establish
internal consistency, not independent review or replication.

To regenerate the additional claim-versus-ground-truth figure:

```powershell
.\.venv\Scripts\python.exe -m analysis.claim_figure
```

The verifier checks its counts against the reviewed dataset and records hashes
of its PNG, SVG and PDF files. Original Sprint 9 figures and plotting data are
preserved unchanged.

If report tables need to be regenerated from unchanged analysis outputs:

```powershell
.\.venv\Scripts\python.exe scripts/verify_report.py --refresh-tables
```

Only marked table and prompt blocks are refreshed; surrounding prose stays
editable. Numerical analysis remains in the [Sprint 9 package](FINAL_ANALYSIS.md).

## Source and submission checks

[Source verification](report/source_verification.md) records six checked primary
research sources and the official event requirements. The suggested MASK-OFF
landing page could not be verified, so no substantive findings are attributed
to it. The official Google Docs template required sign-in, so its detailed
layout was not inspected.

Sprint 10 completes the content draft. Sprint 11 still needs template transfer,
PDF export and visual/page-limit inspection, clean-environment release checks,
the remaining author submission details, upload and confirmation. No submission
or final page-count compliance is claimed by the Markdown draft.
