"""Two-counter release-curve sensitivities, not a calibrated view forecast."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json
import numpy as np

SOURCE = Path('data/deep_review_20261017/gta204_counter_followup_1810.json')
OUT = Path('research/2026-10-17-deep-review/models/gta204_results.json')


def project(n, seed, sigma=.35, floor_max=4, pace_multiplier=1, burst_weight=.10):
    source = json.loads(SOURCE.read_text())
    views = source['comparison']['current_views']/1e6
    rate = source['comparison']['observed_counter_delta']/1e6*86400/source['comparison']['elapsed_seconds']
    rng = np.random.default_rng(seed)
    # Date-only publication has an unknown time zone/hour. Broad48hour instant envelope.
    age = rng.uniform(2.25, 4.25, n)
    smoothed_rate = rate * pace_multiplier * np.exp(rng.normal(0, sigma, n))
    floor = rng.uniform(0, 1, n)*np.minimum(floor_max, smoothed_rate*.8)
    pulse_views = views-floor*age
    pulse_rate = smoothed_rate-floor
    ratio = pulse_views/pulse_rate
    lo = np.full(n, -10.)
    hi = np.full(n, 10.)
    for _ in range(52):
        k = (lo+hi)/2
        observed_ratio = np.where(np.abs(k) < 1e-9, age, np.expm1(k*age)/np.where(k == 0, 1, k))
        below = observed_ratio < ratio
        lo = np.where(below, k, lo)
        hi = np.where(below, hi, k)
    k = (lo+hi)/2
    factor = np.where(np.abs(k) < 1e-8, 7/age, np.expm1(-k*7)/np.expm1(-k*age))
    final = floor*7+pulse_views*factor
    # Explicit unknown promotion/re-sharing branch, not an announced event.
    new_burst = rng.random(n) < burst_weight
    final += new_burst*rng.uniform(0, 20, n)
    # No negative view correction in the central model; test separately when reviewing.
    bins = [float(np.mean(final < 60)), float(np.mean((final >= 60) & (final < 80))),
            float(np.mean(final >= 80))]
    assert abs(sum(bins)-1) < 1e-12
    assert np.all(final >= views)
    return {'n': n, 'sigma_log_smoothed_rate': sigma, 'floor_max_million_per_day': floor_max,
            'pace_multiplier': pace_multiplier, 'unknown_burst_weight': burst_weight,
            'probability_below60_60to80_atleast80': bins,
            'median_million': float(np.median(final)), 'p05_p95_million': np.quantile(final, [.05,.95]).tolist(),
            'negative_decay_growth_fraction': float(np.mean(k < 0))}


def main():
    s = json.loads(SOURCE.read_text())
    raw = gzip.decompress(Path(s['current_capture']['gzip_body_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == s['current_capture']['raw_body_sha256']
    assert b'42636582' in raw and b'rz1B4B2yBZY' in raw
    base = project(50000, 20420261018)
    configs = [('narrower_short_rate', {'sigma': .20}), ('wider_short_rate', {'sigma': .60}),
               ('no_floor', {'floor_max': 0}), ('larger_floor', {'floor_max': 6}),
               ('slower_smoothed_pace', {'pace_multiplier': .6}),
               ('faster_smoothed_pace', {'pace_multiplier': 1.4}),
               ('no_new_promotion', {'burst_weight': 0}), ('larger_promotion', {'burst_weight': .30})]
    sensitivity = {name: project(30000, 20420261019+i, **kw) for i,(name,kw) in enumerate(configs)}
    out = {'written_utc': datetime.now(timezone.utc).isoformat(), 'review_index': 204,
           'before_reading_own_PM_quote': True, 'source_packet': str(SOURCE),
           'source_packet_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           'views': s['comparison']['current_views'], 'observed_counter_delta': s['comparison']['observed_counter_delta'],
           'observation_seconds': s['comparison']['elapsed_seconds'],
           'observed_counter_rate_million_per_day_equivalent': s['comparison']['observed_counter_delta']/1e6*86400/s['comparison']['elapsed_seconds'],
           'method': 'C(t)=A*(1-exp(-k*t))+b*t fitted to cumulative counter and an uncertain smoothed daily rate; negative k retains growth states. Age uniform2.25-4.25days and rate logfactor represent unknown date-only timezone, diurnal/batching effects; they are assumptions, not measured uncertainty distributions.',
           'base': base, 'sensitivity': sensitivity,
           'primary_p_yes': round(base['probability_below60_60to80_atleast80'][1], 2),
           'primary_range': [.10, .85], 'actual_entry_reserve_pp': 25,
           'calibration': 'No historical first-day trajectory or holdout fit; this is sensitivity-led primary judgment, not calibrated posterior/lower bound.',
           'limits': ['Two cumulative observations over16.5min do not identify a whole-day view intensity or intrinsic counter freshness.',
                      'Date-onlyOct15 publication does not establish exact 168hour cutoff; no deadline time invented.',
                      'Floor, smoothing factor, promotion chance and stationary release-curve shape are subjective; major source/model errors can reverse the bucket forecast.',
                      'Only exact official video/channel counter counts; Trailer1/2, allplatform totals, reuploads and comments not substituted.',
                      'Counter filtering/revisions, deletion/unavailability and unforeseen promotions can alter final source, not captured by a guaranteed bound.']}
    assert not OUT.exists(), 'write new version rather than overwrite initial model'
    OUT.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({'p_yes': out['primary_p_yes'], 'base': base,
                      'sensitivities': {k:v['probability_below60_60to80_atleast80'][1] for k,v in sensitivity.items()}}))


if __name__ == '__main__':
    main()
