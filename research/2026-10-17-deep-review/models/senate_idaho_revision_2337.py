"""Dated primary source revision. Research only; never replaces the v1 files."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

from senate_primary_model import simulate

HERE = Path(__file__).resolve().parent
INPUT = HERE / 'senate_idaho_revision_2337_inputs.json'
OUTPUT = HERE / 'senate_idaho_revision_2337_results.json'


def main():
    if OUTPUT.exists():
        raise SystemExit('Dated results already exist; preserve them and use a new revision.')
    inputs = json.loads(INPUT.read_text())
    scenarios = {
        'central_revised': {},
        'ID_original_equal_weights': {'id_regime_weights': [.5, .5]},
        'ID_ATR_only': {'id_regime_weights': [1., 0.]},
        'ID_Peak_only': {'id_regime_weights': [0., 1.]},
        'ID_ATR_10percent': {'id_regime_weights': [.1, .9]},
        'ID_ATR_40percent': {'id_regime_weights': [.4, .6]},
        'no_mean_poll_bias': {'poll_bias': 0.},
        'adverse_mean_poll_bias': {'poll_bias': -3.},
        'generic_D6': {'generic': 6.},
        'generic_D10': {'generic': 10.},
        'no_personal_retention': {'personal_retention': 0.},
        'full_personal_retention': {'personal_retention': 1.},
        'all_ambiguous_protem_R': {'protem_d': 0., 'protem_other': 0.},
        'all_ambiguous_protem_D': {'protem_d': 1., 'protem_other': 0.},
        'house_lower_correlation': {'house_loading': .35},
        'house_higher_correlation': {'house_loading': .85},
        'stacked_adverse_D': {
            'generic': 6., 'poll_bias': -3., 'personal_retention': 0.,
            'all_independent_d': 0., 'protem_d': 0., 'protem_other': 0.
        },
        'stacked_favorable_D': {
            'generic': 10., 'poll_bias': 0., 'personal_retention': 1.,
            'all_independent_d': 1., 'protem_d': 1., 'protem_other': 0.
        },
    }
    results = {name: simulate(inputs, **options) for name, options in scenarios.items()}
    out = {
        'authored_by': 'primary',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'Uncalibrated primary source revision, before1870 quote; not an execution instruction.',
        'source_files_sha256': {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [INPUT, HERE / 'senate_primary_model.py', Path(__file__)]
        },
        'new_fact_packet': 'data/deep_review_20261017/idaho_literal_source_followup.json',
        'previous_results_preserved': str(HERE / 'senate_primary_results.json'),
        'scenarios': results,
    }
    OUTPUT.write_text(json.dumps(out, indent=2) + '\n')
    for name, value in results.items():
        idaho = next(row for row in value['seat_outputs'] if row['seat'] == 'ID')
        print(name, 'ID', round(idaho['non_republican_win_probability'], 5),
              'D', round(value['D_senate_control'], 5),
              'R', round(value['R_senate_control'], 5),
              'Other', round(value['other_senate_control'], 5),
              'DD', round(value['joint']['D_senate_D_house'], 5),
              'RR', round(value['joint']['R_senate_R_house'], 5))


if __name__ == '__main__':
    main()
