"""Primary subjective event trees; no prices/screens or fitted frequencies."""
import json
from pathlib import Path

fresh_agreement = .30 * .50 * (2 / 3)
agreement = .01 + .99 * fresh_agreement
blockade = fresh_agreement * .80 + (1 - fresh_agreement) * .06
blockade += (1 - blockade) * .005
kharg = .002 + .998 * (.05 * .25 + .002)
leader = .04 + .96 * (.025 + .015 + .005)
airspace = .02 + .98 * (.20 * .35 + .80 * .01)
nato = .08 + .92 * (.04 + .96 * .01)

RESULTS = {
    'calibrated': False,
    'price_inputs': False,
    '78': {'raw_p_yes': agreement, 'recorded_p_yes': .109,
           'range': [.03, .35], 'fresh_agreement': fresh_agreement,
           'past_instrument_interpretation': .01},
    '15': {'raw_p_yes': blockade, 'recorded_p_yes': .14,
           'range': [.03, .45], 'end_given_agreement': .80,
           'unilateral_end_given_no_agreement': .06,
           'uncaptured_official_statement_remaining_mass': .005},
    '122': {'raw_p_yes': kharg, 'recorded_p_yes': .02,
            'range': [.001, .20], 'uncaptured_already_transferred': .002,
            'ground_operation': .05, 'lasting_control_given_operation': .25,
            'negotiated_actual_transfer': .002},
    '129': {'raw_p_yes': leader, 'recorded_p_yes': .08,
            'range': [.01, .35], 'already_no_de_facto_control': .04,
            'future_disjoint_attack_medical': .025,
            'future_political_removal': .015, 'future_qualifying_announcement': .005},
    '143': {'raw_p_yes': airspace, 'recorded_p_yes': .10,
            'range': [.02, .40], 'unrecovered_historical_qualifying_closure': .02,
            'escalation': .20, 'whole_FIR_closure_given_escalation': .35,
            'whole_FIR_other_given_no_escalation': .01},
    '240': {'raw_p_yes': nato, 'recorded_p_yes': .13,
            'range': [.02, .65], 'Romania_incident_qualifies': .08,
            'future_distinct_encounter': .04,
            'unrecovered_earlier_encounter_remaining_mass': .01},
    'limits': ['All branch weights are uncalibrated primary judgments.',
               'Past-event and interpretation uncertainty is explicit, not a claim of exhaustive absence.',
               'No measured tail/K=5 exception; ordinary10pp decision stress retained.',
               'Physical traffic, mutual agreement, US announcement, control and force-use are different events.'],
}

if __name__ == '__main__':
    p = Path(__file__).with_name('iran_event_results.json')
    p.write_text(json.dumps(RESULTS, indent=2) + '\n')
    print(json.dumps({k: v['recorded_p_yes'] for k, v in RESULTS.items()
                      if isinstance(v, dict) and 'recorded_p_yes' in v}))
