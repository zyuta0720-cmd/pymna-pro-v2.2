# PyMNA Pro v2.2

**「部品のバラツキによる『回路のワースト状態』を、数学とグラフで未然に防ぐ設計支援ツール」**
 
**Design Support Tool: Using Mathematics and Graphs to Prevent "Worst-Case Circuit Failures" Caused by Component Variations.**

【このプログラムができること / What This Program Does】
  
- 一瞬で計算 / Instant Calculation
  - ネットリスト（回路の接続図）を読み込み、各部の電圧を正確に計算します。
  - Reads your netlist and accurately calculates voltages across the entire circuit in an instant.
- 最悪を探す / Finding the "Worst-Case"
  - 部品の誤差が重なったときの「一番危ない状態」を自動で見つけ出します。
  - Automatically identifies the "most dangerous state" that occurs when multiple component tolerances overlap.
- 原因が見える / Visualizing the Cause
  - どの部品が一番悪影響を与えているか、ランキング（グラフ）で表示します。
  - Displays a ranked graph (Tornado Chart) showing which specific components have the greatest negative impact on your design.

-----

## 概要 / Overview

本プロジェクトは、電子回路の信頼性設計において重要な\*\*最悪値解析（WCA: Worst Case Analysis）\*\*を効率化するためのPythonベースのシミュレータです。
従来の表計算ソフト（Excel等）のソルバー機能で課題となっていた収束精度や計算の不透明さを排除し、回路方程式から論理的・統計的に最悪値を算出することを目的に開発されました。

This project is a Python-based circuit simulator designed to streamline **Worst Case Analysis (WCA)**, a critical process in high-reliability electronics design. It addresses convergence and transparency issues common in spreadsheet-based solvers, ensuring precise theoretical worst-case values derived directly from circuit equations.

## 特徴 / Features

  - **高精度MNAエンジン / High Precision MNA Engine**
      - 修正節点解析（Modified Nodal Analysis）を搭載。R, V, I に加え、依存電源（E, Fソース）に対応。
      - Features a robust MNA solver supporting R, V, I, and dependent sources (E, F).
  - **自動最悪値探索 / Automated WCA**
      - 部品公差（Tolerance）に基づき、ノード電圧を最大・最小にする組み合わせを反復収束アルゴリズムで自動探索。
      - Automatically identifies component combinations that maximize/minimize node voltages using an iterative refinement algorithm.
  - **統計解析 / Monte Carlo Simulation**
      - 部品定数のバラツキを考慮したモンテカルロシミュレーション（一様分布/正規分布）に対応。
      - Supports statistical analysis considering component variations with Uniform or Gaussian distributions.
  - **感度分析の可視化 / Sensitivity Visualization**
      - トルネードチャートを生成し、回路特性に支配的な影響を与える部品を一目で把握可能。
      - Generates Tornado Charts to visualize which components most significantly impact circuit performance.
  - **実用的な連携 / Practical Integration**
      - ネットリスト形式を採用。LTspice等へのエクスポート（.asc / .cir）もサポート。
      - Uses standard netlist formats and supports exporting to LTspice-compatible files (.asc / .cir).
  - **モダンなUI / Modern GUI**
      - ダークモードを採用した、エンジニア向けの直感的でスタイリッシュなインターフェース。
      - Features an intuitive, dark-themed interface tailored for professional engineers.

## 主な機能 / Key Functions

1.  **WCA解析 / WCA Analysis**:
    各ノードの Typ / Min / Max 電圧と、最悪値を与える部品の組み合わせ（Assignment）を算出。
    Calculates Typ/Min/Max node voltages and identifies the specific component assignments for worst-case scenarios.
2.  **モンテカルロ解析 / Monte Carlo**:
    指定した試行回数に基づき、統計的なバラツキ（$\pm 3 \sigma$ 等）を算出。
    Calculates statistical dispersion (e.g., $\pm 3 \sigma$) based on a defined number of iterations.
3.  **トルネードチャート / Tornado Chart**:
    特定ノードに対する各部品の感度をグラフ化。
    Graphs the sensitivity of specific nodes relative to each component.
4.  **電力解析 / Power Analysis**:
    周囲温度（Ta）に応じた軽減定格（Derating）を考慮し、抵抗器の負荷率を算出。
    Calculates resistor load factors considering power derating relative to ambient temperature (Ta).
5.  **プリセット機能 / Presets**:
    R-2Rラダーや増幅回路など、典型的な回路を即座にシミュレーション可能。
    Includes built-in templates for common circuits like R-2R ladders and amplifiers.

## セットアップ / Setup

### 依存ライブラリ / Prerequisites

```bash
pip install numpy matplotlib
```

### 実行方法 / How to Run

リポジトリをクローンまたはダウンロードし、`src` ディレクトリに移動してメインスクリプトを実行してください。

```bash
python src/pymna_main.py
```

## ディレクトリ構成 / Directory Structure

```text
PyMNA-Pro/
├── README.md           # This file / 本ファイル
├── LICENSE             # MIT License / MITライセンス
├── requirements.txt    # Library list / 依存ライブラリリスト
└── src/                # Source code / ソースコード
    ├── pymna_main.py       # Main Entry Point / 起動用スクリプト
    ├── solver_core.py      # MNA Solver Engine / 計算エンジン
    ├── analysis_suite.py   # Analysis Logic / 解析ロジック
    ├── gui_components.py   # View & UI Layout / UIレイアウト
    ├── file_io_utils.py    # File I/O (CSV/LTspice) / 入出力ユーティリティ
    └── pymna_config.py     # Config & Presets / 設定・プリセット
```

## ライセンス / License

本プロジェクトは **MITライセンス** の下で公開されています。詳細は [LICENSE](https://www.google.com/search?q=./LICENSE) ファイルをご確認ください。
This project is licensed under the **MIT License**. See the [LICENSE](https://www.google.com/search?q=./LICENSE) file for details.

-----

**Developer:** Zyutama  
**Field:** Automotive Hardware Engineering (ECU Design / WCA)

-----
