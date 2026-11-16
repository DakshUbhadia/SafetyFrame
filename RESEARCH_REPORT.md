# Research report — Sprint 10

The [complete report draft](report/report.md) is authored as **Daksh Ubhadia,
Independent researcher**, confirmed by the user. It covers Introduction,
Related Work, Methods, Results, Discussion, Limitations and Conclusion, with a
197-word abstract, four main figures and a secondary repair figure in the appendix.

Results are presented in the requested order: Model A framing, Model B framing,
requirement-accounting interaction, self-assessment and repair. The conclusions
retain inconclusive framing evidence, sensitivity to operational handling,
inaccurate completion claims and Model B's substantial reasoning-budget limit.
No inference calls or changes to study scores were made.

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
