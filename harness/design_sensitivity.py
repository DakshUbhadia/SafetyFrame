"""Pre-outcome planning resolution; no model data or external statistical packages."""
import argparse
import csv
import io
import math
from .artifacts import read_json
from .preflight import ROOT


def sensitivity_rows(analysis):
    design=analysis['sensitivity_design']
    return [dict(tasks=n,assumed_paired_contrast_sd=sd,
                 approximate_95pct_ci_half_width=round(design['normal_critical_value']*sd/math.sqrt(n),6))
            for n in design['task_counts'] for sd in design['assumed_paired_contrast_sds']]


def sensitivity_text(analysis):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=['tasks','assumed_paired_contrast_sd','approximate_95pct_ci_half_width'],lineterminator='\n')
    writer.writeheader(); writer.writerows(sensitivity_rows(analysis))
    return stream.getvalue()


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    text=sensitivity_text(read_json(ROOT/'config/analysis.json'))
    path=ROOT/'data/design_sensitivity.csv'
    if path.exists() and path.read_text(encoding='utf-8')!=text:
        raise ValueError('Existing design-sensitivity table differs')
    path.write_text(text,encoding='utf-8',newline='\n')
    print(text,end='')
    print('Planning approximation 1.96*SD/sqrt(n), not a power calculation or promised bootstrap width.')


if __name__=='__main__':
    main()
