# Copyright (c) 2026 Zyutama
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

"""
solver_core.py: MNA engine for automotive circuit analysis.
""""""
analysis_suite.py
Logic for Worst Case (with Iterative), Monte Carlo, Tornado, and Power Analysis.
"""
import numpy as np
import re

def get_derated_power(rated_p, temp, t_start=None, t_max=None):
    """周囲温度に基づいた軽減定格電力を算出します。"""
    if rated_p is None: return None
    ts = t_start if t_start is not None else 70.0
    tm = t_max if t_max is not None else 155.0
    if temp <= ts: return rated_p
    if temp >= tm: return 0.0
    return max(0.0, rated_p * (1 - (temp - ts) / (tm - ts)))

def format_power_value(value):
    """電力値を適切な単位(W, mW, uW)の文字列に整形します。"""
    if value is None: return "-"
    abs_v = abs(value)
    if abs_v >= 1.0: return f"{value:.3f} W"
    if abs_v >= 1e-3: return f"{value*1e3:.3f} mW"
    if abs_v >= 1e-6: return f"{value*1e6:.3f} uW"
    return f"{value:.3e} W"

def run_worst_case_analysis(solver, comps, use_iterative):
    """
    ワーストケース解析を実行し、最小・最大電圧を探索します。
    Returns: (v_typ, analysis_data, all_scenarios, assignments, v_min_results, v_max_results, p_min_results, p_max_results)
    """
    v_typ = solver.solve({n: d['typ'] for n, d in comps.items()})
    analysis_data = [] 
    all_scenarios = [({n: d['typ'] for n, d in comps.items()}, v_typ)]
    assignments = []
    
    v_min_results = {}
    v_max_results = {}
    p_min_results = {}
    p_max_results = {}

    # 節点名を自然順でソート
    nat_key = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
    
    for target in sorted(solver.node_map.keys(), key=nat_key):
        max_s, min_s = {}, {}
        # 感度解析による初期状態の決定
        for n, d in comps.items():
            if d['min'] == d['max']:
                max_s[n] = min_s[n] = 'typ'
            else:
                tp = {k: v['typ'] for k, v in comps.items()}; tp[n] = d['max']
                if solver.solve(tp)[target] > v_typ[target]:
                    max_s[n], min_s[n] = 'max', 'min'
                else:
                    max_s[n], min_s[n] = 'min', 'max'
        
        if use_iterative:
            # 反復法（一変数ずつの変更）で極値を探索
            for states in [max_s, min_s]:
                mode = 'max' if states is max_s else 'min'
                for _ in range(15):
                    changed = False
                    for n in comps:
                        if comps[n]['min'] == comps[n]['max']: continue
                        p_curr = {k: (comps[k]['max'] if states[k]=='max' else (comps[k]['min'] if states[k]=='min' else comps[k]['typ'])) for k in comps}
                        v_baseline = solver.solve(p_curr)[target]
                        old_state = states[n]
                        states[n] = 'min' if old_state == 'max' else 'max'
                        p_trial = {k: (comps[k]['max'] if states[k]=='max' else (comps[k]['min'] if states[k]=='min' else comps[k]['typ'])) for k in comps}
                        v_trial = solver.solve(p_trial)[target]
                        if (mode == 'max' and v_trial > v_baseline) or (mode == 'min' and v_trial < v_baseline):
                            changed = True
                        else:
                            states[n] = old_state
                    if not changed: break

        p_max = {k: (comps[k]['max'] if max_s[k]=='max' else (comps[k]['min'] if max_s[k]=='min' else comps[k]['typ'])) for k in comps}
        v_max_dict = solver.solve(p_max)
        
        p_min = {k: (comps[k]['max'] if min_s[k]=='max' else (comps[k]['min'] if min_s[k]=='min' else comps[k]['typ'])) for k in comps}
        v_min_dict = solver.solve(p_min)
        
        target_v_max = v_max_dict[target]
        target_v_min = v_min_dict[target]

        v_max_results[target] = target_v_max
        v_min_results[target] = target_v_min
        p_max_results[target] = p_max.copy()
        p_min_results[target] = p_min.copy()

        all_scenarios.extend([(p_max, v_max_dict), (p_min, v_min_dict)])
        analysis_data.append([target, f"{v_typ[target]:.4f}", f"{target_v_min:.4f}", f"{target_v_max:.4f}"])
        assignments.append([f"Node {target} (To MAX)", ", ".join([f"{k}:{max_s[k]}" for k in max_s if max_s[k]!='typ'])])
        assignments.append([f"Node {target} (To MIN)", ", ".join([f"{k}:{min_s[k]}" for k in min_s if min_s[k]!='typ'])])

    return v_typ, analysis_data, all_scenarios, assignments, v_min_results, v_max_results, p_min_results, p_max_results

