"""Scientific Model-B figures and a separate-system comparison narrative."""
from .model_a_figures import fmt,interval


def figures(summary,compare,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    def save(fig,name):
        fig.tight_layout()
        for extension in ('png','svg','pdf'):
            path=output/f'{name}.{extension}'
            fig.savefig(path,dpi=180,bbox_inches='tight')
            if extension=='svg':
                text='\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines())+'\n'
                path.write_text(text,encoding='utf-8',newline='\n')
        plt.close(fig)
    tasks=list(summary['task_outcomes']); values=summary['contrasts']['BaselineSafetyGap_B']['task_values']
    fig,ax=plt.subplots(figsize=(6.5,6))
    for i,task in enumerate(tasks):
        if task in values: ax.plot(values[task],i,'o',color='#267653',markersize=5)
        else: ax.text(-.97,i,'pair missing',va='center',fontsize=8,color='#666666')
    ax.axvline(0,color='#555555',linewidth=.8); ax.invert_yaxis()
    ax.set(yticks=range(16),yticklabels=tasks,xlim=(-1.03,1.03),
           xlabel='Turn-2 TCS: capability − safety',title='Model B: every paired task')
    ax.grid(axis='x',alpha=.18); save(fig,'task_framing_gap')
    fig,ax=plt.subplots(figsize=(5.5,3.8))
    for i,(c,v) in enumerate(summary['conditions'].items()):
        color='#2563a6' if c=='C' else '#b45332'
        if v['estimate'] is not None:
            ax.plot(i,v['estimate'],'o',color=color,markersize=7)
            if v['lower'] is not None: ax.vlines(i,v['lower'],v['upper'],color=color,linewidth=1.6)
            ax.annotate(f"n={v['completed']}",(i,v['estimate']),xytext=(0,10),textcoords='offset points',ha='center',fontsize=8)
        else: ax.text(i,.03,'NA',ha='center')
    ax.set(xticks=[0,1],xticklabels=['C','S'],xlim=(-.5,1.5),ylim=(-.04,1.15),
           ylabel='Turn-2 TCS',title='Model B means and 95% task-bootstrap intervals')
    ax.grid(axis='y',alpha=.18); save(fig,'condition_means')
    fig,ax=plt.subplots(figsize=(6.5,6))
    for role,color,offset,marker in [('A','#2563a6',-.13,'o'),('B','#267653',.13,'s')]:
        points=compare['models'][role]['task_values']
        for i,task in enumerate(tasks):
            if task in points:
                ax.plot(points[task],i+offset,marker=marker,color=color,linestyle='none',
                        markersize=4.5,label=f'Model {role}' if i==next(j for j,t in enumerate(tasks) if t in points) else None)
    ax.axvline(0,color='#555555',linewidth=.8); ax.invert_yaxis()
    ax.set(yticks=range(16),yticklabels=tasks,xlim=(-1.03,1.03),xlabel='Turn-2 TCS: capability − safety',
           title='Same tasks, separate model-specific differences')
    ax.grid(axis='x',alpha=.18)
    handles,labels=ax.get_legend_handles_labels()
    if handles: ax.legend(handles,labels,loc='best',frameon=False)
    save(fig,'models_task_comparison')


def report_text(summary,compare):
    contrast=summary['contrasts']['BaselineSafetyGap_B']
    completed=sum(v['completed'] for v in summary['conditions'].values())
    failed=sum(v['provider_failed'] for v in summary['conditions'].values())
    rows=['# Model B framing generalization — Sprint 8','',
        f"All 32 frozen C/S trajectories are terminal: {completed} completed and {failed} provider-failed "
        'across the same sixteen final tasks. Both turns use the unchanged frozen procedure and scoring.',
        '',f"Requested Model B ID: {summary.get('requested_model_id','see frozen configuration')}. "
        'Requested and returned IDs remain available per trajectory.','',
        '## Condition outcomes and missingness','',
        '| Condition | Completed / planned | Provider failures | Turn-2 mean [95% CI] | Turn-1 mean (observed N) | Mean repair gain | Turn-2 format failures |',
        '|---|---:|---:|---|---:|---:|---:|']
    for c,v in summary['conditions'].items():
        rows.append(f"| {c} | {v['completed']}/16 | {v['provider_failed']} | {interval(v)} | {fmt(v['turn1_mean'])} (n={v['turn1_evaluable']}) | "
                    f"{fmt(v['repair_gain_mean'])} | {v['turn2_format_failures']}/{v['turn2_format_evaluable']} |")
    rows+=['','Turn-2 condition means and repair gains use completed trajectories. Turn-1 means retain every observed first turn, '
           'including a trajectory whose second turn later had a provider failure. Paired contrasts use only complete tasks; '
           'preserved-artifact scores remain separately available.',
           '','![Model B condition means](condition_means.png)','','## Model-B framing estimate','',
           f"BaselineSafetyGap_B = mean(C−S): **{interval(contrast)}**, using {contrast['tasks']} complete task pairs. "
           'Positive values favor capability framing. Intervals use 10,000 paired task resamples, seed 2026111509.',
           '',f"Matched condition means: C={fmt(contrast['matched_condition_means']['C'])}, S={fmt(contrast['matched_condition_means']['S'])}.",
           '',f"Zero-provider-utility sensitivity: {interval(contrast['utility_sensitivity'])}, N={contrast['utility_sensitivity']['tasks']}. "
           f"Valid-format sensitivity: {interval(contrast['valid_format_sensitivity'])}, N={contrast['valid_format_sensitivity']['tasks']}.",
           '','![Every Model B task](task_framing_gap.png)','','## Separate-model comparison','',
           '| Model | Complete pairs | Mean C−S [95% CI] | Matched C mean | Matched S mean |',
           '|---|---:|---|---:|---:|']
    for role,v in compare['models'].items():
        rows.append(f"| {role} | {v['tasks']} | {interval(v)} | {fmt(v['matched_condition_means']['C'])} | {fmt(v['matched_condition_means']['S'])} |")
    rows+=['','Requested model IDs: '+ '; '.join(f"{role}: {v.get('requested_model_id','see frozen configuration')}"
           for role,v in compare['models'].items())+'.']
    rows+=['','![Same tasks across both models](models_task_comparison.png)','',
        'These are separate fixed-system estimates on matched benign tasks, not a universal pooled language-model effect. '
        'Compare each model’s interval and per-task distribution; an interval spanning zero is inconclusive, and overlapping '
        'intervals do not establish that model effects are equal. Model A’s disclosure interaction and self-assessment belong '
        'to its separate factorial design; Model B has no CD/SD extension or prompted self-assessment in this frozen study.',
        '','## Provider outcomes and costs','']
    for c,v in summary['conditions'].items():
        rows.append(f"- {c} terminal provider failure types: {v['failures_by_type'] or 'none'}.")
    cost=summary['costs']
    rows+=['',f"Recorded outcomes: {cost['attempts']} attempts and {cost['retries']} frozen-policy retries. "
        f"Known reported cost: {cost['known_reported_cost']:.6f} credits; known token-rate estimate: "
        f"{cost['known_token_estimated_cost']:.6f} credits. {cost['outcomes_with_unknown_usage']} outcomes lack full usage. "
        'Unknown liabilities remain reserved; known charges are not independently verified account debits.',
        '','## Interpretation limits and reproducibility','',
        'The benchmark has sixteen self-reviewed tasks and limited pilot headroom. Ceiling/floor effects, format penalties, '
        'provider routing/version differences, missing pairs, and the broad framing package constrain interpretation. '
        'No result establishes intent or transfers automatically to other model families or safety workflows. '
        'Provider failures are missing in the primary model-behavior analysis and zero only in the labeled utility sensitivity.',
        '','The scored dataset omits response text and includes integrity digests. Raw outputs, public feedback, workspaces, '
        'hidden outcomes and identities remain under data/main. Model A’s reviewed numerical release is preserved unchanged.',
        '','~~~powershell',
        '.\\.venv\\Scripts\\python.exe -m analysis.model_b --dataset report/model_b/scored_dataset.json --output report/model_b_reproduced',
        '~~~','']
    return '\n'.join(rows)
