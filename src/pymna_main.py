# Copyright (c) 2026 Zyutama
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

"""
solver_core.py: MNA engine for automotive circuit analysis.
""""""
pymna_main.py
Main GUI Entry point. Restored full functionality with modularized engine.
"""
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import re
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

import solver_core
import analysis_suite
import file_io_utils
import pymna_config
import analysis_manager
import gui_components

# Enable High DPI
if sys.platform.startswith('win'):
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass

class PyMNAProApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.dpi_scale = self.winfo_fpixels('1i') / 96.0
        self.lang = "en" # Default to English
        self.lang_var = tk.StringVar(value="en")
        self.layout_orientation_var = tk.StringVar(value="vertical")
        self.iter_var = tk.BooleanVar(value=True) # Solver Settings
        self.show_assign_var = tk.BooleanVar(value=True) # Solver Settings
        self.ambient_temp_var = tk.StringVar(value="25") # Power Analysis Conditions
        self.lt_var = tk.BooleanVar(value=True) # LTspice Save option
        self.preset_var = tk.StringVar(value="div") # Preset selection
        self.mc_runs_var = tk.StringVar(value="1000") # Monte Carlo Runs
        self.mc_seed_var = tk.StringVar(value="") # Monte Carlo Seed
        self.dist_var = tk.StringVar(value="gaussian") # Monte Carlo Distribution
        self.is_vertical = True # Layout state
        self.help_visible = False # Help panel visibility
        self.solver = None
        self.last_analysis_data = None
        self.last_power_data = None
        self.last_assignments = None
        
        self.view = gui_components.MainView(self) # Viewインスタンスの作成
        self.view.setup_ui()                      # UIの構築（ここで各ウィジェットが生成される）

        # イベントのバインド: キー入力やクリック時にステータスバーのヒントを更新
        self.input_text.bind("<KeyRelease>", self.update_status_hint)
        self.input_text.bind("<ButtonRelease-1>", self.update_status_hint)

        self.load_preset()                        # UI構築後にデータをロード
        self.update_help_content()                # 初期ヘルプコンテンツのロード
        self.view.update_preset_ui()              # プリセットUIの初期化

    def save_cir_manual(self):
        """Manual LTspice netlist (.cir) export from the editor content."""
        raw = self.input_text.get("1.0", "end-1c").strip()
        if not raw:
            messagebox.showwarning("Tool", "Editor is empty.")
            return
        try:
            netlist, comps = self._parse_comps_for_export(raw)
            path = filedialog.asksaveasfilename(defaultextension=".cir", filetypes=[("LTspice Netlist", "*.cir")])
            if path and file_io_utils.save_ltspice_netlist(path, netlist, comps):
                messagebox.showinfo("Tool", f"Successfully exported to:\n{os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Parsing error during export: {e}")

    def save_asc_manual(self):
        """Manual LTspice schematic (.asc) export from the editor content."""
        raw = self.input_text.get("1.0", "end-1c").strip()
        if not raw:
            messagebox.showwarning("Tool", "Editor is empty.")
            return
        try:
            netlist, comps = self._parse_comps_for_export(raw)
            path = filedialog.asksaveasfilename(defaultextension=".asc", filetypes=[("LTspice Schematic", "*.asc")])
            if path and file_io_utils.save_asc_file(path, netlist, comps):
                messagebox.showinfo("Tool", f"Successfully exported to:\n{os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Parsing error during export: {e}")

    def _parse_comps_for_export(self, raw_text):
        """Helper to parse raw editor text into netlist and comps dictionary for export."""
        lines = [l.strip().split(';', 1)[0].strip() for l in raw_text.split('\n') if l.strip() and not l.strip().startswith((';', '*'))]
        netlist = [re.split(r'\t|\s+', l) for l in lines]
        comps = {}
        for row in netlist:
            rtype, name = row[0].upper(), row[1]
            val_idx = 4
            if rtype == 'E' and len(row) > 6: val_idx = 6
            elif rtype == 'F' and len(row) > 5: val_idx = 5
            comps[name] = {'raw': row[val_idx] if len(row) > val_idx else "0"}
        return netlist, comps

    def _get_layout_label(self, orientation):
        """Helper to get layout label with Japanese suffix if applicable."""
        if orientation == "horizontal":
            base_label = pymna_config.TEXTS[self.lang]["layout_horizontal_lbl"]
            suffix = pymna_config.TEXTS[self.lang]["layout_horizontal_jp_suffix"]
        elif orientation == "vertical":
            base_label = pymna_config.TEXTS[self.lang]["layout_vertical_lbl"]
            suffix = pymna_config.TEXTS[self.lang]["layout_vertical_jp_suffix"]
        else:
            return "" # Should not happen
        
        if self.lang == "jp": return f"{base_label}{suffix}"
        return base_label

    def load_preset_by_key(self, key):
        self.preset_var.set(key)
        self.load_preset()

    def update_status_hint(self, event=None):
        """カーソル位置の行に基づいた構文ヒントをステータスバーに表示"""
        try:
            line_index = self.input_text.index("insert").split(".")[0]
            line_text = self.input_text.get(f"{line_index}.0", f"{line_index}.end").strip().upper()
            
            if not line_text: hint = "Ready"
            elif line_text.startswith('R'): hint = "Resistor: R [Name] [n+] [n-] [Value] [Tol% or Min/Max]"
            elif line_text.startswith('V'): hint = "Voltage Source: V [Name] [n+] [n-] [Value] [Tol% or Min/Max]"
            elif line_text.startswith('I'): hint = "Current Source: I [Name] [n+] [n-] [Value] [Tol% or Min/Max]"
            elif line_text.startswith('E'): hint = "Op-Amp/VCVS: E [Name] [out+] [out-] [in+] [in-] [Gain]"
            elif line_text.startswith('F'): hint = "CCCS: F [Name] [out+] [out-] [VCTRL] [Gain] [Tol% or Min/Max]"
            elif line_text.startswith('*') or line_text.startswith(';'): hint = "Comment line"
            else: hint = "Syntax: Type [Name] [Nodes...] [Value] [Tolerance]"
            
            self.lbl_status.config(text=f" Syntax Hint: {hint}")
        except: pass

    def file_new(self):
        if self.input_text.get("1.0", "end-1c").strip():
            if messagebox.askyesno("PyMNA Pro", pymna_config.TEXTS[self.lang]["save_before_new"]):
                self.export_to_csv()
        self.input_text.delete("1.0", "end"); self.output_text.delete("1.0", "end")

    def file_open(self):
        path = filedialog.askopenfilename(filetypes=[("Netlist Files", "*.txt *.net *.cir")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.input_text.delete("1.0", "end")
                self.input_text.insert("1.0", f.read())

    def open_settings_dialog(self):
        win = tk.Toplevel(self); win.title("All Analysis Settings")
        win.geometry(f"{int(400*self.dpi_scale)}x{int(280*self.dpi_scale)}")
        win.configure(bg="#2d3139")
        win.transient(self)
        win.grab_set()

        main_frame = tk.Frame(win, bg="#2d3139", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # チェックボックスのスタイル定義（バグ修正: selectcolorを設定してチェックを見えるようにする）
        cb_style = {"bg": "#2d3139", "fg": "#e0e0e0", "selectcolor": "#2d3139", 
                    "activebackground": "#2d3139", "activeforeground": "#e0e0e0",
                    "font": ("Segoe UI", 10)}

        tk.Label(main_frame, text="Solver Settings", bg="#2d3139", fg="#abb2bf", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        tk.Checkbutton(main_frame, text="Enable Iterative Solver (Worst Case)", variable=self.iter_var, **cb_style).pack(anchor="w", padx=10)
        tk.Checkbutton(main_frame, text="Show Parameter Assignments in Log", variable=self.show_assign_var, **cb_style).pack(anchor="w", padx=10, pady=(5, 15))
        
        tk.Label(main_frame, text=pymna_config.TEXTS[self.lang]["power_analysis_conditions"], bg="#2d3139", fg="#abb2bf", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        temp_frame = tk.Frame(main_frame, bg="#2d3139")
        temp_frame.pack(anchor="w", padx=10)
        tk.Label(temp_frame, text="Environment Temperature (Ta) [°C]:", bg="#2d3139", fg="#e0e0e0", font=("Segoe UI", 10)).pack(side="left")
        tk.Entry(temp_frame, textvariable=self.ambient_temp_var, width=8, font=("Consolas", 11)).pack(side="left", padx=10)

        tk.Button(main_frame, text="Apply & Close", command=win.destroy, bg="#00bfff", fg="#23272e", font=("Segoe UI", 10, "bold"), width=15).pack(pady=(30, 0))

    def open_presets_dialog(self):
        preset_win = tk.Toplevel(self)
        preset_win.title("Presets")
        preset_win.geometry(f"{int(400*self.dpi_scale)}x{int(200*self.dpi_scale)}")
        preset_win.configure(bg="#2d3139")
        preset_win.transient(self)
        preset_win.grab_set()

        t = pymna_config.TEXTS[self.lang]
        display_map = t["presets"]
        display_names = list(display_map.values())
        disp_var = tk.StringVar(value=display_map.get(self.preset_var.get(), display_names[0]))

        def on_change(selected_name):
            for kid, vname in display_map.items():
                if vname == selected_name:
                    self.preset_var.set(kid)
                    break

        om = tk.OptionMenu(preset_win, disp_var, *display_names, command=on_change)
        om.config(bg="#444", fg="white", highlightthickness=0, relief="flat", width=25)
        om.pack(pady=20)

        btn_frame = tk.Frame(preset_win, bg="#2d3139")
        btn_frame.pack()

        tk.Button(btn_frame, text=t["load_btn"], command=lambda: [self.load_preset(), preset_win.destroy()], bg="#00bfff", fg="#23272e", font=("Segoe UI", int(9*self.dpi_scale), "bold"), width=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text=t["view_btn"], command=self.view_circuit, bg="#444", fg="white", width=12).pack(side="left", padx=5)


    def load_preset(self):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", pymna_config.PRESET_DATA_RAW[self.preset_var.get()]["netlist"])

    def set_language(self, lang_code):
        self.lang = lang_code
        self.lang_var.set(lang_code)
        t = pymna_config.TEXTS[self.lang]
        self.grp_analysis.config(text=t["analysis_grp"])
        self.grp_presets.config(text=t["preset_grp"])
        self.grp_mc.config(text=t["mc_grp"])
        self.btn_run.config(text=t["run_btn"])
        self.btn_tornado.config(text=t["tornado_btn"]) # ここでエラーにならないよう setup_ui で app.btn_tornado に代入しています
        self.btn_mc.config(text=t["mc_btn"])
        self.lbl_seed.config(text=t["mc_seed"])
        self.rb_unif.config(text=t["dist_unif"])
        self.rb_gauss.config(text=t["dist_gauss"])
        
        self.view_menu.entryconfig(self.view_menu.index(pymna_config.TEXTS["en" if self.lang=="jp" else "jp"]["layout_menu_lbl"]), label=t["layout_menu_lbl"])
        self.layout_menu.entryconfig(0, label=self._get_layout_label("horizontal"))
        self.layout_menu.entryconfig(1, label=self._get_layout_label("vertical"))
        self.help_menu.entryconfig(0, label=t["guide_title"])

        self.view.update_preset_ui() # 全てのプリセットUIを更新
        self.update_help_content()
    
    def set_layout_orientation(self, orientation):
        """Sets the layout orientation and updates the UI."""
        self.is_vertical = (orientation == "vertical")
        self.update_layout()

    def update_layout(self):
        self.view.update_layout()

    def toggle_help(self):
        self.help_visible = not self.help_visible
        self.update_layout()

    def update_help_content(self):
        self.help_txt.config(state="normal")
        self.help_txt.delete("1.0", "end")
        self.help_txt.insert("end", pymna_config.TEXTS[self.lang]["guide_text"])
        self.help_txt.config(state="disabled")

    def export_to_csv(self):
        if not self.last_analysis_data: return
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            file_io_utils.export_results_to_csv(path, self.input_text.get("1.0", "end-1c"), 
                                               self.last_analysis_data, self.last_power_data, 
                                               self.last_assignments['log_entries'] if self.last_assignments and 'log_entries' in self.last_assignments else None, # assignments
                                               self.comps, # all_comps_info
                                               self.last_assignments if self.last_assignments and 'voltage_max_params' in self.last_assignments else None # last_assignments_detail
                                               )

    def execute(self):
        try:
            raw = self.input_text.get("1.0", "end-1c").strip()
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
                analysis_suite.run_worst_case_analysis(solver, comps, self.iter_var.get())
            power_rows = analysis_suite.calculate_resistor_power(v_typ, scenarios, comps, float(self.ambient_temp_var.get()))

            self.output_text.delete("1.0", "end"); self.output_text.tag_configure("fail_line", foreground="#ff6b6b")
            self.output_text.insert("end", pymna_config.TEXTS[self.lang]["res_header"] + "-"*45 + "\n")
            for r in data: self.output_text.insert("end", f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")

            if self.show_assign_var.get():
                self.output_text.insert("end", "\n--- Parameter Assignments (Worst Case Scenarios) ---\n")
                for a in assign_log:
                    self.output_text.insert("end", f"{a[0]}: {a[1]}\n")

            self.output_text.insert("end", f"\nCondition: Ta = {self.ambient_temp_var.get()} degC\n" + pymna_config.TEXTS[self.lang]["power_header"] + "-"*45 + "\n")
            for r in power_rows:
                line = "\t".join(r) + "\n"
                self.output_text.insert("end", line, "fail_line" if "FAIL" in line else None)

            self.last_assignments = {
                'voltage_min_params': p_min_res,
                'voltage_max_params': p_max_res,
                'log_entries': assign_log
            }
            self.solver, self.v_typ, self.comps = solver, v_typ, comps
            self.last_analysis_data, self.last_power_data = data, power_rows
            
            self.output_text.see("end") # 末尾へスクロール
            self.btn_tornado.config(state="normal", bg="#ffc107", fg="#212529") # 明るいオレンジ色に変更
            if self.lt_var.get(): file_io_utils.save_ltspice_netlist("output_circuit.cir", netlist, comps)
        except Exception as e: messagebox.showerror("Error", str(e))

    def run_monte_carlo(self):
        try:
            raw = self.input_text.get("1.0", "end-1c").strip()
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
            num_runs = int(self.mc_runs_var.get())
            seed_val = self.mc_seed_var.get().strip()
            dist_type = self.dist_var.get()
            
            # analysis_suiteのモンテカルロシミュレーションを実行
            samples = analysis_suite.run_monte_carlo_sim(solver, comps, num_runs, dist_type, int(seed_val) if seed_val else None)
            
            # 詳細統計レポートの作成
            dist_name = pymna_config.TEXTS[self.lang]["dist_unif"] if dist_type == "uniform" else pymna_config.TEXTS[self.lang]["dist_gauss"]
            report = f"\n--- Monte Carlo Conditions ---\n"
            report += f"Runs: {num_runs}\n"
            report += f"{pymna_config.TEXTS[self.lang]['mc_seed']} {seed_val if seed_val else 'None'}\n"
            report += f"{pymna_config.TEXTS[self.lang]['dist_lbl']} {dist_name}\n"
            report += pymna_config.TEXTS[self.lang]["mc_res_header"] + "-"*60 + "\n"
            
            nat_key = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
            for node in sorted(samples.keys(), key=nat_key):
                data = np.array(samples[node])
                m, s = np.mean(data), np.std(data)
                report += f"{node}\t{m:.4f}\t{s:.4f}\t{m-3*s:.4f}\t{m+3*s:.4f}\n"
            
            self.output_text.insert("end", report)
            self.output_text.see("end")

            # ヒストグラムプロットのオプション
            target_node = simpledialog.askstring("Plot", "Enter node for distribution plot:", parent=self)
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

    def generate_tornado_chart(self):
        target = simpledialog.askstring("Input", "Target node:")
        if not target or not self.solver or not self.v_typ or target not in self.v_typ:
            messagebox.showerror("Error", f"Invalid node '{target}'. Please run analysis and select a valid node.")
            return

        sensitivities = analysis_suite.get_sensitivity_data(self.solver, self.v_typ, self.comps, target)

        if not sensitivities:
            messagebox.showinfo("Info", "No components with tolerances found to generate a chart.")
            return

        comp_names = [s['name'] for s in sensitivities]
        low_values = np.array([min(s['low'], s['high']) for s in sensitivities])
        high_values = np.array([max(s['low'], s['high']) for s in sensitivities])
        
        baseline_v = self.v_typ[target]

        fig, ax = plt.subplots(figsize=(10, max(6, len(comp_names) * 0.5)))
        bar_widths = high_values - low_values
        ax.barh(comp_names, bar_widths, left=low_values, color='skyblue', edgecolor='black', zorder=3)
        ax.axvline(0, color='red', linestyle='--', linewidth=1, zorder=4)

        ax.set_xlabel(f'Voltage Deviation from Typical ({baseline_v:.4f} V)')
        ax.set_ylabel('Component')
        ax.set_title(f'Tornado Chart: Sensitivity of Node "{target}" Voltage', fontsize=14, fontweight='bold')
        ax.grid(axis='x', linestyle=':', alpha=0.7, zorder=0)
        ax.invert_yaxis() # これにより、最大の変動幅を持つ要素がグラフの上部に表示されます
        fig.tight_layout()
        plt.show()

    def view_circuit(self):
        file_io_utils.open_preset_image(self.preset_var.get()) # file_io_utilsモジュール内の関数を呼び出す

if __name__ == "__main__":
    app = PyMNAProApp(); app.mainloop()
