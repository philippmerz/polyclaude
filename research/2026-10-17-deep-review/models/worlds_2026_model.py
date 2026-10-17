"""Primary Worlds scenario model; transparent assumptions, not calibration.

No odds enter. Inputs are the separately verified current Riot GPR table and
qualified-team list. This research module does not trade or update priors.
"""
from pathlib import Path
from collections import Counter, defaultdict
from itertools import permutations
import json, math, random

HERE = Path(__file__).parent
TEAMS = {
    'GEN': ('LCK', 1519), 'HLE': ('LCK', 1540), 'T1': ('LCK', 1471),
    'DK': ('LCK', 1409), 'AL': ('LPL', 1409), 'BLG': ('LPL', 1513),
    'TES': ('LPL', 1364), 'IG': ('LPL', 1348), 'G2': ('LEC', 1478),
    'MKOI': ('LEC', 1320), 'KC': ('LEC', 1396), 'TLAW': ('LCS', 1369),
    'LYON': ('LCS', 1424), 'C9': ('LCS', 1326), 'TSW': ('LCP', 1371),
    'CFO': ('LCP', 1317), 'MVK': ('LCP', 1256), 'LOS': ('CBLOL', 1182),
    'FUR': ('CBLOL', 1221),
}
REGIONS = sorted({r for r, _ in TEAMS.values()})
SCENARIOS = [
    dict(name='series-unit conservative', weight=.50, unit='series', scale=600),
    dict(name='game-unit longer-series amplification', weight=.35, unit='game', scale=600),
    dict(name='sharper game mapping sensitivity', weight=.15, unit='game', scale=400),
]
SEED = 2026101754
N_DRAWS = 12000


def series_probability(p, best_of):
    needed = best_of // 2 + 1
    return sum(math.comb(best_of, k) * p**k * (1-p)**(best_of-k)
               for k in range(needed, best_of + 1))


def pairings(rng, teams, met):
    """Uniform rejection draw, then exact uniform enumeration if needed."""
    assert len(teams) % 2 == 0
    for _ in range(100):
        shuffled = list(teams)
        rng.shuffle(shuffled)
        pairs = list(zip(shuffled[::2], shuffled[1::2]))
        if all(b not in met[a] for a, b in pairs):
            return pairs, False

    def enumerate_valid(xs):
        if not xs:
            return [[]]
        a, *rest = xs
        result = []
        for j, b in enumerate(rest):
            if b in met[a]:
                continue
            for tail in enumerate_valid(rest[:j] + rest[j+1:]):
                result.append([(a, b)] + tail)
        return result

    valid = enumerate_valid(list(teams))
    if valid:
        return rng.choice(valid), False
    # The organizer may waive the no-rematch rule if no legal draw exists.
    shuffled = list(teams)
    rng.shuffle(shuffled)
    return list(zip(shuffled[::2], shuffled[1::2])), True


