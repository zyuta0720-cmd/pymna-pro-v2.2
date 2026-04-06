# Copyright (c) 2026 Zyutama
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

"""
solver_core.py: MNA engine for automotive circuit analysis.
"""
"""
pymna_config.py
Central configuration for UI texts and preset circuit data.
"""

TEXTS = {
    "jp": {
        "guide_title": "📌 入力ガイド",
        "analysis_grp": "ワーストケース解析", "mc_grp": "統計解析 (モンテカルロ)",
        "run_btn": "▶  Run", "mc_btn": "🎲  Monte Carlo", "tornado_btn": "🌪️  Tornado", "presets_btn": "📋  Presets",
        "preset_grp": "プリセット回路", "view_btn": "🔍 回路図を表示", "load_btn": "ロード", "mc_seed": "シード:",
        "dist_lbl": "分布:", "dist_unif": "一様", "dist_gauss": "正規",
        "ambient_temp_lbl": "周囲温度 [Ta]:", "power_analysis_conditions": "電力解析設定",
        "res_header": "--- Node Voltages ---\nNode\tTyp[V]\tMin[V]\tMax[V]\n",
        "power_header": "\n--- Resistor Power Dissipation (with Derating) ---\nResistor\tTyp\tMax\tRated\tP_limit\tLoad[%]\tStatus\n",
        "mc_res_header": "\n--- Monte Carlo Statistics ---\nNode\tMean[V]\tStdDev\t-3sigma\t+3sigma\n",
        "presets": {"div": "R-2Rラダー", "super": "重ね合わせ", "inv": "反転増幅", "noninv": "非反転増幅", "hsd": "HSD電流モニタ"},
        "save_before_new": "データをCSV保存してから初期状態にしますか？",
        "csv_btn": "CSVエクスポート",
        "help_btn": "❓ ヘルプ",
        "toggle_lang": "English Interface",
        "layout_menu_lbl": "レイアウト",
        "layout_horizontal_lbl": "水平",
        "layout_vertical_lbl": "垂直",
        "layout_horizontal_jp_suffix": " (横)",
        "layout_vertical_jp_suffix": " (縦)",
        "iter_check": "反復収束法を有効にする",
        "lt_check": "LTspiceネットリストを保存"
    },
    "en": {
        "guide_title": "📌 Input Guide",
        "guide_text": "[Basic Format]\nComponentType Name Node+ Node- Value [Tolerance/Range]\n\n* Resistors (R), Voltage Sources (V), Current Sources (I):\n  R R1 1 0 1k 1  (1kΩ ±1%)\n  R R2 1 0 1k 0.9k/1.1k  (1kΩ, Min 0.9kΩ, Max 1.1kΩ - Asymmetric margins allowed)\n  V V1 1 0 12V 5  (12V ±5%)\n  I I1 1 0 1mA  (1mA, fixed)\n\n* Voltage Controlled Voltage Source (E - Op-Amp Model):\n  E Name OutputNode+ OutputNode- ControlNode+ ControlNode- Gain\n  Ex: E OP1 3 0 1 2 100k  (Output V(3)-V(0) = 100k * (V(1)-V(2)))\n\n* Current Controlled Current Source (F):\n  F Name OutputNode+ OutputNode- ControllingVoltageSourceName Gain [Tolerance/Range]\n  Ex: F F1 3 0 V_sense 2 1.8/2.2  (Output Current I(3->0) = Gain * I(V_sense))\n  (V_sense must be an existing Voltage Source in the netlist)\n\n[Units Supported]\nk (kilo), meg (mega), m (milli), u (micro), n (nano), p (pico)\n\n[Power Analysis Tags (Resistors Only)]\nAdd these as comments to resistor lines:\n; @P=0.1W @T_S=70 @T_M=155\n  @P: Rated Power [W]\n  @T_S: Derating Start Temperature [°C] (e.g., 70 for standard, 125 for automotive)\n  @T_M: Maximum Operating Temperature [°C] (e.g., 155)\n\n[Copy & Paste from Excel available]",
        "analysis_grp": "Worst Case Analysis", "mc_grp": "Monte Carlo Analysis",
        "run_btn": "▶  Run", "mc_btn": "🎲  Monte Carlo", "tornado_btn": "🌪️  Tornado", "presets_btn": "📋  Presets",
        "preset_grp": "Preset Circuits", "view_btn": "🔍 View Diagram", "load_btn": "Load", "mc_seed": "Seed:",
        "dist_lbl": "Distribution:", "dist_unif": "Uniform", "dist_gauss": "Gaussian",
        "ambient_temp_lbl": "Ta [°C]:", "power_analysis_conditions": "Power Analysis Conditions",
        "res_header": "--- Node Voltages ---\nNode\tTyp[V]\tMin[V]\tMax[V]\n",
        "power_header": "\n--- Resistor Power Dissipation (with Derating) ---\nResistor\tTyp\tMax\tRated\tP_limit\tLoad[%]\tStatus\n",
        "mc_res_header": "\n--- Monte Carlo Statistics ---\nNode\tMean[V]\tStdDev\t-3sigma\t+3sigma\n",
        "presets": {"div": "R-2R Ladder", "super": "Superposition", "inv": "Inverting Amp", "noninv": "Non-Inverting Amp", "hsd": "High-Side Monitor"},
        "save_before_new": "Save current netlist to CSV before creating new?",
        "csv_btn": "Export CSV",
        "help_btn": "❓ Help",
        "toggle_lang": "日本語インターフェース", # This label is for the command to switch to Japanese
        "layout_menu_lbl": "Layout",
        "layout_horizontal_lbl": "Horizontal",
        "layout_vertical_lbl": "Vertical",
        "layout_horizontal_jp_suffix": "", # No suffix for English
        "layout_vertical_jp_suffix": "",   # No suffix for English
        "iter_check": "Enable Iterative Solver",
        "lt_check": "Save LTspice Netlist"
    }
}

