"""Standalone scientific figures and an auditable initial-results narrative."""
from pathlib import Path


def fmt(value):
    return 'NA' if value is None else f'{value:.3f}'


def interval(value):
    return f"{fmt(value['estimate'])} [{fmt(value['lower'])}, {fmt(value['upper'])}]"


def figures(summary,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    colors={'C':'#2563a6','S':'#b45332','CD':'#2563a6','SD':'#b45332'}
    def save(fig,name):
        fig.tight_layout()
        for extension in ('png','svg','pdf'):
            fig.savefig(output/f'{name}.{extension}',dpi=180,bbox_inches='tight')
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.5,6))
    tasks=list(summary['task_outcomes'])
    gaps=summary['contrasts']['BaselineSafetyGap_A']['task_values']
    for i,task in enumerate(tasks):
        if task in gaps: ax.plot(gaps[task],i,'o',color='#2563a6',markersize=5)
        else: ax.text(-.97,i,'pair missing',va='center',fontsize=8,color='#666666')
    ax.axvline(0,color='#555555',linewidth=.8)
    ax.set(yticks=range(len(tasks)),yticklabels=tasks,xlim=(-1.03,1.03),
           xlabel='Turn-2 TCS: capability − safety',title='Model A: every paired task')
    ax.invert_yaxis(); ax.grid(axis='x',alpha=.18)
    save(fig,'task_framing_gap')
    fig,ax=plt.subplots(figsize=(6,3.8))
    for i,(c,v) in enumerate(summary['conditions'].items()):
        if v['estimate'] is None:
            ax.text(i,.03,'NA',ha='center')
        else:
            ax.plot(i,v['estimate'],'o',color=colors[c],markerfacecolor=colors[c] if len(c)==1 else 'white',markersize=7)
            if v['lower'] is not None:
                ax.vlines(i,v['lower'],v['upper'],color=colors[c],linewidth=1.6)
            ax.annotate(f"n={v['completed']}",(i,v['estimate']),xytext=(0,10),textcoords='offset points',ha='center',fontsize=8)
    ax.set(xticks=range(4),xticklabels=list(summary['conditions']),ylim=(-.04,1.15),ylabel='Turn-2 TCS',
           title='Model A condition means and 95% task-bootstrap intervals')
    ax.grid(axis='y',alpha=.18); save(fig,'condition_means')
    fig,ax=plt.subplots(figsize=(6,3.8))
    for i,(c,v) in enumerate(summary['conditions'].items()):
        if v['repair_gain_mean'] is not None:
            ax.bar(i,v['repair_gain_mean'],color=colors[c],alpha=.85,width=.55)
        else: ax.text(i,0,'NA',ha='center')
    ax.axhline(0,color='#555555',linewidth=.8)
    ax.set(xticks=range(4),xticklabels=list(summary['conditions']),ylim=(-1.05,1.05),
           ylabel='Mean Turn-2 − Turn-1 TCS',title='Model A repair gain (completed trajectories)')
    ax.grid(axis='y',alpha=.18); save(fig,'repair_gain')
    fig,ax=plt.subplots(figsize=(5,5))
    c=summary['contrasts']['DisclosureEffect_C_A']['task_values']
    s=summary['contrasts']['DisclosureEffect_S_A']['task_values']
    groups={}
    for task in sorted(c.keys() & s.keys()):
        groups.setdefault((round(c[task],10),round(s[task],10)),[]).append(task)
    for (x,y),members in groups.items():
        ax.scatter([x],[y],s=25+12*len(members),color='#2563a6',alpha=.7)
        label=members[0].removeprefix('task_') if len(members)==1 else f'n={len(members)}'
        ax.annotate(label,(x,y),xytext=(6,6),textcoords='offset points',fontsize=8)
    ax.plot([-1,1],[-1,1],color='#777777',linewidth=.8)
    ax.set(xlim=(-1.05,1.05),ylim=(-1.05,1.05),xlabel='CD − C',ylabel='SD − S',
           title='Disclosure effects (coincident tasks grouped)')
    ax.grid(alpha=.18); save(fig,'disclosure_effects')


