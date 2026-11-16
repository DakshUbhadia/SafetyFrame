"""Study 2 paper figures from observed data only; optional pinned matplotlib."""
from collections import defaultdict
from pathlib import Path


def generate_figures(rows, summary, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)

    def save(fig, name):
        fig.tight_layout()
        for extension in ('png', 'pdf', 'svg'):
            fig.savefig(output/f'{name}.{extension}', dpi=180)
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for axis, metric in zip(axes, ('FCR', 'strict_URDR')):
        values = [r for r in summary['condition_summary'] if r['metric'] == metric and r['mean_difference'] is not None]
        for i, row in enumerate(values):
            axis.plot([row['ci_low'], row['ci_high']], [i, i], color='#265d74')
            axis.scatter(row['mean_difference'], i, color='#265d74')
        axis.set_yticks(range(len(values)), [r['audit_condition']+' / '+r['auditor_model'] for r in values])
        axis.set_xlabel(metric+' (task mean, 95% task-bootstrap CI)')
        axis.set_xlim(-.03, 1.03)
    save(fig, 'figure_1_failure_detection')
    groups = defaultdict(lambda: defaultdict(int))
    for row in rows:
        if row['ground_truth_pass'] == 0:
            groups[(row['audit_condition'], row['auditor_model'])][row['auditor_claim']] += 1
    fig, axis = plt.subplots(figsize=(10, 5))
    keys = sorted(groups)
    bottom = [0]*len(keys)
    for claim, color in [('implemented', '#ac5347'), ('not fully implemented', '#367b6c'),
                         ('uncertain', '#e5b765'), ('missing', '#a3a3a3')]:
        values = [groups[key][claim] for key in keys]
        axis.bar(range(len(keys)), values, bottom=bottom, label=claim, color=color)
        bottom = [a+b for a, b in zip(bottom, values)]
    axis.set_xticks(range(len(keys)), [' / '.join(key) for key in keys], rotation=25, ha='right')
    axis.set_ylabel('Objectively failed requirements (descriptive counts)')
    axis.legend()
    save(fig, 'figure_2_ground_truth_claims')
    confidence = [r for r in rows if r['probability_fully_satisfied'] is not None]
    if confidence:
        fig, axis = plt.subplots(figsize=(6, 4))
        for truth, label, color in [(0, 'Failed', '#ac5347'), (1, 'Passed', '#367b6c')]:
            values = [r['probability_fully_satisfied'] for r in confidence if r['ground_truth_pass'] == truth]
            axis.scatter([truth + ((i % 11)-5)*.012 for i in range(len(values))], values, alpha=.5, color=color, label=label)
        axis.set_xticks([0, 1], ['Failed', 'Passed'])
        axis.set_ylabel('Probability fully satisfied (%)')
        axis.set_ylim(-2, 102)
        save(fig, 'figure_3_confidence')
    fig, axis = plt.subplots(figsize=(10, 5))
    for row in summary['primary']:
        if row['left'] == 'builder' and row['metric'] == 'FCR':
            tasks = row['task_differences']
            axis.scatter(list(tasks), list(tasks.values()), label=row['auditor_model'])
    axis.axhline(0, color='gray', linewidth=.7)
    axis.set_ylabel('FCR builder − fresh auditor')
    axis.tick_params(axis='x', rotation=65)
    if axis.collections:
        axis.legend()
    save(fig, 'figure_4_task_improvement')
    auditors = sorted({r['auditor_model'] for r in rows if r['audit_condition'] != 'builder'})
    if len(auditors) > 1:
        from .audit_metrics import audit_metrics
        builders = sorted({r['builder_model'] for r in rows})
        matrix = []
        for builder in builders:
            matrix.append([audit_metrics([r for r in rows if r['builder_model'] == builder
                and r['auditor_model'] == auditor and r['audit_condition'] == 'fresh'])['FCR'] for auditor in auditors])
        fig, axis = plt.subplots(figsize=(7, 4))
        import numpy as np
        image = axis.imshow(np.array([[float('nan') if v is None else v for v in row] for row in matrix]),
                            vmin=0, vmax=1, cmap='YlOrRd')
        axis.set_xticks(range(len(auditors)), auditors)
        axis.set_yticks(range(len(builders)), builders)
        axis.set_xlabel('Fresh auditor; pooled descriptive FCR')
        axis.set_ylabel('Builder')
        fig.colorbar(image, ax=axis)
        save(fig, 'figure_5_cross_model_matrix')
