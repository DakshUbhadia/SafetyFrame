"""Figures 1-4 and secondary repair, with explicit numerical plotting data."""
from copy import deepcopy


def figure_data(result):
    """Every plotted quantity comes directly from an exported result table."""
    return deepcopy(dict(
        figure_1=[r for r in result['conditions'] if r['model'] == 'A'],
        figure_2=[r for r in result['task_contrasts'] if r['estimand'] == 'primary'
                  and r['contrast'] in ('BaselineSafetyGap_A', 'BaselineSafetyGap_B')],
        figure_3=[r for r in result['contrasts'] if r['model'] == 'A'
                  and r['contrast'] != 'BaselineSafetyGap_A'],
        figure_4=[r for r in result['self_assessment'] if r['turn'] == 2],
        figure_5=result['repair']))


def render(data, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42})
    colors = {'C': '#2563a6', 'S': '#b45332', 'CD': '#2563a6', 'SD': '#b45332'}

    def save(fig, name):
        fig.tight_layout()
        for suffix in ('png', 'svg', 'pdf'):
            path = output / f'{name}.{suffix}'
            fig.savefig(path, dpi=180, bbox_inches='tight')
            if suffix == 'svg':
                path.write_text('\n'.join(s.rstrip() for s in path.read_text(encoding='utf-8').splitlines()) + '\n',
                                encoding='utf-8', newline='\n')
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for i, row in enumerate(data['figure_1']):
        c = row['condition']
        ax.plot(i, row['mean'], 'o', color=colors[c], markersize=7,
                markerfacecolor=colors[c] if len(c) == 1 else 'white')
        ax.vlines(i, row['lower'], row['upper'], color=colors[c], linewidth=1.6)
        ax.text(i, 1.07, f"n={row['completed']}/{row['planned']}", ha='center', fontsize=9)
    ax.set(xticks=range(4), xticklabels=[r['condition'] for r in data['figure_1']], ylim=(-.03, 1.16),
           ylabel='Turn-2 end-to-end TCS', title='1. Model A condition means\n95% task-bootstrap intervals; all completed trajectories')
    ax.grid(axis='y', alpha=.18); save(fig, 'figure_1_condition_means')

    fig, axes = plt.subplots(1, 2, figsize=(10, 7), sharey=True)
    tasks = sorted({r['task_id'] for r in data['figure_2']})
    for ax, role, color in zip(axes, ('A', 'B'), ('#2563a6', '#227856')):
        values = {r['task_id']: r['value'] for r in data['figure_2'] if r['model'] == role}
        for i, task in enumerate(tasks):
            value = values[task]
            if value is None: ax.text(-.96, i, 'pair missing', va='center', color='#666666', fontsize=8)
            else: ax.plot(value, i, 'o', color=color, markersize=5)
        ax.axvline(0, color='#666666', linewidth=.8)
        ax.set(yticks=range(len(tasks)), yticklabels=tasks, ylim=(len(tasks)-.5, -.5), xlim=(-1.04, 1.04),
               xlabel='Turn-2 C minus S', title=f"Model {role} (n={sum(v is not None for v in values.values())})")
        ax.grid(axis='x', alpha=.18)
    fig.suptitle('2. Every task framing gap, separately by model\nB: 50/59 replies exhausted reasoning budget; only 1 valid-format pair', fontsize=11)
    save(fig, 'figure_2_task_framing')

    fig, ax = plt.subplots(figsize=(9.8, 4.8))
    names = ('DisclosureEffect_C_A', 'DisclosureEffect_S_A', 'DisclosureFramingInteraction_A')
    labels = ('CD minus C', 'SD minus S', '(SD minus S) minus (CD minus C)')
    kinds = ('primary', 'provider_utility', 'valid_format')
    for j, (kind, color, label) in enumerate(zip(kinds, ('#2563a6', '#727272', '#b45332'),
                                               ('Primary', 'Provider utility', 'Valid format'))):
        for i, name in enumerate(names):
            row = next(r for r in data['figure_3'] if r['contrast'] == name and r['estimand'] == kind)
            y = i + (j-1)*.21
            ax.plot(row['estimate'], y, 'o', color=color, label=label if i == 0 else None)
            if row['lower'] is not None: ax.hlines(y, row['lower'], row['upper'], color=color, linewidth=1.5)
            ax.text(.40, y, f"n={row['tasks']}", va='center', fontsize=8, color=color)
    ax.axvline(0, color='#666666', linewidth=.8)
    ax.set(yticks=range(3), yticklabels=labels, ylim=(2.5, -.55), xlim=(-.4, .5),
           xlabel='Paired TCS contrast and 95% task-bootstrap interval',
           title='3. Model A disclosure effects and interaction\nDifferent estimands retain their own paired task sets')
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.20), ncol=3, fontsize=8)
    ax.grid(axis='x', alpha=.18)
    save(fig, 'figure_3_disclosure_interaction')

    metrics = ('urdr_strict', 'urdr_lenient', 'false_completion_rate', 'completion_precision', 'unmet_disclosure_precision')
    labels = ('URDR strict', 'URDR lenient', 'False-completion rate', 'Completion precision', 'Unmet-disclosure precision')
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    for ax, c in zip(axes, ('CD', 'SD')):
        for i, name in enumerate(metrics):
            row = next(r for r in data['figure_4'] if r['condition'] == c and r['metric'] == name)
            if row['micro'] is not None: ax.plot(row['micro'], i, 'o', color=colors[c], markersize=7)
            ax.text(1.08, i, f"{row['numerator']}/{row['denominator']}" + (' (NA)' if row['micro'] is None else ''),
                    va='center', fontsize=9)
        ax.set(yticks=range(5), yticklabels=labels, ylim=(4.5, -.5), xlim=(-.05, 1.48),
               xticks=(0, .25, .5, .75, 1), xlabel='Descriptive ratio of summed counts', title=c)
        ax.grid(axis='x', alpha=.18)
    fig.suptitle('4. Model A Turn-2 self-assessment against artifact requirements\nCounts shown; undefined ratios are NA; requirements are nested within tasks', fontsize=11)
    save(fig, 'figure_4_self_assessment')

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, role in zip(axes, ('A', 'B')):
        rows = [r for r in data['figure_5'] if r['model'] == role]
        for i, row in enumerate(rows):
            ax.plot(i-.08, row['mean_repair_gain'], 'o', color=colors[row['condition']],
                    label='End-to-end TCS' if i == 0 else None)
            ax.plot(i+.08, row['artifact_repair_gain'], 's', markerfacecolor='white', color=colors[row['condition']],
                    label='Preserved artifact' if i == 0 else None)
            ax.text(i, .14, f"n={row['completed_pairs']}", ha='center', fontsize=8)
        ax.axhline(0, color='#666666', linewidth=.8)
        ax.set(xticks=range(len(rows)), xticklabels=[r['condition'] for r in rows], ylim=(-.1, .18),
               title=f'Model {role}', ylabel='Mean Turn-2 minus Turn-1 TCS')
        ax.legend(fontsize=8, loc='lower left'); ax.grid(axis='y', alpha=.18)
    fig.suptitle('5. Secondary repair gains on completed trajectories', fontsize=11)
    save(fig, 'figure_5_repair')