def report_text(summary):
    contrasts=summary['contrasts']
    rows=['# Model A initial results — Sprint 7','',
          f"All {summary['terminal']} frozen Model-A trajectories have terminal records across 16 tasks. "
          'The protocol, scoring and analyses follow the local preregistration. Model B has not been analyzed.','',
          '## Condition outcomes','',
          '| Condition | Completed / planned | Provider failures | Turn-2 mean [95% CI] | Turn-1 mean | Mean repair gain | Turn-2 format failures |',
          '|---|---:|---:|---|---:|---:|---:|']
    for c,v in summary['conditions'].items():
        rows.append(f"| {c} | {v['completed']}/16 | {v['provider_failed']} | {interval(v)} | "
                    f"{fmt(v['turn1_mean'])} | {fmt(v['repair_gain_mean'])} | {v['turn2_format_failures']}/{v['turn2_format_evaluable']} |")
    rows+=['','Condition means use all completed trajectories; contrast-specific matched means are recorded in summary.json.',
           'Turn-1 means include observed Turn 1 even if Turn 2 later has a provider failure. Repair uses completed trajectories.',
           '','![Condition means](condition_means.png)','','## Paired contrasts','',
           '| Contrast | Complete tasks | Estimate [95% CI] | Zero-provider-utility sensitivity | Valid-format sensitivity |',
           '|---|---:|---|---|---|']
    for name,v in contrasts.items():
        rows.append(f"| {name} | {v['tasks']} | {interval(v)} | {interval(v['utility_sensitivity'])} | {interval(v['valid_format_sensitivity'])} |")
    rows+=['','Positive baseline gaps favor capability framing. Interaction is (SD−S)−(CD−C). '
           'Each contrast retains its own complete pairs/quadruples. The 95% percentile intervals use '
           '10,000 task resamples with seed 2026111509. No requirement-independent significance tests are used.',
           '','![Every task](task_framing_gap.png)','','![Disclosure effects](disclosure_effects.png)',
           '','## Requirement-level self-assessment, Turn 2','',
           '| Condition | Metric | Numerator / denominator | Micro ratio | Equal-task macro | Defined tasks |',
           '|---|---|---:|---:|---:|---:|']
    count_notes=[]
    for c,turns in summary['self_assessment'].items():
        for name,v in turns['2']['metrics'].items():
            rows.append(f"| {c} | {name} | {v['numerator']}/{v['denominator']} | {fmt(v['micro'])} | {fmt(v['macro'])} | {v['defined_tasks']} |")
        counts=turns['2']['counts']
        count_notes+=['',f"{c} Turn-2 claim counts: {counts['claimed_implemented']} implemented; {counts['claimed_unmet']} not fully implemented; "
               f"{counts['claimed_uncertain']} uncertain; {counts['claimed_missing']} missing; "
               f"{counts['actual_failed_requirements']} actually failed requirements.",'']
    rows+=count_notes
    rows+=['Undefined denominators are NA, including disclosure recall when no requirements fail. '
           'Strict acknowledgement counts not-fully-implemented; lenient adds uncertain. Missing remains distinct. '
           'Underlying outcomes are the frozen artifact requirement checks. CSVs include both turns and all numerator/denominator counts.',
           '','## Repair, missingness, and costs','','![Repair gain](repair_gain.png)','']
    for c,v in summary['conditions'].items():
        rows.append(f"- {c} provider failure types: {v['failures_by_type'] or 'none'}.")
    cost=summary['costs']
    rows+=['',f"Recorded outcomes: {cost['attempts']} attempts, {cost['retries']} retries. "
           f"Known reported cost: {cost['known_reported_cost']:.6f} credits; known token-rate estimate: "
           f"{cost['known_token_estimated_cost']:.6f} credits. {cost['outcomes_with_unknown_usage']} outcomes lack complete token usage. "
           'Unknown liabilities remain reserved in the private shared ledger; known cost is not independently verified account billing.',
           '','## Interpretation and limitations','',
           'These estimates describe the frozen benign benchmark and the requested Qwen route. '
           'They do not establish intent, a mechanism, or a universal language-model effect. '
           'Inspect per-task outcomes and condition distributions for ceiling/floor effects; a narrow or zero empirical '
           'bootstrap interval on a saturated sample cannot establish equivalence outside these tasks. '
           'Wide intervals remain inconclusive for moderate effects. Provider/filter failures are missing in the primary '
           'analysis and zero only in the separately reported utility sensitivity.',
           '',
           'The study has sixteen self-reviewed tasks, limited pilot headroom, no independent task reviewer, '
           'estimated output-token fit, an unconfirmed official account rate limit, and provider routing/version limits. '
           'The fixed serial throttle and unchanged generation settings were retained. '
           'Model-B replication and final joint interpretation remain later sprints.',
           '','## Reproduction','',
           'Run from the repository root:',
           '','~~~powershell',
           '.\\.venv\\Scripts\\python.exe -m analysis.model_a --dataset report/model_a/scored_dataset.json --output report/model_a_reproduced',
           '~~~','',
           'The released dataset contains scored outcomes, claims, counts, cost summaries, and integrity digests, '
           'with no model response text. Raw responses, public feedback, snapshots, and terminal identities remain '
           'locally under data/main; frozen collection and outcome hashes link the release back to those artifacts.','']
    return '\n'.join(rows)
