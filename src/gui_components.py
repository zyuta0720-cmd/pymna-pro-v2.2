# Copyright (c) 2026 Zyutama
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

"""
solver_core.py: MNA engine for automotive circuit analysis.
""""""
gui_components.py
Handles the View layer: UI creation, layouts, and visual updates.
"""
import tkinter as tk
from tkinter import ttk
import pymna_config
import file_io_utils
import re

class MainView:
    def __init__(self, app):
        self.app = app
        self.dpi_scale = app.dpi_scale

    def setup_ui(self):
        """メインウィンドウの基本構築"""
        app = self.app
        app.title(f"PyMNA Pro - Ver {file_io_utils.VERSION} ({file_io_utils.LAST_UPDATE})")
        app.geometry(f"{int(1300*self.dpi_scale)}x{int(850*self.dpi_scale)}")
        app.configure(bg="#23272e")
        
        # --- Ribbon UI ---
        app.ribbon = tk.Frame(app, bg="#2d3139", height=int(120*self.dpi_scale), bd=1, relief="flat")
        app.ribbon.grid(row=0, column=0, columnspan=3, sticky="ew")

        # Analysis Group
        app.grp_analysis = tk.LabelFrame(app.ribbon, text=pymna_config.TEXTS[app.lang]["analysis_grp"], bg="#2d3139", fg="#abb2bf", font=("Segoe UI", int(9*self.dpi_scale)))
        app.grp_analysis.pack(side="left", padx=10, pady=5, fill="y")
        
        app.btn_run = tk.Button(app.grp_analysis, text=pymna_config.TEXTS[app.lang]["run_btn"], command=app.execute, font=("Segoe UI", int(11*self.dpi_scale), "bold"), bg="#00bfff", fg="#23272e", relief="flat", width=10)
        app.btn_run.pack(side="left", padx=10, pady=5)
        
        app.btn_tornado = tk.Button(app.grp_analysis, text=pymna_config.TEXTS[app.lang]["tornado_btn"], command=app.generate_tornado_chart, font=("Segoe UI", int(10*self.dpi_scale), "bold"), bg="#444", fg="#abb2bf", relief="flat", state="disabled", width=12)
        app.btn_tornado.pack(side="left", padx=10, pady=5)
        
        # Presets Group
        app.grp_presets = tk.LabelFrame(app.ribbon, text=pymna_config.TEXTS[app.lang]["preset_grp"], bg="#2d3139", fg="#abb2bf", font=("Segoe UI", int(9*self.dpi_scale)))
        app.grp_presets.pack(side="left", padx=5, pady=5, fill="y")
        
        # Monte Carlo Group
        app.grp_mc = tk.LabelFrame(app.ribbon, text=pymna_config.TEXTS[app.lang]["mc_grp"], bg="#2d3139", fg="#abb2bf", font=("Segoe UI", int(9*self.dpi_scale)))
        app.grp_mc.pack(side="left", padx=10, pady=5, fill="y")
        
        app.btn_mc = tk.Button(app.grp_mc, text=pymna_config.TEXTS[app.lang]["mc_btn"], command=app.run_monte_carlo, font=("Segoe UI", int(11*self.dpi_scale), "bold"), bg="#ff9800", fg="#23272e", relief="flat", width=15)
        app.btn_mc.pack(side="left", padx=10, pady=5)
        
        app.mc_settings = tk.Frame(app.grp_mc, bg="#2d3139")
        app.mc_settings.pack(side="left", padx=5)
        
        row1 = tk.Frame(app.mc_settings, bg="#2d3139"); row1.pack(fill="x")
        tk.Label(row1, text="Runs:", font=("Segoe UI", int(8*self.dpi_scale)), fg="#abb2bf", bg="#2d3139").pack(side="left")
        tk.Entry(row1, textvariable=app.mc_runs_var, width=5, font=("Segoe UI", int(9*self.dpi_scale))).pack(side="left", padx=2)
        
        app.lbl_seed = tk.Label(row1, text=pymna_config.TEXTS[app.lang]["mc_seed"], font=("Segoe UI", int(8*self.dpi_scale)), fg="#abb2bf", bg="#2d3139")
        app.lbl_seed.pack(side="left", padx=(5,0))
        tk.Entry(row1, textvariable=app.mc_seed_var, width=5, font=("Segoe UI", int(9*self.dpi_scale))).pack(side="left", padx=2)
        
        row2 = tk.Frame(app.mc_settings, bg="#2d3139"); row2.pack(fill="x", pady=2)
        app.rb_unif = tk.Radiobutton(row2, text=pymna_config.TEXTS[app.lang]["dist_unif"], variable=app.dist_var, value="uniform", font=("Segoe UI", int(8*self.dpi_scale)), fg="#e0e0e0", bg="#2d3139", selectcolor="#2d3139")
        app.rb_unif.pack(side="left")
        app.rb_gauss = tk.Radiobutton(row2, text=pymna_config.TEXTS[app.lang]["dist_gauss"], variable=app.dist_var, value="gaussian", font=("Segoe UI", int(8*self.dpi_scale)), fg="#e0e0e0", bg="#2d3139", selectcolor="#2d3139")
        app.rb_gauss.pack(side="left")

        # --- Editor Area ---
        app.main_container = tk.Frame(app, bg="#23272e")
        app.main_container.grid(row=1, column=0, columnspan=3, sticky="nsew")
        app.grid_rowconfigure(1, weight=1); app.grid_columnconfigure(0, weight=1)

        app.input_frame = tk.Frame(app.main_container, bg="#23272e")
        app.input_text = tk.Text(app.input_frame, font=("Consolas", int(13*self.dpi_scale)), bg="#181c22", fg="#e0e0e0", insertbackground="#00bfff", wrap="none", undo=True)
        app.in_vsb = tk.Scrollbar(app.input_frame, orient="vertical", command=app.input_text.yview)
        app.in_hsb = tk.Scrollbar(app.input_frame, orient="horizontal", command=app.input_text.xview)
        app.input_text.configure(yscrollcommand=app.in_vsb.set, xscrollcommand=app.in_hsb.set)
        app.input_text.grid(row=0, column=0, sticky="nsew")
        app.in_vsb.grid(row=0, column=1, sticky="ns")
        app.in_hsb.grid(row=1, column=0, sticky="ew")
        app.input_frame.grid_rowconfigure(0, weight=1); app.input_frame.grid_columnconfigure(0, weight=1)

        app.output_frame = tk.Frame(app.main_container, bg="#23272e")
        app.output_text = tk.Text(app.output_frame, font=("Consolas", int(13*self.dpi_scale)), bg="#101216", fg="#00ff99", wrap="none")
        app.out_vsb = tk.Scrollbar(app.output_frame, orient="vertical", command=app.output_text.yview)
        app.out_hsb = tk.Scrollbar(app.output_frame, orient="horizontal", command=app.output_text.xview)
        app.output_text.configure(yscrollcommand=app.out_vsb.set, xscrollcommand=app.out_hsb.set)
        app.output_text.grid(row=0, column=0, sticky="nsew")
        app.out_vsb.grid(row=0, column=1, sticky="ns")
        app.out_hsb.grid(row=1, column=0, sticky="ew")
        app.output_frame.grid_rowconfigure(0, weight=1); app.output_frame.grid_columnconfigure(0, weight=1)

        app.help_panel = tk.Frame(app.main_container, bg="#3e4451", width=0, bd=1, relief="sunken")
        app.help_txt = tk.Text(app.help_panel, font=("Consolas", int(10*self.dpi_scale)), bg="#3e4451", fg="#e0e0e0", relief="flat", padx=10, pady=10, wrap="word")
        app.help_txt.pack(fill="both", expand=True)

        # --- Status Bar ---
        app.status_bar = tk.Frame(app, bg="#1c1e22", height=int(25*self.dpi_scale))
        app.status_bar.grid(row=2, column=0, columnspan=3, sticky="ew")
        app.lbl_status = tk.Label(app.status_bar, text=" Ready", font=("Segoe UI", int(9*self.dpi_scale)), fg="#abb2bf", bg="#1c1e22", anchor="w")
        app.lbl_status.pack(side="left", fill="x")

        self.setup_menus()
        self.update_layout()

    def setup_menus(self):
        """メニューバーの構築"""
        app = self.app
        app.main_menu = tk.Menu(app)
        app.config(menu=app.main_menu)

        app.file_menu = tk.Menu(app.main_menu, tearoff=0)
        app.main_menu.add_cascade(label="File", menu=app.file_menu)
        app.file_menu.add_command(label="New", command=app.file_new)
        app.file_menu.add_command(label="Open Netlist...", command=app.file_open)
        app.file_menu.add_command(label="Export to CSV", command=app.export_to_csv)
        
        app.tool_menu = tk.Menu(app.main_menu, tearoff=0)
        app.main_menu.add_cascade(label="Tool", menu=app.tool_menu)
        app.tool_menu.add_command(label="Save LTspice Netlist (.cir)", command=app.save_cir_manual)
        app.tool_menu.add_command(label="Save LTspice Schematic (.asc)", command=app.save_asc_manual)

        app.preset_menu = tk.Menu(app.main_menu, tearoff=0)
        app.main_menu.add_cascade(label="Presets", menu=app.preset_menu)

        app.lang_menu = tk.Menu(app.main_menu, tearoff=0)
        app.main_menu.add_cascade(label="Language", menu=app.lang_menu)
        app.lang_menu.add_radiobutton(label="English", variable=app.lang_var, value="en", command=lambda: app.set_language("en"))
        app.lang_menu.add_radiobutton(label="日本語", variable=app.lang_var, value="jp", command=lambda: app.set_language("jp"))

        app.view_menu = tk.Menu(app.main_menu, tearoff=0)
        app.main_menu.add_cascade(label="View", menu=app.view_menu)
        app.layout_menu = tk.Menu(app.view_menu, tearoff=0)
        app.view_menu.add_cascade(label=pymna_config.TEXTS[app.lang]["layout_menu_lbl"], menu=app.layout_menu)
        app.layout_menu.add_radiobutton(label=app._get_layout_label("horizontal"), variable=app.layout_orientation_var, value="horizontal", command=lambda: app.set_layout_orientation("horizontal"))
        app.layout_menu.add_radiobutton(label=app._get_layout_label("vertical"), variable=app.layout_orientation_var, value="vertical", command=lambda: app.set_layout_orientation("vertical"))

        app.settings_menu = tk.Menu(app.main_menu, tearoff=0)
        app.main_menu.add_cascade(label="Settings", menu=app.settings_menu)
        app.settings_menu.add_command(label="All Analysis Settings...", command=app.open_settings_dialog)

        app.help_menu = tk.Menu(app.main_menu, tearoff=0)
        app.main_menu.add_cascade(label="Help", menu=app.help_menu)
        app.help_menu.add_command(label="Input Guide", command=app.toggle_help)

    def update_layout(self):
        """レイアウト切替の再配置ロジック"""
        app = self.app
        app.layout_orientation_var.set("vertical" if app.is_vertical else "horizontal")
        app.input_frame.grid_forget()
        app.output_frame.grid_forget()
        app.help_panel.grid_forget()
        
        for i in range(3):
            app.main_container.grid_columnconfigure(i, weight=0, minsize=0)
            app.main_container.grid_rowconfigure(i, weight=0, minsize=0)

        if app.is_vertical:
            app.main_container.grid_rowconfigure(0, weight=1)
            app.main_container.grid_columnconfigure(0, weight=1)
            app.main_container.grid_columnconfigure(1, weight=1)
            app.input_frame.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
            app.output_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
            if app.help_visible:
                app.help_panel.grid(row=0, column=2, sticky="nsew")
                app.main_container.grid_columnconfigure(2, minsize=int(350*app.dpi_scale))
        else:
            app.main_container.grid_columnconfigure(0, weight=1)
            app.main_container.grid_rowconfigure(0, weight=1)
            app.main_container.grid_rowconfigure(1, weight=1)
            app.input_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
            app.output_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
            if app.help_visible:
                app.help_panel.grid(row=0, column=1, rowspan=2, sticky="nsew")
                app.main_container.grid_columnconfigure(1, minsize=int(350*app.dpi_scale))

    def update_preset_ui(self):
        """言語切替等に連動してプリセットメニュー(Menu)とツールバー(Ribbon)を再構築"""
        app = self.app
        t = pymna_config.TEXTS[app.lang]

        # 1. メニューバーのプリセット項目を更新
        app.preset_menu.delete(0, "end")
        for pk, pv in pymna_config.PRESET_DATA_RAW.items():
            p_name = t["presets"].get(pk, pk)
            app.preset_menu.add_command(label=p_name, command=lambda k=pk: app.load_preset_by_key(k))

        # 2. ツールバー（リボンUI）のウィジェットを再構築
        for widget in app.grp_presets.winfo_children():
            widget.destroy()
        
        display_map = t["presets"]
        display_names = list(display_map.values())
        
        current_id = app.preset_var.get()
        current_name = display_map.get(current_id, display_names[0])
        app.disp_var = tk.StringVar(value=current_name)
        
        def on_change(selected_name):
            for kid, vname in display_map.items():
                if vname == selected_name:
                    app.preset_var.set(kid); break

        # コンパクトなドロップダウンメニュー
        om = tk.OptionMenu(app.grp_presets, app.disp_var, *display_names, command=on_change)
        om.config(bg="#444", fg="white", highlightthickness=0, relief="flat", font=("Segoe UI", int(9*self.dpi_scale)), width=15)
        om["menu"].config(bg="#444", fg="white", font=("Segoe UI", int(9*self.dpi_scale)))
        om.pack(side="top", padx=5, pady=2)
        
        btn_frame = tk.Frame(app.grp_presets, bg="#2d3139")
        btn_frame.pack(side="top", fill="x", padx=5, pady=2)

        # ロードボタン
        btn_load = tk.Button(btn_frame, text=t["load_btn"], command=app.load_preset, font=("Segoe UI", int(9*self.dpi_scale), "bold"), bg="#00bfff", fg="#23272e", relief="flat")
        btn_load.pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        # 回路図参照（View）ボタン
        btn_view = tk.Button(btn_frame, text=t["view_btn"], command=app.view_circuit, font=("Segoe UI", int(8*self.dpi_scale)), bg="#444", fg="white", relief="flat")
        btn_view.pack(side="left", fill="x", expand=True, padx=(2, 0))