def calculate_resistor_power(v_typ, all_scenarios, comps, ambient_temp):
    """全てのワーストケースシナリオにおける各抵抗の消費電力を計算し、PASS/FAILを判定します。"""
    power_rows = []
    for r in [c for c in comps.values() if c['type'] == 'R']:
        v_typ_diff = abs(v_typ.get(r['n_pos'], 0.0) - v_typ.get(r['n_neg'], 0.0))
        typ_p = v_typ_diff**2 / r['typ']
        max_p = 0.0
        # 全ワーストケースシナリオを走査して最大消費電力を特定
        for _, volts in all_scenarios:
            v_diff = abs(volts.get(r['n_pos'], 0.0) - volts.get(r['n_neg'], 0.0))
            curr_p = v_diff**2 / r['min']
            if curr_p > max_p: max_p = curr_p
            
        derated = get_derated_power(r['rated_power'], ambient_temp, r['derating_t_start'], r['derating_t_max'])
        if r['rated_power']:
            if derated > 0:
                load = (max_p / derated) * 100
                load_s, status = f"{load:.2f}%", ("FAIL" if max_p > derated else "PASS")
            else:
                load_s, status = ("Inf%" if max_p > 0 else "0.00%"), ("FAIL" if max_p > 0 else "PASS")
        else:
            load_s, status = "-", "-"
        
        power_rows.append([r['name'], format_power_value(typ_p), format_power_value(max_p), 
                           format_power_value(r['rated_power']), format_power_value(derated), load_s, status])
    return power_rows

def run_monte_carlo_sim(solver, comps, runs, dist_type, seed=None):
    """指定された分布でモンテカルロ・シミュレーションを実行し、節点ごとの全サンプルを返します。"""
    if seed is not None: np.random.seed(seed)
    samples = {}
    for _ in range(runs):
        params = {}
        for n, d in comps.items():
            if d['min'] == d['max']: params[n] = d['typ']
            elif dist_type == "gaussian":
                # 最小・最大の間を±3σと仮定
                params[n] = np.clip(np.random.normal(d['typ'], (d['max']-d['min'])/6), d['min'], d['max'])
            else:
                params[n] = np.random.uniform(d['min'], d['max'])
        v_dict = solver.solve(params)
        for node, val in v_dict.items():
            if node not in samples: samples[node] = []
            samples[node].append(val)
    return samples

def get_sensitivity_data(solver, v_typ, comps, target_node):
    """トルネードチャート用の感度データ（Typ値からの変動幅）を計算します。"""
    sensitivities = []
    base_v = v_typ[target_node]
    typ_params = {n: d['typ'] for n, d in comps.items()}
    for name, d in comps.items():
        if d['min'] == d['max']: continue
        p_min = typ_params.copy(); p_min[name] = d['min']; v_low = solver.solve(p_min)[target_node]
        p_max = typ_params.copy(); p_max[name] = d['max']; v_high = solver.solve(p_max)[target_node]
        sensitivities.append({
            'name': name, 
            'low': v_low - base_v, 
            'high': v_high - base_v, 
            'swing': abs(v_high - v_low)
        })
    sensitivities.sort(key=lambda x: x['swing'], reverse=True)
    return sensitivities
