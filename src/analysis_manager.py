# Copyright (c) 2026 Zyutama
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

"""
solver_core.py: MNA engine for automotive circuit analysis.
""""""
analysis_manager.py
Manages the execution of analysis (Worst Case, Monte Carlo) by orchestrating
solver_core and analysis_suite, and updating the GUI.
"""
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import re
import os
import numpy as np
import matplotlib.pyplot as plt

import solver_core
import analysis_suite
import file_io_utils
import pymna_config

def run_analysis(app_instance):
    """
    Worst Case Analysisのロジックを管理し、GUIを更新します。
    app_instance: PyMNAProAppのインスタンス
    """
    try:
        raw = app_instance.input_text.get("1.0", "end-1c").strip()
        if not raw: return
        raw_lines = raw.split('\n'); lines = []; line_map = {}
        for i, l in enumerate(raw_lines):
            ls = l.strip()
            if not ls or ls.startswith((';', '*')): continue
            if ';' in ls: ls = ls.split(';', 1)[0].strip()
            line_map[len(lines)] = i; lines.append(ls)
        
        netlist = [re.split(r'\t|\s+', l) for l in lines]
        solver = solver_core.MNASolver(netlist)
        comps = {}
        for i, row in enumerate(netlist):
            rtype, name = row[0].upper(), row[1]; val = 0.0; raw_val = "0"
            v_min, v_max = val, val

            if rtype in ['R', 'V', 'I']:
                val = solver_core.parse_value(row[4]); raw_val = row[4]
                if len(row) > 5:
                    tol = str(row[5]).strip()
                    if '/' in tol: p = tol.split('/'); v_min, v_max = solver_core.parse_value(p[0]), solver_core.parse_value(p[1])
                    else: t = solver_core.parse_value(tol); v_min, v_max = val*(1-t/100), val*(1+t/100)
                else: v_min, v_max = val, val
            elif rtype == 'E':
                val = solver_core.parse_value(row[6]) if len(row) > 6 else solver_core.parse_value(row[4])
                raw_val = row[6] if len(row) > 6 else row[4]; v_min, v_max = val, val
            elif rtype == 'F':
                val = solver_core.parse_value(row[5]); raw_val = row[5]; v_min, v_max = val, val

            rp, ts, tm = None, None, None
            if rtype == 'R' and i in line_map:
                cmt = raw_lines[line_map[i]].split(';', 1)
                if len(cmt) > 1:
                    p_m = re.search(r'@P=([\d.]+)([a-zA-Z]+)?', cmt[1], re.IGNORECASE)
                    if p_m: rp = solver_core.parse_value(p_m.group(1) + (p_m.group(2) if p_m.group(2) else ""))
                    ts_m = re.search(r'@T_S=([\d.]+)', cmt[1], re.IGNORECASE); ts = float(ts_m.group(1)) if ts_m else None
                    tm_m = re.search(r'@T_M=([\d.]+)', cmt[1], re.IGNORECASE); tm = float(tm_m.group(1)) if tm_m else None
            comps[name] = {'typ': val, 'min': v_min, 'max': v_max, 'type': rtype, 'raw': raw_val,
                           'name': name, 'n_pos': str(row[2]), 'n_neg': str(row[3]), 'rated_power': rp, 'derating_t_start': ts, 'derating_t_max': tm}

        v_typ, data, scenarios, assign_log, v_min_res, v_max_res, p_min_res, p_max_res = \
            analysis_suite.run_worst_case_analysis(solver, comps, app_instance.iter_var.get())
        power_rows = analysis_suite.calculate_resistor_power(v_typ, scenarios, comps, float(app_instance.ambient_temp_var.get()))

        app_instance.output_text.delete("1.0", "end"); app_instance.output_text.tag_configure("fail_line", foreground="#ff6b6b")
        app_instance.output_text.insert("end", pymna_config.TEXTS[app_instance.lang]["res_header"] + "-"*45 + "\n")
        for r in data: app_instance.output_text.insert("end", f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")

        if app_instance.show_assign_var.get():
            app_instance.output_text.insert("end", "\n--- Parameter Assignments (Worst Case Scenarios) ---\n")
            for a in assign_log:
                app_instance.output_text.insert("end", f"{a[0]}: {a[1]}\n")

        app_instance.output_text.insert("end", f"\nCondition: Ta = {app_instance.ambient_temp_var.get()} degC\n" + pymna_config.TEXTS[app_instance.lang]["power_header"] + "-"*45 + "\n")
        for r in power_rows:
            line = "\t".join(r) + "\n"
            app_instance.output_text.insert("end", line, "fail_line" if "FAIL" in line else None)

        app_instance.last_assignments = {
            'voltage_min_params': p_min_res,
            'voltage_max_params': p_max_res,
            'log_entries': assign_log
        }
        app_instance.solver, app_instance.v_typ, app_instance.comps = solver, v_typ, comps
        app_instance.last_analysis_data, app_instance.last_power_data = data, power_rows
        
        app_instance.output_text.see("end") # 末尾へスクロール
        app_instance.btn_tornado.config(state="normal")
        # LTspice保存機能はSettingsダイアログで制御されるため、ここでは直接呼び出さない
        # if app_instance.lt_var.get():
        #     file_io_utils.save_asc_file("output_circuit.asc", netlist, comps) # Save .asc
        #     file_io_utils.save_ltspice_netlist("output_circuit.cir", netlist, comps) # Save .cir
    except Exception as e: messagebox.showerror("Error", str(e))

def run_monte_carlo_analysis(app_instance):
    """
    Monte Carlo Analysisのロジックを管理し、GUIを更新します。
    app_instance: PyMNAProAppのインスタンス
    """
    try:
        raw = app_instance.input_text.get("1.0", "end-1c").strip()
        lines = [re.split(r'\t|\s+', l.strip()) for l in raw.split('\n') if l.strip() and not l.strip().startswith((';', '*'))]
        solver = solver_core.MNASolver(lines)
        comps = {}
        for row in lines:
            rtype, name = row[0].upper(), row[1]; val = 0.0
            v_min, v_max = val, val
            # モンテカルロ用の正しいパースロジック
            if rtype in ['R', 'V', 'I']:
                val = solver_core.parse_value(row[4])
                if len(row) > 5:
                    tol = str(row[5]).strip()
                    if '/' in tol: p = tol.split('/'); v_min, v_max = solver_core.parse_value(p[0]), solver_core.parse_value(p[1])
                    else: t = solver_core.parse_value(tol); v_min, v_max = val*(1-t/100), val*(1+t/100)
                else: v_min, v_max = val, val
            elif rtype == 'E':
                val = solver_core.parse_value(row[6]) if len(row) > 6 else solver_core.parse_value(row[4])
                v_min, v_max = val, val
            elif rtype == 'F':
                val = solver_core.parse_value(row[5])
                v_min, v_max = val, val
            comps[name] = {'typ': val, 'min': v_min, 'max': v_max}
        num_runs = int(app_instance.mc_runs_var.get())
        seed_val = app_instance.mc_seed_var.get().strip()
        dist_type = app_instance.dist_var.get()
        
        # analysis_suiteのモンテカルロシミュレーションを実行
        samples = analysis_suite.run_monte_carlo_sim(solver, comps, num_runs, dist_type, int(seed_val) if seed_val else None)
        
        # 詳細統計レポートの作成
        dist_name = pymna_config.TEXTS[app_instance.lang]["dist_unif"] if dist_type == "uniform" else pymna_config.TEXTS[app_instance.lang]["dist_gauss"]
        report = f"\n--- Monte Carlo Conditions ---\n"
        report += f"Runs: {num_runs}\n"
        report += f"{pymna_config.TEXTS[app_instance.lang]['mc_seed']} {seed_val if seed_val else 'None'}\n"
        report += f"{pymna_config.TEXTS[app_instance.lang]['dist_lbl']} {dist_name}\n"
        report += pymna_config.TEXTS[app_instance.lang]["mc_res_header"] + "-"*60 + "\n"
        
        nat_key = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
        for node in sorted(samples.keys(), key=nat_key):
            data = np.array(samples[node])
            m, s = np.mean(data), np.std(data)
            report += f"{node}\t{m:.4f}\t{s:.4f}\t{m-3*s:.4f}\t{m+3*s:.4f}\n"
        
        app_instance.output_text.insert("end", report)
        app_instance.output_text.see("end")

        # ヒストグラムプロットのオプション
        target_node = simpledialog.askstring("Plot", "Enter node for distribution plot:", parent=app_instance)
        if target_node and target_node in samples:
            data = np.array(samples[target_node])
            mu, sigma = np.mean(data), np.std(data)
            
            plt.figure(f"Monte Carlo Distribution: Node {target_node}", figsize=(8, 5))
            n, bins, patches = plt.hist(data, bins=30, density=True, alpha=0.7, color='skyblue', edgecolor='white', label='Simulated')
            
            if sigma > 0:
                y = ((1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-0.5 * (1 / sigma * (bins - mu))**2))
                plt.plot(bins, y, '--', color='red', linewidth=2, label='Normal Dist. Fit')
            
            plt.axvline(mu, color='navy', linestyle='-', linewidth=2, label=f'Mean: {mu:.4f}')
            plt.title(f"Voltage Distribution at Node {target_node}\n({num_runs} runs, {dist_name} Sampling)")
            plt.xlabel("Voltage [V]")
            plt.ylabel("Probability Density")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.show()            
    except Exception as e: messagebox.showerror("MC Error", str(e))