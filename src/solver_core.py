# Copyright (c) 2026 Zyutama
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

"""
solver_core.py: MNA engine for automotive circuit analysis.
"""
"""
solver_core.py
MNA (Modified Nodal Analysis) engine and SPICE-style unit parsing.
"""
import numpy as np
import re

# --- 1. 単位変換エンジン ---
UNIT_DICT = {
    'g': 1e9, 'G': 1e9, 'meg': 1e6, 'Meg': 1e6, 'MEG': 1e6,
    'k': 1e3, 'K': 1e3, 'm': 1e-3, 'u': 1e-6, 'U': 1e-6,
    'n': 1e-9, 'N': 1e-9, 'p': 1e-12, 'P': 1e-12,
}

def parse_value(val_str):
    if not val_str or str(val_str).strip() in ['-', '', 'none', '0']:
        return 0.0
    val_str = str(val_str).strip()
    match = re.match(r"([+-]?\d*\.?\d+)([a-zA-Z]+)?", val_str)
    if not match: return 0.0
    num = float(match.group(1))
    unit = match.group(2)
    if unit and unit in UNIT_DICT:
        num *= UNIT_DICT[unit]
    return num

# --- 2. 修正節点解析 (MNA) エンジン ---
class MNASolver:
    def __init__(self, netlist):
        self.netlist = netlist
        self.nodes = set()
        for row in netlist:
            if len(row) < 4: continue
            self.nodes.add(str(row[2]))
            self.nodes.add(str(row[3]))
            # For Voltage Controlled Voltage Source (E) and Current Controlled Current Source (F)
            # need to add controlling nodes to node map, though 'F' refers to a V-source name.
            if row[0].upper() == 'E' and len(row) >= 6:
                self.nodes.add(str(row[4])) # Controlling positive node for E source
                self.nodes.add(str(row[5])) # Controlling negative node for E source
            # F type (CCCS) format: F Name N+ N- VCTRL GAIN
            # VCTRL is a voltage source name, not a node itself, so no need to add row[4] as node

        self.nodes.discard('0')
        self.node_map = {name: i for i, name in enumerate(sorted(list(self.nodes)))}
        self.num_n = len(self.node_map)
        # Include 'V' and 'E' type sources for MNA extra variables (their currents)
        # 'F' type sources need to reference currents of existing 'V' or 'E' sources.
        self.v_sources = [r for r in netlist if r[0].upper() in ['V', 'E']] # 'F' type removed from here
        self.num_v = len(self.v_sources)
        self.v_map = {r[1]: i for i, r in enumerate(self.v_sources)}
        self.dim = self.num_n + self.num_v

    def solve(self, params):
        A = np.zeros((self.dim, self.dim))
        Z = np.zeros(self.dim)
        for row in self.netlist:
            rtype, name = row[0].upper(), row[1]
            # The `val` from params will be used for component value or gain.
            # For resistors, current sources, voltage sources, and E-sources, it's directly used.
            # For F-sources, `val` will be the gain.
            val = params.get(name, 0.0)
            n_pos, n_neg = self.node_map.get(str(row[2]), -1), self.node_map.get(str(row[3]), -1)

            if rtype == 'R':
                g = 1.0 / val if val != 0 else 1e12
                if n_pos != -1: A[n_pos, n_pos] += g
                if n_neg != -1: A[n_neg, n_neg] += g
                if n_pos != -1 and n_neg != -1: A[n_pos, n_neg] -= g; A[n_neg, n_pos] -= g
            elif rtype == 'I':
                # Current source flowing from n_neg to n_pos
                if n_pos != -1: Z[n_pos] -= val
                if n_neg != -1: Z[n_neg] += val
            elif rtype == 'V':
                # Voltage source from n_pos to n_neg
                v_idx = self.num_n + self.v_map[name]
                if n_pos != -1: A[n_pos, v_idx] += 1; A[v_idx, n_pos] += 1
                if n_neg != -1: A[n_neg, v_idx] -= 1; A[v_idx, n_neg] -= 1
                Z[v_idx] = val
            elif rtype == 'E':
                # Voltage Controlled Voltage Source (VCVS)
                # E Name N+ N- NI+ NI- GAIN
                v_idx = self.num_n + self.v_map[name]
                ni_pos, ni_neg = self.node_map.get(str(row[4]), -1), self.node_map.get(str(row[5]), -1)
                
                if n_pos != -1: A[n_pos, v_idx] += 1; A[v_idx, n_pos] += 1
                if n_neg != -1: A[n_neg, v_idx] -= 1; A[v_idx, n_neg] -= 1
                
                # Equation for VCVS: V(N+,N-) - GAIN * V(NI+,NI-) = 0
                # -> V_v_idx - GAIN * (V_ni_pos - V_ni_neg) = 0
                # In MNA, this is implemented by modifying the row corresponding to V_v_idx
                if ni_pos != -1: A[v_idx, ni_pos] -= val # -= GAIN * V(NI+)
                if ni_neg != -1: A[v_idx, ni_neg] += val # += GAIN * V(NI-)
            elif rtype == 'F':
                # Current Controlled Current Source (CCCS)
                # F Name N+ N- VCTRL GAIN
                # Current of GAIN * I(VCTRL) flows from N+ to N-
                vctrl_name = row[4] # Name of the controlling voltage source
                gain = val # GAIN is the component's value for F type

                if vctrl_name not in self.v_map: # Check if controlling V source is defined
                    raise ValueError(f"Controlling voltage source '{vctrl_name}' for CCCS '{name}' not found.")

                # Get the index corresponding to the current of the controlling voltage source I(VCTRL)
                vctrl_idx = self.num_n + self.v_map[vctrl_name]

                # Add gain to the MNA matrix for the current flowing from N+ to N-
                if n_pos != -1: A[n_pos, vctrl_idx] += gain
                if n_neg != -1: A[n_neg, vctrl_idx] -= gain

        try:
            # Debugging: Print A and Z before solving
            print("--- MNA Matrix A ---")
            print(A)
            print("--- MNA Vector Z ---")
            print(Z)
            print(f"Node Map: {self.node_map}")
            print(f"Voltage Source Map: {self.v_map}")

            res = np.linalg.solve(A, Z)
            volts = {n: res[self.node_map[n]] for n in self.node_map}
            volts['0'] = 0.0
            return volts
        except Exception as e:
            print(f"Error solving MNA: {e}") # For debugging - RE-ENABLED THIS LINE
            return {n: 0.0 for n in self.node_map} | {'0': 0.0}


