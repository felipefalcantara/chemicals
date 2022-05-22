# -*- coding: utf-8 -*-
"""Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2022, Caleb Bell <Caleb.Andrew.Bell@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from thermo import *
from chemicals import *
from chemicals.identifiers import pubchem_db
import pandas as pd
import numpy as np

try:
    Chemical('asdfsdaf')
except:
    pass

props = ['MW', 'Tt', 'Tm', 'Tb', 'Tc', 'Pt', 'Pc', 'Vc',
         'Zc','omega', 'Tflash', 'Tautoignition', 'LFL', 'UFL',
                     'Hfs', 'Hfl', 'Hfg', 'S0s', 'S0l', 'S0g',
                     'RI', 'Hfus', 
                     'Dipole', 'logP', 'RG', 'RON', 'MON', 'IGNITION_DELAY']

funcs = [MW, Tt, Tm, Tb, Tc, Pt, Pc, Vc,
         Zc,omega, T_flash, T_autoignition, LFL, UFL,
                     Hfs, Hfl, Hfg, S0s, S0l, S0g,
                     RI, Hfus, 
                     dipole_moment, logP, RG, RON, MON, ignition_delay]
props = [f.__name__ for f in funcs]
CASs = []
prop_array = [[] for _ in range(len(props))]

objs = list(pubchem_db.CAS_index.values())
stuff = []
hits = 0
for v in objs:
    CAS = v.CASs
    CASs.append(CAS)
    for i, p in enumerate(props):
        if p == 'MW':
            lookedup_constant = v.MW
        else:
            lookedup_constant = funcs[i](CASRN=CAS)
        if p == 'RI':
            lookedup_constant = lookedup_constant[0]
        prop_array[i].append(lookedup_constant)
        
        
        
prop_array_T = np.array(prop_array).T
CASs_ints = [CAS_to_int(i) for i in CASs]
df = pd.DataFrame(prop_array_T, columns=props, index=CASs_ints)
df = df.fillna(value=np.nan).astype(np.float32) 
# df.sort_values(by=['logP'], inplace=True)
df.sort_index(inplace=True)

from sqlalchemy import create_engine
engine = create_engine('sqlite:///../chemicals/Misc/default.sqlite', echo=False)
df.to_sql('constants', con=engine)