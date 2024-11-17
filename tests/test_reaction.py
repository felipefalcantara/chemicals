"""Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2016, Caleb Bell <Caleb.Andrew.Bell@gmail.com>

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

import pandas as pd
import pytest
from fluids.numerics import assert_close, assert_close1d, assert_close2d, numpy as np

from chemicals.heat_capacity import CRC_standard_data, TRC_gas_data
from chemicals.reaction import (
    Gibbs_formation,
    Hf_basis_converter,
    Hfg,
    Hfg_all_methods,
    Hfg_API_TDB_data,
    Hfg_ATcT_data,
    Hfg_methods,
    Hfg_S0g_YAWS_data,
    Hfl,
    Hfl_ATcT_data,
    Hfl_methods,
    Hfs,
    Hfs_methods,
    S0g,
    S0g_all_methods,
    S0g_methods,
    S0l,
    S0l_methods,
    S0s,
    S0s_methods,
    balance_stoichiometry,
    entropy_formation,
    standard_formation_reaction,
    stoichiometric_matrix,
)


def test_API_TDB_data():
    assert Hfg_API_TDB_data['Hfg'].abs().sum() == 101711260
    assert Hfg_API_TDB_data.shape == (571, 2)


def test_ATcT_l():
    assert Hfl_ATcT_data.shape == (34,5)
    tots_calc = [Hfl_ATcT_data[i].abs().sum() for i in ['Hfl_0K', 'Hfl', 'uncertainty']]
    tots = [2179500.0, 6819443, 19290]
    assert_close1d(tots_calc, tots)


def test_Hfg_ATcT_data():
    assert Hfg_ATcT_data.shape == (595, 5)
    tots_calc = [Hfg_ATcT_data[i].abs().sum() for i in ['Hfg_0K', 'Hfg', 'uncertainty']]
    tots = [300788330, 300592764, 829204]
    assert_close1d(tots_calc, tots)

def test_Hfg_API_TDB_data():
    assert_close(Hfg('7732-18-5', method='API_TDB_G'), -241820.0)

    assert Hfg_methods('7732-18-5') == ['ATCT_G', 'CRC', 'API_TDB_G', 'WEBBOOK', 'TRC', 'JANAF', 'YAWS']

    assert None is Hfg('98-00-1')

    with pytest.raises(Exception):
        Hfg('98-00-0', method='BADMETHOD')

@pytest.mark.slow
def test_Hfg_API_TDB_data_fuzz():
    tot = sum([abs(Hfg(i, method='API_TDB_G')) for i in Hfg_API_TDB_data.index])
    assert_close(tot, 101711260.0)


def test_Hfl():
    Hfs = [Hfl('67-56-1'), Hfl('67-56-1', method='ATCT_L')]
    assert_close1d(Hfs, [-238400.0]*2)

    assert Hfl_methods('67-56-1') == ['ATCT_L', 'CRC', 'WEBBOOK']
    assert None is Hfl('98-00-1')

    tot = sum([abs(Hfl(i)) for i in Hfl_ATcT_data.index])
    assert_close(tot, 6819443.0)

    with pytest.raises(Exception):
        Hfl('98-00-0', method='BADMETHOD')


def test_Hfg():
    # default method ATCT_G
    assert_close(Hfg('7732-18-5'), -241822.0)

    Hfs = [Hfg('67-56-1', method=i) for i in Hfg_all_methods]
    assert_close1d(Hfs, [-200700.0, -190100.0, -201000.0, -205000.0, None, -200900.0, -216200.0])

    assert Hfg_methods('67-56-1') == ['ATCT_G', 'CRC', 'API_TDB_G', 'WEBBOOK', 'TRC', 'YAWS', 'JOBACK']
    assert_close(-211800.0, Hfg('98-00-0'))

    with pytest.raises(Exception):
        Hfg('98-00-0', method='BADMETHOD')

def test_Hfs():
    assert_close(Hfs('101-81-5'), 71500)
    assert_close(Hfs('101-81-5', method='CRC'), 71500)
    assert ['CRC', 'WEBBOOK'] == Hfs_methods('101-81-5')



@pytest.mark.fuzz
@pytest.mark.slow
def test_Hfg_all_values():
    tot1 = sum([abs(Hfg(i, method='TRC')) for i in TRC_gas_data.index[pd.notnull(TRC_gas_data['Hfg'])]])
    assert_close(tot1, 495689880.0)

    tot2 = sum([abs(Hfg(i, method='ATCT_G')) for i in Hfg_ATcT_data.index])
    assert_close(tot2, 300592764.0)

    tot3 = sum([abs(Hfg(i, method='YAWS')) for i in Hfg_S0g_YAWS_data.index[pd.notnull(Hfg_S0g_YAWS_data['Hfg'])]])
    assert_close(tot3, 1544220403.0)

    tot4 = sum([abs(Hfg(i, method='CRC')) for i in CRC_standard_data.index[pd.notnull(CRC_standard_data['Hfg'])]])
    assert_close(tot4, 392946600.0)

def test_S0g():
    S0s = [S0g('7732-18-5', method=i) for i in S0g_all_methods]
    assert_close1d(S0s, [188.8, 188.83842, 188.834, 188.84])

    assert S0g_methods('67-56-1') == ['CRC', 'YAWS']

    assert_close(239.9, S0g('67-56-1'))

    with pytest.raises(Exception):
        S0g('98-00-0', method='BADMETHOD')

@pytest.mark.fuzz
@pytest.mark.slow
def test_S0g_all_values():
    tot3 = sum([abs(S0g(i, method='YAWS')) for i in Hfg_S0g_YAWS_data.index[pd.notnull(Hfg_S0g_YAWS_data['S0g'])]])
    assert_close(tot3, 2690113.4130000058)

    tot4 = sum([abs(S0g(i, method='CRC')) for i in CRC_standard_data.index[pd.notnull(CRC_standard_data['S0g'])]])
    assert_close(tot4, 141558.30000000008)


def test_S0s():
    assert_close(S0s('7439-93-2'), 29.1) # Lithium
    assert_close(S0s('7439-93-2', method='CRC'), 29.1)

    methods = S0s_methods('7439-93-2')
    assert methods == ['CRC', 'WEBBOOK']

def test_S0l():
    assert_close(S0l('7439-97-6'), 75.9) # Lithium
    assert_close(S0l('7439-97-6', method='CRC'), 75.9)

    methods = S0l_methods('7439-97-6')
    assert methods == ['CRC', 'WEBBOOK']

def test_Gibbs_formation():
    Gf =  Gibbs_formation(-285830.0, 69.91,  [0.0, 0.0], [130.571, 205.147], [1.0, .5])
    assert_close(Gf, -237161.633825)

    Gf = Gibbs_formation(-241818, 188.825,  [0.0, 0], [130.571, 205.147], [1.0, .5])
    assert_close(Gf, -228604.141075)

    Gf = Gibbs_formation(-648980, 297.713, [0.0, 0.0, 0.0], [5.74, 152.206, 202.789], [1, .5, 1.5])
    assert_close(Gf, -622649.329975)


def test_Hf_basis_converter():
    assert_close(Hf_basis_converter(44018.0, Hf_liq=-285830.0), -241812)

    assert_close(Hf_basis_converter(44018, Hf_gas=-241812.0), -285830)

    with pytest.raises(ValueError):
        Hf_basis_converter(44018, Hf_liq=None)
    with pytest.raises(ValueError):
        Hf_basis_converter(2000, Hf_gas=None, Hf_liq=None)
    with pytest.raises(ValueError):
        Hf_basis_converter(Hvapm=-1, Hf_liq=1)
    with pytest.raises(ValueError):
        Hf_basis_converter(Hvapm=None, Hf_liq=1)

def test_entropy_formation():
    Sf = entropy_formation(Hf=-74520.0, Gf=-50490.0)
    assert_close(Sf, -80.59701492537314)

    Sf = entropy_formation(Hf=-241818, Gf=-228572)
    assert_close(Sf, -44.427301693778304)


def check_reaction_balance(matrix, products_calc, atol=1e-13):
    """Check that coefficients satisfy the stoichiometric matrix equation within tolerance."""
    result = np.array(matrix) @ np.array(products_calc)
    assert_close1d(result, [0.0]*len(result), atol=atol)

    
def test_balance_stoichiometry():
    test_cases = [
    [[{'Hg': 1, 'O': 1}, {'Hg': 1}, {'O': 2}], [True, False, False], [2.0, 2.0, 1.0]],
    [[{'Cl': 2}, {'C': 3, 'H': 6}, {'C': 3, 'Cl': 1, 'H': 5}, {'Cl': 1, 'H': 1}],
      [True, True, False, False, False],
      [1, 1, 1, 1]],
    [[{'Al': 1}, {'H': 1, 'N': 1, 'O': 3}, {'Al': 1, 'N': 3, 'O': 9}, {'N': 1, 'O': 1}, {'H': 2, 'O': 1}],
      [True, True, False, False, False],
      [1.0, 4.0, 1.0, 1.0, 2.0]],
    [[{'Fe': 1}, {'O': 2}, {'Fe':2, 'O': 3}], [True, True, False], [4.0, 3.0, 2.0]],
    [[{'N': 1, 'H': 3}, {'O': 2}, {'N': 1, 'O': 1}, {'H': 2, 'O': 1}], [True, True, False, False], [4.0, 5.0, 4.0, 6.0]],
    [[{'O': 2}, {'H': 2, 'O': 1}, {'C': 1, 'O': 2}, {'C': 6, 'H': 14}], [True, False, False, True], [19.0, 14.0, 12.0, 2.0]],

    # Examples from
    #Smith, William R., and Ronald W. Missen. “Using Mathematica and Maple To Obtain Chemical Equations.” Journal of Chemical Education 74, no. 11 (November 1, 1997): 1369. https://doi.org/10.1021/ed074p1369.

    # Complex redox system test case
    # [Cr(N2H4CO)6]4[Cr(CN)6]3 + KMnO4 + H2SO4 → K2Cr2O7 + MnSO4 + CO2 + KNO3 + K2SO4 + H2O
    [[
        # B = [Cr(N2H4CO)6]4[Cr(CN)6]3
        {'Cr': 7, 'N': 66, 'H': 96, 'C': 42, 'O': 24},
        # KMnO4
        {'K': 1, 'Mn': 1, 'O': 4},
        # H2SO4
        {'H': 2, 'S': 1, 'O': 4},
        # K2Cr2O7
        {'K': 2, 'Cr': 2, 'O': 7},
        # MnSO4
        {'Mn': 1, 'S': 1, 'O': 4},
        # CO2
        {'C': 1, 'O': 2},
        # KNO3
        {'K': 1, 'N': 1, 'O': 3},
        # K2SO4
        {'K': 2, 'S': 1, 'O': 4},
        # H2O
        {'H': 2, 'O': 1}
    ],
    [True, True, True, False, False, False, False, False, False],
    [10.0, 1176.0, 1399.0, 35.0, 1176.0, 420.0, 660.0, 223.0, 1879.0]],  # Expected coefficients

    # Reaction 1: H+ + OH- = H2O
    [
        [
            {'H': 1, 'p': 1},          # H+
            {'H': 1, 'O': 1, 'p': -1}, # OH-
            {'H': 2, 'O': 1}           # H2O
        ],
        [True, True, False],
        [1.0, 1.0, 1.0]
    ],

    # Reaction 2: OH- + NO+ = NO2- + H+
    [
        [
            {'H': 1, 'O': 1, 'p': -1}, # OH-
            {'N': 1, 'O': 1, 'p': 1},  # NO+
            {'N': 1, 'O': 2, 'p': -1}, # NO2-
            {'H': 1, 'p': 1}           # H+
        ],
        [True, True, False, False],
        [1.0, 1.0, 1.0, 1.0]
    ],

    # Reaction 3: 2OH- + 2NO+ = N2O3 + H+
    [
        [
            {'H': 1, 'O': 1, 'p': -1}, # OH-
            {'N': 1, 'O': 1, 'p': 1},  # NO+
            {'N': 2, 'O': 3},          # N2O3
            {'H': 1, 'p': 1}           # H+
        ],
        [True, True, False, False],
        [1.0, 2.0, 1.0, 1.0]
    ],

    # Reaction 4: OH- + NO+ = HNO2
    [
        [
            {'H': 1, 'O': 1, 'p': -1}, # OH-
            {'N': 1, 'O': 1, 'p': 1},  # NO+
            {'H': 1, 'N': 1, 'O': 2}   # HNO2
        ],
        [True, True, False],
        [1.0, 1.0, 1.0]
    ],

    # Reaction 5: OH- + NO+ + Tl+ = TlNO2 + H+
    [
        [
            {'H': 1, 'O': 1, 'p': -1}, # OH-
            {'N': 1, 'O': 1, 'p': 1},  # NO+
            {'Tl': 1, 'p': 1},         # Tl+
            {'Tl': 1, 'N': 1, 'O': 2}, # TlNO2
            {'H': 1, 'p': 1}           # H+
        ],
        [True, True, True, False, False],
        [1.0, 1.0, 1.0, 1.0, 1.0]
    ],

    # Herndon, William C. “On Balancing Chemical Equations: Past and Present.” Journal of Chemical Education 74, no. 11 (November 1997): 1359. https://doi.org/10.1021/ed074p1359.
    [
        [
            {'H': 1, 'p': 1},             # H+
            {'p': -1},                    # e-
            {'Fe': 1, 'Cl': 3},           # FeCl3
            {'H': 1, 'I': 1, 'O': 3},     # HIO3
            {'Fe': 1, 'I': 2},            # FeI2
            {'H': 1, 'Cl': 1},            # HCl
            {'H': 2, 'O': 1}              # H2O
        ],
        [True, True, True, True, False, False, False],
        [13.0, 13.0, 1.0, 2.0, 1.0, 3.0, 6.0]
    ],

    # from http://myweb.astate.edu/mdraganj/BalanceEqn.html

    # C3H8 + O2 = CO2 + H2O
    [[{'C': 3, 'H': 8}, {'O': 2}, {'C': 1, 'O': 2}, {'H': 2, 'O': 1}],
    [True, True, False, False],
    [1.0, 5.0, 3.0, 4.0]],

    # Al2(SO3)3 + NaOH = Na2SO3 + Al(OH)3
    [[{'Al': 2, 'S': 3, 'O': 9}, {'Na': 1, 'O': 1, 'H': 1}, {'Na': 2, 'S': 1, 'O': 3}, {'Al': 1, 'O': 3, 'H': 3}],
    [True, True, False, False],
    [1.0, 6.0, 3.0, 2.0]],

    # Al2O3 + Fe = Fe3O4 + Al
    [[{'Al': 2, 'O': 3}, {'Fe': 1}, {'Fe': 3, 'O': 4}, {'Al': 1}],
    [True, True, False, False],
    [4.0, 9.0, 3.0, 8.0]],

    # KClO3 = KCl + O2
    [[{'K': 1, 'Cl': 1, 'O': 3}, {'K': 1, 'Cl': 1}, {'O': 2}],
    [True, False, False],
    [2.0, 2.0, 3.0]],

    # NH4NO3 = N2O + H2O
    [[{'N': 2, 'H': 4, 'O': 3}, {'N': 2, 'O': 1}, {'H': 2, 'O': 1}],
    [True, False, False],
    [1.0, 1.0, 2.0]],

    # NaHCO3 = Na2CO3 + H2O + CO2
    [[{'Na': 1, 'H': 1, 'C': 1, 'O': 3}, {'Na': 2, 'C': 1, 'O': 3}, {'H': 2, 'O': 1}, {'C': 1, 'O': 2}],
    [True, False, False, False],
    [2.0, 1.0, 1.0, 1.0]],

    # P4O10 + H2O = H3PO4
    [[{'P': 4, 'O': 10}, {'H': 2, 'O': 1}, {'H': 3, 'P': 1, 'O': 4}],
    [True, True, False],
    [1.0, 6.0, 4.0]],

    # Be2C + H2O = Be(OH)2 + CH4
    [[{'Be': 2, 'C': 1}, {'H': 2, 'O': 1}, {'Be': 1, 'O': 2, 'H': 2}, {'C': 1, 'H': 4}],
    [True, True, False, False],
    [1.0, 4.0, 2.0, 1.0]],

    # Al + H2SO4 = Al2(SO4)3 + H2
    [[{'Al': 1}, {'H': 2, 'S': 1, 'O': 4}, {'Al': 2, 'S': 3, 'O': 12}, {'H': 2}],
    [True, True, False, False],
    [2.0, 3.0, 1.0, 3.0]],

    # S + HNO3 = H2SO4 + NO2 + H2O
    [[{'S': 1}, {'H': 1, 'N': 1, 'O': 3}, {'H': 2, 'S': 1, 'O': 4}, {'N': 1, 'O': 2}, {'H': 2, 'O': 1}],
    [True, True, False, False, False],
    [1.0, 6.0, 1.0, 6.0, 2.0]],

    # NH3 + CuO = Cu + N2 + H2O
    [[{'N': 1, 'H': 3}, {'Cu': 1, 'O': 1}, {'Cu': 1}, {'N': 2}, {'H': 2, 'O': 1}],
    [True, True, False, False, False],
    [2.0, 3.0, 3.0, 1.0, 3.0]],

    # Cu + HNO3 = Cu(NO3)2 + NO + H2O
    [[{'Cu': 1}, {'H': 1, 'N': 1, 'O': 3}, {'Cu': 1, 'N': 2, 'O': 6}, {'N': 1, 'O': 1}, {'H': 2, 'O': 1}],
    [True, True, False, False, False],
    [3.0, 8.0, 3.0, 2.0, 4.0]],

    # from https://www.chembuddy.com/balancing-stoichiometry-questions-balancing-questions

    # K4Fe(CN)6 + KMnO4 + H2SO4 = KHSO4 + Fe2(SO4)3 + MnSO4 + HNO3 + CO2 + H2O
    [[{'K': 4, 'Fe': 1, 'C': 6, 'N': 6}, {'K': 1, 'Mn': 1, 'O': 4}, {'H': 2, 'S': 1, 'O': 4}, {'K': 1, 'H': 1, 'S': 1, 'O': 4}, {'Fe': 2, 'S': 3, 'O': 12}, {'Mn': 1, 'S': 1, 'O': 4}, {'H': 1, 'N': 1, 'O': 3}, {'C': 1, 'O': 2}, {'H': 2, 'O': 1}],
    [True, True, True, False, False, False, False, False, False],
    [10.0, 122.0, 299.0, 162.0, 5.0, 122.0, 60.0, 60.0, 188.0]],

    # K3Fe(SCN)6 + Na2Cr2O7 + H2SO4 = Fe(NO3)3 + Cr2(SO4)3 + CO2 + H2O + Na2SO4 + KNO3
    [[{'K': 3, 'Fe': 1, 'S': 6, 'C': 6, 'N': 6}, {'Na': 2, 'Cr': 2, 'O': 7}, {'H': 2, 'S': 1, 'O': 4}, {'Fe': 1, 'N': 3, 'O': 9}, {'Cr': 2, 'S': 3, 'O': 12}, {'C': 1, 'O': 2}, {'H': 2, 'O': 1}, {'Na': 2, 'S': 1, 'O': 4}, {'K': 1, 'N': 1, 'O': 3}],
    [True, True, True, False, False, False, False, False, False],
    [1.0, 16.0, 58.0, 1.0, 16.0, 6.0, 58.0, 16.0, 3.0]],

    # K4Fe(SCN)6 + K2Cr2O7 + H2SO4 = Fe2(SO4)3 + Cr2(SO4)3 + CO2 + H2O + K2SO4 + KNO3
    [[{'K': 4, 'Fe': 1, 'S': 6, 'C': 6, 'N': 6}, {'K': 2, 'Cr': 2, 'O': 7}, {'H': 2, 'S': 1, 'O': 4}, {'Fe': 2, 'S': 3, 'O': 12}, {'Cr': 2, 'S': 3, 'O': 12}, {'C': 1, 'O': 2}, {'H': 2, 'O': 1}, {'K': 2, 'S': 1, 'O': 4}, {'K': 1, 'N': 1, 'O': 3}],
    [True, True, True, False, False, False, False, False, False],
    [6.0, 97.0, 355.0, 3.0, 97.0, 36.0, 355.0, 91.0, 36.0]],

    ]

    for atomss, statuses, products in test_cases:
        matrix = stoichiometric_matrix(atomss, statuses)
        products_calc = balance_stoichiometry(matrix)
        check_reaction_balance(matrix, products_calc)
        assert_close1d(products_calc, products)


def test_stoichiometric_matrix():
    res = stoichiometric_matrix([{'Mg': 1, 'O': 1}, {'Mg': 1}, {'O': 2}], [True, False, False])
    assert_close2d([[1, -1, 0], [1, 0, -2]], res)


def test_standard_formation_reaction():
    reactant_coeff, coeff_test, reactant_atomss_test = standard_formation_reaction({'C': 3, 'H': 8})
    assert coeff_test == [3.0, 4.0]
    assert reactant_atomss_test == [{'C': 1}, {'H': 2}]

    reactant_coeff, coeff_test, reactant_atomss_test = standard_formation_reaction({'C': 3, 'H': 7, 'N': 1, 'O': 2, 'S': 1})
    assert coeff_test == [6.0, 7.0, 1.0, 2.0, 2.0]
    assert reactant_atomss_test == [{'C': 1}, {'H': 2}, {'N': 2}, {'O': 2}, {'S': 1}]

    reactant_coeff, coeff_test, reactant_atomss_test = standard_formation_reaction({'C': 6, 'H': 7, 'B': 1, 'O': 2})
    assert coeff_test == [12.0, 7.0, 2.0, 2.0]
    assert reactant_atomss_test == [{'C': 1}, {'H': 2}, {'B': 1}, {'O': 2}]

    reactant_coeff, coeff_test, reactant_atomss_test = standard_formation_reaction({'C': 4, 'H': 12, 'Si': 1})
    assert coeff_test == [4.0, 6.0, 1.0]
    assert reactant_atomss_test ==  [{'C': 1}, {'H': 2}, {'Si': 1}]

    reactant_coeff, coeff_test, reactant_atomss_test = standard_formation_reaction({'C': 12, 'H': 10, 'Cl': 1, 'P': 1})
    assert coeff_test == [24.0, 10.0, 1.0, 2.0]
    assert reactant_atomss_test ==  [{'C': 1}, {'H': 2}, {'Cl': 2}, {'P': 1}]

    reactant_coeff, coeff_test, reactant_atomss_test = standard_formation_reaction({'C': 2, 'H': 4, 'Br': 1, 'F': 1})
    assert coeff_test == [4.0, 4.0, 1.0, 1.0]
    assert reactant_atomss_test == [{'C': 1}, {'H': 2}, {'Br': 2}, {'F': 2}]