def run(scenario, seed, draws=N_DRAWS, play_in_state='unverified'):
    rng = random.Random(seed)
    champions, qualifiers, playin_winners = Counter(), Counter(), Counter()
    waivers = 0
    for _ in range(draws):
        region_shocks = {r: rng.gauss(0, 50) for r in REGIONS}
        ratings = {t: v + region_shocks[r] + rng.gauss(0, 65)
                   for t, (r, v) in TEAMS.items()}
        # The future patch/roster strength is persistent across this draw,
        # rather than independent fresh noise for every match.
        def win(a, b, best_of):
            p = 1 / (1 + 10 ** ((ratings[b] - ratings[a]) / scenario['scale']))
            if scenario['unit'] == 'game':
                p = series_probability(p, best_of)
            else:
                # Riot's original method describes match outcomes. A direct
                # series mapping avoids silently counting a series as games.
                # BO1s are noisier in this explicitly assumed sensitivity.
                if best_of == 1:
                    p = .5 + .70 * (p - .5)
                elif best_of == 3:
                    p = .5 + .90 * (p - .5)
            return (a, b) if rng.random() < p else (b, a)

        # The source printed CBLOL placeholders rather than exact seed labels.
        # Marginalize the two assignments instead of inventing an identity.
        if play_in_state == 'kc_mvk_final':
            direct_brazil, play_brazil = 'LOS', 'FUR'
        else:
            direct_brazil, play_brazil = rng.sample(['LOS', 'FUR'], 2)
        if play_in_state == 'kc_mvk_final':
            play_winner, _ = win('KC', 'MVK', 5)
        elif play_in_state == 'kc_upper_final_c9_eliminated':
            upper = 'KC'
            lower, _ = win(play_brazil, 'MVK', 5)
            play_winner, _ = win(upper, lower, 5)
        elif play_in_state in TEAMS:
            play_winner = play_in_state
        else:
            initial = ['KC', 'C9', 'MVK', play_brazil]
            rng.shuffle(initial)
            a, b = win(initial[0], initial[1], 5)
            c, d = win(initial[2], initial[3], 5)
            upper, upper_loser = win(a, c, 5)
            lower, _ = win(b, d, 5)
            lower, _ = win(upper_loser, lower, 5)
            play_winner, _ = win(upper, lower, 5)
        playin_winners[play_winner] += 1
        pools = [
            ['GEN', 'AL', 'TLAW', 'G2'],
            [direct_brazil, 'TSW', 'HLE', 'BLG'],
            ['LYON', 'MKOI', 'T1', 'TES'],
            ['CFO', 'IG', 'DK', play_winner],
        ]
        teams = sum(pools, [])
        assert len(set(teams)) == 16
        records = {t: [0, 0] for t in teams}
        met = {t: set() for t in teams}
        first = []
        for x, y in [(pools[0], pools[3]), (pools[1], pools[2])]:
            choices = [z for z in permutations(y)
                       if all(TEAMS[a][0] != TEAMS[b][0] for a, b in zip(x, z))]
            assert choices
            first.extend(zip(x, rng.choice(choices)))
        for round_number in range(5):
            matches = first if round_number == 0 else []
            if round_number:
                groups = defaultdict(list)
                for t, (wins, losses) in records.items():
                    if wins < 3 and losses < 3:
                        groups[(wins, losses)].append(t)
                for group in groups.values():
                    pairs, waived = pairings(rng, group, met)
                    waivers += int(waived)
                    matches.extend(pairs)
            for a, b in matches:
                assert records[a] == records[b]
                bo = 3 if max(records[a]) == 2 else 1
                winner, loser = win(a, b, bo)
                records[winner][0] += 1
                records[loser][1] += 1
                met[a].add(b)
                met[b].add(a)
        q = [t for t in teams if records[t][0] == 3]
        assert len(q) == 8
        qualifiers.update(q)
        undefeated = [t for t in q if records[t][1] == 0]
        three_two = [t for t in q if records[t][1] == 2]
        assert len(undefeated) == 2 and len(three_two) == 3
        rng.shuffle(undefeated)
        rng.shuffle(three_two)
        seeded = list(zip(undefeated, three_two[:2]))
        remaining = [t for t in q if t not in sum(([a, b] for a, b in seeded), [])]
        rng.shuffle(remaining)
        other = list(zip(remaining[::2], remaining[1::2]))
        # The undefeated teams are in opposite halves. Other placement is random.
        quarterfinals = [seeded[0], other[0], seeded[1], other[1]]
        sf = [win(a, b, 5)[0] for a, b in quarterfinals]
        final = [win(sf[0], sf[1], 5)[0], win(sf[2], sf[3], 5)[0]]
        champion = win(*final, 5)[0]
        champions[champion] += 1
    by_team = {t: champions[t] / draws for t in TEAMS}
    by_region = {r: sum(p for t, p in by_team.items() if TEAMS[t][0] == r)
                 for r in REGIONS}
    assert abs(sum(by_team.values()) - 1) < 1e-10
    assert abs(sum(by_region.values()) - 1) < 1e-10
    return dict(scenario=scenario, draws=draws, play_in_state=play_in_state,
                champion=by_team, region=by_region,
                qualify={t: qualifiers[t]/draws for t in TEAMS},
                playin_winner={t: n/draws for t, n in playin_winners.items()},
                no_rematch_waivers=waivers,
                max_binomial_mc_standard_error=.5/math.sqrt(draws))


def main():
    results = [run(s, SEED + j, play_in_state='kc_mvk_final')
               for j, s in enumerate(SCENARIOS)]
    mixed_team = {t: sum(s['weight'] * r['champion'][t]
                         for s, r in zip(SCENARIOS, results)) for t in TEAMS}
    mixed_region = {a: sum(s['weight'] * r['region'][a]
                           for s, r in zip(SCENARIOS, results)) for a in REGIONS}
    output = dict(author='primary_operator', seed=SEED, calibrated=False,
                  input_price_used=False, scenarios=results,
                  mixed_team_before_resolution_risk=mixed_team,
                  mixed_region_before_resolution_risk=mixed_region,
                  assumptions=dict(region_persistent_score_sd=50,
                                   team_persistent_score_sd=65,
                                   official_original_elo_denominator=600,
                                   original_method_year=2024,
                                   current_2026_formula_identity_proved=False,
                                   score_unit_ambiguity='series versus individual game',
                                   cbLOL_seed_identity='LOS direct; FUR eliminated in verified play-in',
                                   play_in_condition='only KC or MVK may now advance'))
    (HERE/'worlds_2026_results.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({'champion': mixed_team, 'region': mixed_region,
                      'scenario_GenG_LCK': [(r['scenario']['name'], r['champion']['GEN'],
                                             r['region']['LCK']) for r in results]}))


if __name__ == '__main__':
    main()
