"""Final-analysis entry points for the unchanged, frozen task bootstrap."""
from harness.bootstrap import complete_contrast, paired_bootstrap


def estimate(tasks, weights, settings):
    """Form one contrast per complete task, then resample whole task values."""
    values = complete_contrast(tasks, weights)
    return {**paired_bootstrap(values, settings), 'task_values': values}
