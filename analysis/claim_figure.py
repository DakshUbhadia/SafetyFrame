"""Editorial claim-versus-ground-truth figure from unchanged Model A outcomes."""
from harness.artifacts import digest, read_json, write_json
from harness.preflight import ROOT


def counts(dataset):
    if dataset['role'] != 'A':
        raise ValueError('The accounting result belongs to Model A')
    selected = [r for r in dataset['records'] if r['trajectory']['condition'] in ('CD', 'SD')
                and r['trajectory']['status'] == 'completed']
    if not selected or any(len(r['turns']) != 2 for r in selected):
        raise ValueError('Completed accounting trajectories must have two turns')
    failed = implemented = acknowledged = missing = affected = entries = all_implemented = 0
    for record in selected:
        turn = record['turns'][1]
        requirements, claims = turn['requirements'], turn['claims']
        if not isinstance(claims, dict) or set(claims) != set(requirements):
            raise ValueError('Require parsed requirement-level claims')
        failures = [rid for rid, passed in requirements.items() if not passed]
        failed += len(failures)
        affected += bool(failures)
        entries += len(claims)
        all_implemented += sum(v == 'implemented' for v in claims.values())
        implemented += sum(claims[rid] == 'implemented' for rid in failures)
        acknowledged += sum(claims[rid] in ('not_fully_implemented', 'uncertain') for rid in failures)
        missing += sum(claims[rid] == 'missing' for rid in failures)
    return dict(model='A', conditions=['CD', 'SD'], turn=2, ground_truth='artifact requirements',
        completed_trajectories=len(selected), affected_trajectories=affected,
        checklist_entries=entries, entries_claimed_implemented=all_implemented,
        failed_requirements=failed, failed_claimed_implemented=implemented,
        failed_acknowledged_incomplete_or_uncertain=acknowledged, failed_claims_missing=missing,
        source_dataset='model_a/scored_dataset.json', source_dataset_hash=digest(dataset),
        interpretation='Descriptive nested requirement counts; no intent or independent-requirement inference.')


def render(data, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11, 'svg.fonttype':'none', 'pdf.fonttype':42})
    labels = ['Failed artifact requirements', 'Claimed implemented', 'Acknowledged incomplete / uncertain']
    values = [data['failed_requirements'], data['failed_claimed_implemented'],
              data['failed_acknowledged_incomplete_or_uncertain']]
    fig, ax = plt.subplots(figsize=(9.2, 3.9))
    ax.barh(range(3), values, color=['#727272', '#b45332', '#2563a6'], height=.52)
    for i, value in enumerate(values):
        ax.text(value + .5, i, str(value), va='center', fontweight='bold', fontsize=14)
    cap = max(values + [1])
    ax.set(yticks=range(3), yticklabels=labels, ylim=(2.6, -.6), xlim=(0, cap * 1.16),
           xlabel='Requirement count', title='Every failed requirement was claimed implemented')
    ax.spines[['top','right','left']].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.set_axisbelow(True); ax.grid(axis='x', alpha=.15)
    fig.text(.5, .025,
        f"Model A, final CD/SD artifacts: {data['affected_trajectories']}/{data['completed_trajectories']} trajectories had failures.\n"
        'Claim bars refer to those failed requirements; counts are nested within tasks.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .12, 1, 1))
    for extension in ('png','svg','pdf'):
        path = output / f'claim_ground_truth.{extension}'
        fig.savefig(path, dpi=180, bbox_inches='tight')
        if extension == 'svg':
            path.write_text('\n'.join(s.rstrip() for s in path.read_text(encoding='utf-8').splitlines())+'\n',
                            encoding='utf-8', newline='\n')
    plt.close(fig)


def main():
    data = counts(read_json(ROOT / 'report/model_a/scored_dataset.json'))
    write_json(ROOT / 'report/claim_figure_data.json', data)
    render(data, ROOT / 'report/figures')
    print('Claim figure rendered from unchanged artifact requirements and parsed claims.')


if __name__ == '__main__':
    main()