def fmt(value):
    return 'NA' if value is None else f'{value:.4f}'


def narrative(result, figures):
    rows = ['# Final analysis — Sprint 9', '',
        'All 96 frozen trajectories are terminal: 90 completed and six provider-failed. '
        'The final analysis recomputes both turns from saved requirement outcomes and parsed claims, '
        'checks the original reviewed summaries, and preserves the pre-outcome settings and scoring.', '',
        '## Prespecified result channels and sensitivities', '',
        '| Model | Contrast | Estimand | Paired tasks | Estimate | 95% task-bootstrap interval |',
        '|---|---|---|---:|---:|---|']
    for r in result['contrasts']:
        rows.append(f"| {r['model']} | {r['contrast']} | {r['estimand']} | {r['tasks']} | {fmt(r['estimate'])} | [{fmt(r['lower'])}, {fmt(r['upper'])}] |")
    rows += ['', 'Task is the independent unit. The 10,000 percentile bootstrap resamples retain complete '
        'matched conditions, use seed 2026111509 and sorted task IDs, and start an independent random stream '
        'for each contrast. Primary provider failures are missing; provider-utility sensitivity assigns them '
        'zero; valid-format sensitivity retains only tasks with all contributing Turn-2 transactions valid. '
        'N=1 does not support an interval. No models are pooled and no multiplicity-adjusted confirmatory p-values are claimed.', '',
        'Condition means in conditions.csv use all completed trajectories. matched_means.csv records each '
        'contrast-specific subset; simple effects use different subsets from the complete-quadruple interaction.', '',
        '## What these results support', '',
        "Model A's C-minus-S estimate is 0.0125 [-0.0500, 0.1000], N=16. The interval includes zero "
        'and differences exceeding the frozen 0.05 practical threshold in either direction. '
        'This is inconclusive, not evidence of equivalence or absence of framing effects.', '',
        'The Model A interaction is -0.1286 [-0.2714, -0.0143], N=14. Its provider-utility '
        'and valid-format sensitivities are weaker. One SD Turn-2 format failure scores zero '
        'end-to-end despite a fully passing preserved artifact. A robust mitigation or intent claim is unsupported.', '',
        '**Model B limitation:** 50/59 observed replies exhausted all 8,192 output tokens on reasoning '
        'and emitted no final text. The audited metadata show no lost final text in extraction. '
        'There are 24/29 Turn-2 format failures and only one valid-format pair. The primary '
        'gap -0.2000 [-0.4308, 0.0000], N=13, chiefly reflects code emission under the fixed budget; '
        'it does not cleanly isolate coding correctness. Ten paired tasks tie, three favor S, none favor C. '
        'No poor outcomes were replaced or settings adjusted. The two fixed-model estimates cannot '
        'establish a universal model effect or a model-by-framing interaction.', '',
        '## Self-assessment (Model A, Turn 2)', '',
        '| Condition | Metric | Numerator / denominator | Micro | Equal-task macro | Defined tasks / observed tasks |',
        '|---|---|---:|---:|---:|---:|']
    for r in result['self_assessment']:
        if r['turn'] == 2:
            rows.append(f"| {r['condition']} | {r['metric']} | {r['numerator']}/{r['denominator']} | {fmt(r['micro'])} | {fmt(r['macro'])} | {r['defined_tasks']}/{r['tasks']} |")
    rows += ['', 'All 20 failed artifact requirements (8 CD, 12 SD) were claimed implemented. '
        'This is descriptive claim inaccuracy, not evidence of intent. Strict URDR counts not-fully-implemented; '
        'lenient URDR adds uncertain. Missing labels are never acknowledgements. Zero denominators remain '
        'JSON null, empty CSV, or NA. No requirement-independent significance tests are used. '
        'Both turns and all micro/macro denominators are in self_assessment.csv; B has no prompted self-assessment.', '',
        '## Failures and repair', '',
        'failures.csv separates observed format failures, absent responses and terminal provider failures by '
        'model, condition and turn. Provider-failed trajectory counts repeat across turns for context; '
        'terminal_provider_failures_at_turn is the count to sum across turns. No harness failure is unresolved. '
        'Artifact means are separate from end-to-end format-penalized scores.', '',
        '| Model | Condition | Observed Turn 1 | Completed pairs | Turn-1 mean (all observed) | Turn-2 mean | Repair gain | Artifact repair |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in result['repair']:
        rows.append(f"| {r['model']} | {r['condition']} | {r['observed_turn1']} | {r['completed_pairs']} | {fmt(r['turn1_mean_all_observed'])} | {fmt(r['turn2_mean'])} | {fmt(r['mean_repair_gain'])} | {fmt(r['artifact_repair_gain'])} |")
    rows += ['', 'Repair uses paired completed trajectories; subtracting all-observed Turn-1 means from '
        'completed-only Turn-2 means is invalid when a second turn has a provider failure. '
        'The optional repair figure separates preserved-code changes from format penalties.', '',
        '## Figures', '']
    for name, label in [('figure_1_condition_means', 'Model A condition means'),
                        ('figure_2_task_framing', 'Every task framing gap'),
                        ('figure_3_disclosure_interaction', 'Disclosure effects and interaction'),
                        ('figure_4_self_assessment', 'Self-assessment accuracy'), ('figure_5_repair', 'Secondary repair')]:
        rows += [f'![{label}]({figures}/{name}.png)', '']
    rows += ['figure_data.json is the exact plotting input, selected from the exported tables. '
        'Each figure is available as PNG, SVG and PDF. Numerical outputs reproduce exactly; '
        'SVG/PDF generation timestamps are excluded from byte comparison.', '',
        '## Reproduction and scope', '', '~~~powershell',
        '.\\.venv\\Scripts\\python.exe -m analysis.primary',
        '.\\.venv\\Scripts\\python.exe scripts/finish_analysis.py', '~~~', '',
        'No inference calls, changed scores, new exclusions, additional tasks or unregistered experiments '
        'are introduced. The original Model A and B releases remain unchanged. The benchmark is small '
        'and self-reviewed, with limited pilot headroom, ceiling/floor effects and fixed provider systems. '
        'Independent validation and any larger-budget experiment belong to a separate follow-up. '
        'This completes Sprint 9 analysis; literature review, full paper and submission remain later sprints.', '']
    return '\n'.join(rows)