# URL definitions for preset circuit diagrams
PRESET_URLS = {
    "div": "https://raw.githubusercontent.com/zyuta0720-cmd/pymna-pro-v2/main/images/preset_r2r.png",
    "super": "https://raw.githubusercontent.com/zyuta0720-cmd/pymna-pro-v2/main/images/preset_superposition.png",
    "inv": "https://raw.githubusercontent.com/zyuta0720-cmd/pymna-pro-v2/main/images/preset_InvAmp.png",
    "noninv": "https://raw.githubusercontent.com/zyuta0720-cmd/pymna-pro-v2/main/images/preset_NonInvAmp.png",
    "hsd": "https://raw.githubusercontent.com/zyuta0720-cmd/pymna-pro-v2/main/images/preset_HSD_C_moni.png"
}

PRESET_DATA_RAW = {
    "div": {"netlist": "V\tVin\t1\t0\t10\nR\tR1\t1\t2\t1k\t1\nR\tR2\t1\t0\t2k\t1\nR\tR3\t2\t3\t1k\t1\nR\tR4\t2\t0\t2k\t1\nR\tR5\t3\t4\t1k\t1\nR\tR6\t3\t0\t2k\t1\nR\tR7\t4\t5\t1k\t1\nR\tR8\t4\t0\t2k\t1\nR\tR9\t5\t0\t1k\t1"},
    "super": {"netlist": "V\tV1\t1\t0\t10\nI\tI1\t2\t0\t1m\nR\tR1\t1\t3\t1k\t5\nR\tR2\t2\t3\t2k\t5\nR\tR3\t3\t0\t2k\t5"},
    "inv": {"netlist": "V\tVin\t1\t0\t1\nR\tRin\t1\t2\t10k\t1\nR\tRf\t2\t3\t100k\t1\nE\tOP1\t3\t0\t0\t2\t100k"},
    "noninv": {"netlist": "V\tVin\t1\t0\t1\nR\tR1\t3\t2\t90k\t1\nR\tR2\t2\t0\t10k\t1\nE\tOP1\t3\t0\t1\t2\t100k"},
    "hsd": {"netlist": "V\tV1\t1\t0\t12\nV\tV_sense\t1\t2\t0\nR\tR_load\t2\t0\t12\t10\nF\tF_mirror\t0\t3\tV_sense\t0.001\nR\tR_monitor\t3\t0\t1k"}
}