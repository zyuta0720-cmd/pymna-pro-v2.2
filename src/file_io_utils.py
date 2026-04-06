# Copyright (c) 2026 Zyutama
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

"""
solver_core.py: MNA engine for automotive circuit analysis.
"""
"""
file_io_utils.py
Utilities for file I/O (CSV, LTspice) and Preset Circuit management.
"""
import csv
import re
import os
import webbrowser
from tkinter import messagebox
import pymna_config

VERSION = "2.2.0"
LAST_UPDATE = "2026-04-06"

def open_preset_image(preset_key):
    """Opens the circuit diagram image in a web browser."""
    url = pymna_config.PRESET_URLS.get(preset_key)
    if url:
        webbrowser.open(url)
    else:
        messagebox.showinfo("Info", "Circuit diagram URL not defined.")


def export_results_to_csv(filepath, input_raw, analysis_data, power_data=None, assignments=None, all_comps_info=None, last_assignments_detail=None):
    """元コードの完全なCSVエクスポート機能を再現"""
    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["--- Input Netlist ---"])
            for line in input_raw.strip().split('\n'):
                row_parts = re.split(r'\t|\s+', line.strip())
                writer.writerow(row_parts)
            
            writer.writerow([])
            writer.writerow(["--- Analysis Results ---"])
            writer.writerow(["Node", "Typical [V]", "Min [V]", "Max [V]"])
            writer.writerows(analysis_data)

            # 各ノードのMin/Max電圧を達成した際のコンポーネントパラメータを出力
            if last_assignments_detail and all_comps_info:
                writer.writerow([])
                writer.writerow(["--- Component Parameters for Worst Case Voltages ---"])
                
                # 全てのコンポーネント名をソートしてヘッダーを作成
                all_comp_names = sorted(list(all_comps_info.keys()))
                param_header = ["Node", "Case"] + all_comp_names
                writer.writerow(param_header)

                # 各ノードのMAX電圧時のパラメータ
                for node, params_dict in last_assignments_detail['voltage_max_params'].items():
                    row_data = [node, "MAX Voltage"]
                    for comp_name in all_comp_names:
                        row_data.append(params_dict.get(comp_name, all_comps_info.get(comp_name, {}).get('typ', '-'))) # 該当コンポーネントの値をセット
                    writer.writerow(row_data)
                
                # 各ノードのMIN電圧時のパラメータ
                for node, params_dict in last_assignments_detail['voltage_min_params'].items():
                    row_data = [node, "MIN Voltage"]
                    for comp_name in all_comp_names:
                        row_data.append(params_dict.get(comp_name, all_comps_info.get(comp_name, {}).get('typ', '-'))) # 該当コンポーネントの値をセット
                    writer.writerow(row_data)

            if assignments:
                writer.writerow([])
                writer.writerow(["--- Parameter Assignments ---"])
                writer.writerow(["Case", "Assignments"])
                # assignmentsは既に ['Node X (To MAX)', 'R1:max, R2:min'] の形式なのでそのまま出力
                for entry in assignments:
                    writer.writerow(entry)
            
            if power_data:
                writer.writerow([])
                writer.writerow(["--- Resistor Power Dissipation ---"])
                writer.writerow(["Resistor", "Typical [W]", "Max [W]", "Rated [W]", "P_limit [W]", "Load [%]", "Status"])
                writer.writerows(power_data)
        return True
    except Exception as e:
        messagebox.showerror("CSV Error", f"Failed to save CSV: {str(e)}")
        return False

def save_asc_file(filepath, netlist, comps):
    """ネットリストをLTspice回路図(.asc)形式に変換して保存"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("Version 4\nSHEET 1 880 680\n")
            x, y = 112, 96
            sym_map = {'r': 'res', 'v': 'voltage', 'i': 'current', 'c': 'cap', 'l': 'ind'}
            for row in netlist:
                rtype = row[0].lower()
                name = row[1]
                # Use 'raw' value from comps dictionary for correct E/F parsing
                val = comps[name]['raw'] if name in comps and 'raw' in comps[name] else "0"
                
                # For E and F sources, the symbol might be different or not directly mapped
                # The user requested "配線できてなくていいから" so basic symbol placement is fine.
                
                sym = sym_map.get(rtype, rtype)
                f.write(f"SYMBOL {sym} {x} {y} R0\nSYMATTR InstName {name}\nSYMATTR Value {val}\n")
                y += 112
        return True
    except Exception as e:
        messagebox.showerror("ASC Error", str(e))
        return False

def save_ltspice_netlist(filepath, netlist, comps):
    """LTspice実行用の.cirネットリストを出力"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("* LTspice Netlist Export\n")
            for row in netlist:
                rtype, name = row[0].upper(), row[1]
                n1, n2 = row[2], row[3]
                if rtype in ['R', 'V', 'I']:
                    f.write(f"{rtype}{name} {n1} {n2} {comps[name]['raw']}\n")
                elif rtype == 'E':
                    f.write(f"E{name} {n1} {n2} {row[4]} {row[5]} {comps[name]['raw']}\n")
                elif rtype == 'F':
                    f.write(f"F{name} {n1} {n2} V{row[4]} {comps[name]['raw']}\n")
            f.write(".tran 0 1 0 0.01\n.end\n")
        return True
    except:
        return False
