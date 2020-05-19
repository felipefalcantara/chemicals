# -*- coding: utf-8 -*-
'''Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2016, 2017, 2018, 2019 Caleb Bell <Caleb.Andrew.Bell@gmail.com>

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
SOFTWARE.'''

from __future__ import division

__all__ = ['Tb_methods', 'Tb', 'Tm_methods', 'Tm', 
           'Clapeyron', 'Pitzer', 'SMK', 'MK', 'Velasco', 'Riedel', 'Chen', 
           'Liu', 'Vetere', 'Watson', 'Hfus']

import os
import numpy as np
import pandas as pd
from fluids.constants import R, pi, N_A
from chemicals.utils import log, isnan
from chemicals.utils import PY37
from chemicals import miscdata
from chemicals.data_reader import register_df_source, data_source

folder = os.path.join(os.path.dirname(__file__), 'Phase Change')

register_df_source(folder, name='Yaws Boiling Points.tsv')
register_df_source(folder, name='OpenNotebook Melting Points.tsv')
register_df_source(folder, name='Ghazerati Appendix Vaporization Enthalpy.tsv',
                   csv_kwargs={'dtype': {'Hvap298': float}})
register_df_source(folder, name='CRC Handbook Heat of Vaporization.tsv')
register_df_source(folder, name='CRC Handbook Heat of Fusion.tsv')
register_df_source(folder, name='Ghazerati Appendix Sublimation Enthalpy.tsv')

register_df_source(folder, name='Table 2-150 Heats of Vaporization of Inorganic and Organic Liquids.tsv')
register_df_source(folder, name='VDI PPDS Enthalpies of vaporization.tsv')
register_df_source(folder, name='Alibakhshi one-coefficient enthalpy of vaporization.tsv')

_phase_change_const_loaded = False
def load_phase_change_constants():
    global Yaws_data, Tm_ON_data, GharagheiziHvap_data, CRCHvap_data
    global CRCHfus_data, GharagheiziHsub_data, _phase_change_const_loaded
    
    Yaws_data = data_source('Yaws Boiling Points.tsv')
    Tm_ON_data = data_source('OpenNotebook Melting Points.tsv')
    GharagheiziHvap_data = data_source('Ghazerati Appendix Vaporization Enthalpy.tsv')
    CRCHvap_data = data_source('CRC Handbook Heat of Vaporization.tsv')
    CRCHfus_data = data_source('CRC Handbook Heat of Fusion.tsv')
    GharagheiziHsub_data = data_source('Ghazerati Appendix Sublimation Enthalpy.tsv')
    _phase_change_const_loaded = True

_phase_change_corrs_loaded = False
def load_phase_change_correlations():
    global Perrys2_150, _Perrys2_150_values, VDI_PPDS_4, _VDI_PPDS_4_values
    global Alibakhshi_Cs, _phase_change_corrs_loaded

    # 66554 for pandas; 19264 bytes for numpy
    Perrys2_150 = data_source('Table 2-150 Heats of Vaporization of Inorganic and Organic Liquids.tsv')
    _Perrys2_150_values = np.array(Perrys2_150.values[:, 1:], dtype=float)
    
    # 52187 bytes for pandas, 13056 bytes for numpy
    VDI_PPDS_4 = data_source('VDI PPDS Enthalpies of vaporization.tsv')
    _VDI_PPDS_4_values = np.array(VDI_PPDS_4.values[:, 2:], dtype=float)
    
    Alibakhshi_Cs = data_source('Alibakhshi one-coefficient enthalpy of vaporization.tsv')
    _phase_change_corrs_loaded = True
    
if PY37:
    def __getattr__(name):
        if name in ('Yaws_data', 'Tm_ON_data', 'GharagheiziHvap_data', 'CRCHvap_data',
                    'CRCHfus_data', 'GharagheiziHsub_data'):
            load_phase_change_constants()
            return globals()[name]
        elif name in ('Perrys2_150', '_Perrys2_150_values', 'VDI_PPDS_4', '_VDI_PPDS_4_values', 'Alibakhshi_Cs'):
            load_phase_change_correlations()
            return globals()[name]
        raise AttributeError("module %s has no attribute %s" %(__name__, name))
else:
    load_phase_change_constants()
    load_phase_change_correlations()

### Boiling Point at 1 atm

CRC_ORG = 'CRC_ORG'
CRC_INORG = 'CRC_INORG'
YAWS = 'YAWS'
NONE = 'NONE'

Tb_methods = [CRC_INORG, CRC_ORG, YAWS]


def Tb(CASRN, AvailableMethods=False, Method=None, IgnoreMethods=[]):
    r'''This function handles the retrieval of a chemical's boiling
    point. Lookup is based on CASRNs. Will automatically select a data
    source to use if no Method is provided; returns None if the data is not
    available.

    Prefered sources are 'CRC Physical Constants, organic' for organic
    chemicals, and 'CRC Physical Constants, inorganic' for inorganic
    chemicals. Function has data for approximately 13000 chemicals.

    Parameters
    ----------
    CASRN : string
        CASRN [-]

    Returns
    -------
    Tb : float
        Boiling temperature, [K]
    methods : list, only returned if AvailableMethods == True
        List of methods which can be used to obtain Tb with the given inputs

    Other Parameters
    ----------------
    Method : string, optional
        A string for the method name to use, as defined by constants in
        Tb_methods
    AvailableMethods : bool, optional
        If True, function will determine which methods can be used to obtain
        Tb for the desired chemical, and will return methods instead of Tb
    IgnoreMethods : list, optional
        A list of methods to ignore in obtaining the full list of methods,
        useful for for performance reasons and ignoring inaccurate methods

    Notes
    -----
    A total of three methods are available for this function. They are:

        * 'CRC_ORG', a compillation of data on organics
          as published in [1]_.
        * 'CRC_INORG', a compillation of data on
          inorganic as published in [1]_.
        * 'YAWS', a large compillation of data from a
          variety of sources; no data points are sourced in the work of [2]_.

    Examples
    --------
    >>> Tb('7732-18-5')
    373.124

    References
    ----------
    .. [1] Haynes, W.M., Thomas J. Bruno, and David R. Lide. CRC Handbook of
       Chemistry and Physics, 95E. Boca Raton, FL: CRC press, 2014.
    .. [2] Yaws, Carl L. Thermophysical Properties of Chemicals and
       Hydrocarbons, Second Edition. Amsterdam Boston: Gulf Professional
       Publishing, 2014.
    '''
    if not _phase_change_const_loaded:
        load_phase_change_constants()
    def list_methods():
        methods = []
        if CASRN in miscdata.CRC_inorganic_data.index and not isnan(miscdata.CRC_inorganic_data.at[CASRN, 'Tb']):
            methods.append(CRC_INORG)
        if CASRN in miscdata.CRC_organic_data.index and not isnan(miscdata.CRC_organic_data.at[CASRN, 'Tb']):
            methods.append(CRC_ORG)
        if CASRN in Yaws_data.index:
            methods.append(YAWS)
        if IgnoreMethods:
            for Method in IgnoreMethods:
                if Method in methods:
                    methods.remove(Method)
        methods.append(NONE)
        return methods
    if AvailableMethods:
        return list_methods()
    if not Method:
        Method = list_methods()[0]

    if Method == CRC_INORG:
        return float(miscdata.CRC_inorganic_data.at[CASRN, 'Tb'])
    elif Method == CRC_ORG:
        return float(miscdata.CRC_organic_data.at[CASRN, 'Tb'])
    elif Method == YAWS:
        return float(Yaws_data.at[CASRN, 'Tb'])
    elif Method == NONE:
        return None
    else:
        raise Exception('Failure in in function')


### Melting Point


OPEN_NTBKM = 'OPEN_NTBKM'

Tm_methods = [OPEN_NTBKM, CRC_INORG, CRC_ORG]


def Tm(CASRN, AvailableMethods=False, Method=None, IgnoreMethods=[]):
    r'''This function handles the retrieval of a chemical's melting
    point. Lookup is based on CASRNs. Will automatically select a data
    source to use if no Method is provided; returns None if the data is not
    available.

    Prefered sources are 'Open Notebook Melting Points', with backup sources
    'CRC Physical Constants, organic' for organic chemicals, and
    'CRC Physical Constants, inorganic' for inorganic chemicals. Function has
    data for approximately 14000 chemicals.

    Parameters
    ----------
    CASRN : string
        CASRN [-]

    Returns
    -------
    Tm : float
        Melting temperature, [K]
    methods : list, only returned if AvailableMethods == True
        List of methods which can be used to obtain Tm with the given inputs

    Other Parameters
    ----------------
    Method : string, optional
        A string for the method name to use, as defined by constants in
        Tm_methods
    AvailableMethods : bool, optional
        If True, function will determine which methods can be used to obtain
        Tm for the desired chemical, and will return methods instead of Tm
    IgnoreMethods : list, optional
        A list of methods to ignore in obtaining the full list of methods

    Notes
    -----
    A total of three sources are available for this function. They are:

        * 'OPEN_NTBKM, a compillation of data on organics
          as published in [1]_ as Open Notebook Melting Points; Averaged 
          (median) values were used when
          multiple points were available. For more information on this
          invaluable and excellent collection, see
          http://onswebservices.wikispaces.com/meltingpoint.
        * 'CRC_ORG', a compillation of data on organics
          as published in [2]_.
        * 'CRC_INORG', a compillation of data on
          inorganic as published in [2]_.

    Examples
    --------
    >>> Tm(CASRN='7732-18-5')
    273.15

    References
    ----------
    .. [1] Bradley, Jean-Claude, Antony Williams, and Andrew Lang.
       "Jean-Claude Bradley Open Melting Point Dataset", May 20, 2014.
       https://figshare.com/articles/Jean_Claude_Bradley_Open_Melting_Point_Datset/1031637.
    .. [2] Haynes, W.M., Thomas J. Bruno, and David R. Lide. CRC Handbook of
       Chemistry and Physics, 95E. Boca Raton, FL: CRC press, 2014.
    '''
    if not _phase_change_const_loaded:
        load_phase_change_constants()
    def list_methods():
        methods = []
        if CASRN in Tm_ON_data.index:
            methods.append(OPEN_NTBKM)
        if CASRN in miscdata.CRC_inorganic_data.index and not isnan(miscdata.CRC_inorganic_data.at[CASRN, 'Tm']):
            methods.append(CRC_INORG)
        if CASRN in miscdata.CRC_organic_data.index and not isnan(miscdata.CRC_organic_data.at[CASRN, 'Tm']):
            methods.append(CRC_ORG)
        if IgnoreMethods:
            for Method in IgnoreMethods:
                if Method in methods:
                    methods.remove(Method)
        methods.append(NONE)
        return methods
    if AvailableMethods:
        return list_methods()
    if not Method:
        Method = list_methods()[0]

    if Method == OPEN_NTBKM:
        return float(Tm_ON_data.at[CASRN, 'Tm'])
    elif Method == CRC_INORG:
        return float(miscdata.CRC_inorganic_data.at[CASRN, 'Tm'])
    elif Method == CRC_ORG:
        return float(miscdata.CRC_organic_data.at[CASRN, 'Tm'])
    elif Method == NONE:
        return None
    else:
        raise Exception('Failure in in function')


### Enthalpy of Vaporization at T

def Clapeyron(T, Tc, Pc, dZ=1, Psat=101325):
    r'''Calculates enthalpy of vaporization at arbitrary temperatures using the
    Clapeyron equation.

    The enthalpy of vaporization is given by:

    .. math::
        \Delta H_{vap} = RT \Delta Z \frac{\ln (P_c/Psat)}{(1-T_{r})}

    Parameters
    ----------
    T : float
        Temperature of fluid [K]
    Tc : float
        Critical temperature of fluid [K]
    Pc : float
        Critical pressure of fluid [Pa]
    dZ : float
        Change in compressibility factor between liquid and gas, []
    Psat : float
        Saturation pressure of fluid [Pa], optional

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization, [J/mol]

    Notes
    -----
    No original source is available for this equation.
    [1]_ claims this equation overpredicts enthalpy by several percent.
    Under Tr = 0.8, dZ = 1 is a reasonable assumption.
    This equation is most accurate at the normal boiling point.

    Internal units are bar.

    WARNING: I believe it possible that the adjustment for pressure may be incorrect

    Examples
    --------
    Problem from Perry's examples.

    >>> Clapeyron(T=294.0, Tc=466.0, Pc=5.55E6)
    26512.36357131963

    References
    ----------
    .. [1] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    '''
    Tr = T/Tc
    return R*T*dZ*log(Pc/Psat)/(1. - Tr)


def Pitzer(T, Tc, omega):
    r'''Calculates enthalpy of vaporization at arbitrary temperatures using a
    fit by [2]_ to the work of Pitzer [1]_; requires a chemical's critical
    temperature and acentric factor.

    The enthalpy of vaporization is given by:

    .. math::
        \frac{\Delta_{vap} H}{RT_c}=7.08(1-T_r)^{0.354}+10.95\omega(1-T_r)^{0.456}

    Parameters
    ----------
    T : float
        Temperature of fluid [K]
    Tc : float
        Critical temperature of fluid [K]
    omega : float
        Acentric factor [-]

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization, [J/mol]

    Notes
    -----
    This equation is listed in [3]_, page 2-487 as method #2 for estimating
    Hvap. This cites [2]_.

    The recommended range is 0.6 to 1 Tr. Users should expect up to 5% error.
    T must be under Tc, or an exception is raised.

    The original article has been reviewed and found to have a set of tabulated
    values which could be used instead of the fit function to provide additional
    accuracy.

    Examples
    --------
    Example as in [3]_, p2-487; exp: 37.51 kJ/mol

    >>> Pitzer(452, 645.6, 0.35017)
    36696.749078320056

    References
    ----------
    .. [1] Pitzer, Kenneth S. "The Volumetric and Thermodynamic Properties of
       Fluids. I. Theoretical Basis and Virial Coefficients."
       Journal of the American Chemical Society 77, no. 13 (July 1, 1955):
       3427-33. doi:10.1021/ja01618a001
    .. [2] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    .. [3] Green, Don, and Robert Perry. Perry's Chemical Engineers' Handbook,
       Eighth Edition. McGraw-Hill Professional, 2007.
    '''
    Tr = T/Tc
    return R*Tc * (7.08*(1. - Tr)**0.354 + 10.95*omega*(1. - Tr)**0.456)


def SMK(T, Tc, omega):
    r'''Calculates enthalpy of vaporization at arbitrary temperatures using a
    the work of [1]_; requires a chemical's critical temperature and
    acentric factor.

    The enthalpy of vaporization is given by:

    .. math::
         \frac{\Delta H_{vap}} {RT_c} =
         \left( \frac{\Delta H_{vap}} {RT_c} \right)^{(R1)} + \left(
         \frac{\omega - \omega^{(R1)}} {\omega^{(R2)} - \omega^{(R1)}} \right)
         \left[\left( \frac{\Delta H_{vap}} {RT_c} \right)^{(R2)} - \left(
         \frac{\Delta H_{vap}} {RT_c} \right)^{(R1)} \right]

        \left( \frac{\Delta H_{vap}} {RT_c} \right)^{(R1)}
        = 6.537 \tau^{1/3} - 2.467 \tau^{5/6} - 77.251 \tau^{1.208} +
        59.634 \tau + 36.009 \tau^2 - 14.606 \tau^3

        \left( \frac{\Delta H_{vap}} {RT_c} \right)^{(R2)} - \left(
        \frac{\Delta H_{vap}} {RT_c} \right)^{(R1)}=-0.133 \tau^{1/3} - 28.215
        \tau^{5/6} - 82.958 \tau^{1.208} + 99.00 \tau  + 19.105 \tau^2 -2.796 \tau^3

        \tau = 1-T/T_c

    Parameters
    ----------
    T : float
        Temperature of fluid [K]
    Tc : float
        Critical temperature of fluid [K]
    omega : float
        Acentric factor [-]

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization, [J/mol]

    Notes
    -----
    The original article has been reviewed and found to have coefficients with
    slightly more precision. Additionally, the form of the equation is slightly
    different, but numerically equivalent.

    The refence fluids are:

    :math:`\omega_0` = benzene = 0.212

    :math:`\omega_1` = carbazole = 0.461

    A sample problem in the article has been verified. The numerical result
    presented by the author requires high numerical accuracy to obtain.

    Examples
    --------
    Problem in [1]_:

    >>> SMK(553.15, 751.35, 0.302)
    39866.18999046229

    References
    ----------
    .. [1] Sivaraman, Alwarappa, Joe W. Magee, and Riki Kobayashi. "Generalized
       Correlation of Latent Heats of Vaporization of Coal-Liquid Model Compounds
       between Their Freezing Points and Critical Points." Industrial &
       Engineering Chemistry Fundamentals 23, no. 1 (February 1, 1984): 97-100.
       doi:10.1021/i100013a017.
    '''
    if T > Tc:
        return 0.0
    omegaR1, omegaR2 = 0.212, 0.461
    A10 = 6.536924
    A20 = -2.466698
    A30 = -77.52141
    B10 = 59.63435
    B20 = 36.09887
    B30 = -14.60567

    A11 = -0.132584
    A21 = -28.21525
    A31 = -82.95820
    B11 = 99.00008
    B21 = 19.10458
    B31 = -2.795660
    # 1 branch, two powers, 1 division
    tau = 1. - T/Tc
    tau_16 = tau**(1.0/6.0)
    tau_13 = tau_16*tau_16
    tau_56 = tau_13*tau_13*tau_16
    tau_other = tau**1.2083333333333333 #(1-1/8. + 1/3.))
    L0 = (A10*tau_13 + A20*tau_56 + A30*tau_other +
          tau*(B10 + tau*(B20 + B30*tau)))

    L1 = (A11*tau_13 + A21*tau_56 + A31*tau_other + 
           tau*(B11 + tau*(B21 + B31*tau)))

    domega = 4.016064257028112*(omega - omegaR1) # 4.016... = 1.0/(omegaR2 - omegaR1
#    domega = (omega - omegaR1)/(omegaR2 - omegaR1)
    return R*Tc*(L0 + domega*L1)


def MK(T, Tc, omega):
    r'''Calculates enthalpy of vaporization at arbitrary temperatures using a
    the work of [1]_; requires a chemical's critical temperature and
    acentric factor.

    The enthalpy of vaporization is given by:

    .. math::
        \Delta H_{vap} =  \Delta H_{vap}^{(0)} + \omega \Delta H_{vap}^{(1)} + \omega^2 \Delta H_{vap}^{(2)}

        \frac{\Delta H_{vap}^{(i)}}{RT_c} = b^{(j)} \tau^{1/3} + b_2^{(j)} \tau^{5/6}
        + b_3^{(j)} \tau^{1.2083} + b_4^{(j)}\tau + b_5^{(j)} \tau^2 + b_6^{(j)} \tau^3

        \tau = 1-T/T_c

    Parameters
    ----------
    T : float
        Temperature of fluid [K]
    Tc : float
        Critical temperature of fluid [K]
    omega : float
        Acentric factor [-]

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization, [J/mol]

    Notes
    -----
    The original article has been reviewed. A total of 18 coefficients are used:

    WARNING: The correlation has been implemented as described in the article,
    but its results seem different and with some error.
    Its results match with other functions however.

    Has poor behavior for low-temperature use.

    Examples
    --------
    Problem in article for SMK function.

    >>> MK(553.15, 751.35, 0.302)
    38728.00667307733

    References
    ----------
    .. [1] Morgan, David L., and Riki Kobayashi. "Extension of Pitzer CSP
       Models for Vapor Pressures and Heats of Vaporization to Long-Chain
       Hydrocarbons." Fluid Phase Equilibria 94 (March 15, 1994): 51-87.
       doi:10.1016/0378-3812(94)87051-9.
    '''
    bs = [[5.2804, 0.080022, 7.2543],
          [12.8650, 273.23, -346.45],
          [1.1710, 465.08, -610.48],
          [-13.1160, -638.51, 839.89],
          [0.4858, -145.12, 160.05],
          [-1.0880, 74.049, -50.711]]

    tau = 1. - T/Tc
    H0 = (bs[0][0]*tau**(0.3333) + bs[1][0]*tau**(0.8333) + bs[2][0]*tau**(1.2083) +
    bs[3][0]*tau + bs[4][0]*tau**(2) + bs[5][0]*tau**(3))*R*Tc

    H1 = (bs[0][1]*tau**(0.3333) + bs[1][1]*tau**(0.8333) + bs[2][1]*tau**(1.2083) +
    bs[3][1]*tau + bs[4][1]*tau**(2) + bs[5][1]*tau**(3))*R*Tc

    H2 = (bs[0][2]*tau**(0.3333) + bs[1][2]*tau**(0.8333) + bs[2][2]*tau**(1.2083) +
    bs[3][2]*tau + bs[4][2]*tau**(2) + bs[5][2]*tau**(3))*R*Tc

    return H0 + omega*H1 + omega**2*H2


def Velasco(T, Tc, omega):
    r'''Calculates enthalpy of vaporization at arbitrary temperatures using a
    the work of [1]_; requires a chemical's critical temperature and
    acentric factor.

    The enthalpy of vaporization is given by:

    .. math::
        \Delta_{vap} H = RT_c(7.2729 + 10.4962\omega + 0.6061\omega^2)(1-T_r)^{0.38}

    Parameters
    ----------
    T : float
        Temperature of fluid [K]
    Tc : float
        Critical temperature of fluid [K]
    omega : float
        Acentric factor [-]

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization, [J/mol]

    Notes
    -----
    The original article has been reviewed. It is regressed from enthalpy of
    vaporization values at 0.7Tr, from 121 fluids in REFPROP 9.1.
    A value in the article was read to be similar, but slightly too low from
    that calculated here.

    Examples
    --------
    From graph, in [1]_ for perfluoro-n-heptane.

    >>> Velasco(333.2, 476.0, 0.5559)
    33299.428636069264

    References
    ----------
    .. [1] Velasco, S., M. J. Santos, and J. A. White. "Extended Corresponding
       States Expressions for the Changes in Enthalpy, Compressibility Factor
       and Constant-Volume Heat Capacity at Vaporization." The Journal of
       Chemical Thermodynamics 85 (June 2015): 68-76.
       doi:10.1016/j.jct.2015.01.011.
    '''
    return (7.2729 + 10.4962*omega + 0.6061*omega**2)*(1-T/Tc)**0.38*R*Tc


### Enthalpy of Vaporization at Normal Boiling Point.

def Riedel(Tb, Tc, Pc):
    r'''Calculates enthalpy of vaporization at the boiling point, using the
    Ridel [1]_ CSP method. Required information are critical temperature
    and pressure, and boiling point. Equation taken from [2]_ and [3]_.

    The enthalpy of vaporization is given by:

    .. math::
        \Delta_{vap} H=1.093 T_b R\frac{\ln P_c-1.013}{0.930-T_{br}}

    Parameters
    ----------
    Tb : float
        Boiling temperature of fluid [K]
    Tc : float
        Critical temperature of fluid [K]
    Pc : float
        Critical pressure of fluid [Pa]

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization at the normal boiling point, [J/mol]

    Notes
    -----
    This equation has no example calculation in any source. The source has not
    been verified. It is equation 4-144 in Perry's. Perry's also claims that
    errors seldom surpass 5%.

    [2]_ is the source of example work here, showing a calculation at 0.0%
    error.

    Internal units of pressure are bar.

    Examples
    --------
    Pyridine, 0.0% err vs. exp: 35090 J/mol; from Poling [2]_.

    >>> Riedel(388.4, 620.0, 56.3E5)
    35089.80179000598

    References
    ----------
    .. [1] Riedel, L. "Eine Neue Universelle Dampfdruckformel Untersuchungen
       Uber Eine Erweiterung Des Theorems Der Ubereinstimmenden Zustande. Teil
       I." Chemie Ingenieur Technik 26, no. 2 (February 1, 1954): 83-89.
       doi:10.1002/cite.330260206.
    .. [2] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    .. [3] Green, Don, and Robert Perry. Perry's Chemical Engineers' Handbook,
       Eighth Edition. McGraw-Hill Professional, 2007.
    '''
    Pc = Pc/1E5  # Pa to bar
    Tbr = Tb/Tc
    return 1.093*Tb*R*(log(Pc) - 1.013)/(0.93 - Tbr)


def Chen(Tb, Tc, Pc):
    r'''Calculates enthalpy of vaporization using the Chen [1]_ correlation
    and a chemical's critical temperature, pressure and boiling point.

    The enthalpy of vaporization is given by:

    .. math::
        \Delta H_{vb} = RT_b \frac{3.978 T_r - 3.958 + 1.555 \ln P_c}{1.07 - T_r}

    Parameters
    ----------
    Tb : float
        Boiling temperature of the fluid [K]
    Tc : float
        Critical temperature of fluid [K]
    Pc : float
        Critical pressure of fluid [Pa]

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization, [J/mol]

    Notes
    -----
    The formulation presented in the original article is similar, but uses
    units of atm and calorie instead. The form in [2]_ has adjusted for this.
    A method for estimating enthalpy of vaporization at other conditions
    has also been developed, but the article is unclear on its implementation.
    Based on the Pitzer correlation.

    Internal units: bar and K

    Examples
    --------
    Same problem as in Perry's examples.

    >>> Chen(294.0, 466.0, 5.55E6)
    26705.902558030946

    References
    ----------
    .. [1] Chen, N. H. "Generalized Correlation for Latent Heat of Vaporization."
       Journal of Chemical & Engineering Data 10, no. 2 (April 1, 1965): 207-10.
       doi:10.1021/je60025a047
    .. [2] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    '''
    Tbr = Tb/Tc
    Pc = Pc/1E5  # Pa to bar
    return R*Tb*(3.978*Tbr - 3.958 + 1.555*log(Pc))/(1.07 - Tbr)


def Liu(Tb, Tc, Pc):
    r'''Calculates enthalpy of vaporization at the normal boiling point using
    the Liu [1]_ correlation, and a chemical's critical temperature, pressure
    and boiling point.

    The enthalpy of vaporization is given by:

    .. math::
        \Delta H_{vap} = RT_b \left[ \frac{T_b}{220}\right]^{0.0627} \frac{
        (1-T_{br})^{0.38} \ln(P_c/P_A)}{1-T_{br} + 0.38 T_{br} \ln T_{br}}

    Parameters
    ----------
    Tb : float
        Boiling temperature of the fluid [K]
    Tc : float
        Critical temperature of fluid [K]
    Pc : float
        Critical pressure of fluid [Pa]

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization, [J/mol]

    Notes
    -----
    This formulation can be adjusted for lower boiling points, due to the use
    of a rationalized pressure relationship. The formulation is taken from
    the original article.

    A correction for alcohols and organic acids based on carbon number,
    which only modifies the boiling point, is available but not implemented.

    No sample calculations are available in the article.

    Internal units: Pa and K

    Examples
    --------
    Same problem as in Perry's examples

    >>> Liu(294.0, 466.0, 5.55E6)
    26378.575260517395

    References
    ----------
    .. [1] LIU, ZHI-YONG. "Estimation of Heat of Vaporization of Pure Liquid at
       Its Normal Boiling Temperature." Chemical Engineering Communications
       184, no. 1 (February 1, 2001): 221-28. doi:10.1080/00986440108912849.
    '''
    Tbr = Tb/Tc
    return R*Tb*(Tb/220.)**0.0627*(1. - Tbr)**0.38*log(Pc/101325.) \
        / (1 - Tbr + 0.38*Tbr*log(Tbr))


def Vetere(Tb, Tc, Pc, F=1):
    r'''Calculates enthalpy of vaporization at the boiling point, using the
    Vetere [1]_ CSP method. Required information are critical temperature
    and pressure, and boiling point. Equation taken from [2]_.

    The enthalpy of vaporization is given by:

    .. math::
        \frac {\Delta H_{vap}}{RT_b} = \frac{\tau_b^{0.38}
        \left[ \ln P_c - 0.513 + \frac{0.5066}{P_cT_{br}^2}\right]}
        {\tau_b + F(1-\tau_b^{0.38})\ln T_{br}}

    Parameters
    ----------
    Tb : float
        Boiling temperature of fluid [K]
    Tc : float
        Critical temperature of fluid [K]
    Pc : float
        Critical pressure of fluid [Pa]
    F : float, optional
        Constant for a fluid, [-]

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization at the boiling point, [J/mol]

    Notes
    -----
    The equation cannot be found in the original source. It is believed that a
    second article is its source, or that DIPPR staff have altered the formulation.

    Internal units of pressure are bar.

    Examples
    --------
    Example as in [2]_, p2-487; exp: 25.73

    >>> Vetere(294.0, 466.0, 5.55E6)
    26363.43895706672

    References
    ----------
    .. [1] Vetere, Alessandro. "Methods to Predict the Vaporization Enthalpies
       at the Normal Boiling Temperature of Pure Compounds Revisited."
       Fluid Phase Equilibria 106, no. 1-2 (May 1, 1995): 1–10.
       doi:10.1016/0378-3812(94)02627-D.
    .. [2] Green, Don, and Robert Perry. Perry's Chemical Engineers' Handbook,
       Eighth Edition. McGraw-Hill Professional, 2007.
    '''
    Tbr = Tb/Tc
    taub = 1-Tb/Tc
    Pc = Pc/1E5
    term = taub**0.38*(log(Pc)-0.513 + 0.5066/Pc/Tbr**2) / (taub + F*(1-taub**0.38)*log(Tbr))
    return R*Tb*term


### Enthalpy of Vaporization at STP.


### Enthalpy of Vaporization adjusted for T

def Watson(T, Hvap_ref, T_ref, Tc, exponent=0.38):
    r'''Calculates enthalpy of vaporization of a chemical at a temperature 
    using the known heat of vaporization at another temperature according to
    the Watson [1]_ [2]_ correlation. This is an application of the 
    corresponding-states principle, with an emperical temperature dependence.

    .. math::
        \frac{\Delta H_{vap}^{T2}}{\Delta H_{vap}^{T1}}  = \left(
        \frac{1-T_{r,1}}{1-T_{r,2}} \right)^{0.38}

    Parameters
    ----------
    T : float
        Temperature for which to calculate heat of vaporization, [K]
    Hvap_ref : float
        Enthalpy of vaporization at the known temperature point, [J/mol]
    T_ref : float
        Reference temperature; ideally as close to `T` as posible, [K]
    Tc : float
        Critical temperature of fluid [K]
    exponent : float, optional
        A fit exponent can optionally be used instead of the Watson 0.38 
        exponent, [-]

    Returns
    -------
    Hvap : float
        Enthalpy of vaporization at `T`, [J/mol]

    Notes
    -----

    Examples
    --------
    Predict the enthalpy of vaporization of water at 320 K from a point at
    300 K:
        
    >>> Watson(T=320, Hvap_ref=43908, T_ref=300.0, Tc=647.14)
    42928.990094915454
    
    The error is 0.38% compared to the correct value of 43048 J/mol.

    References
    ----------
    .. [1] Watson, KM. "Thermodynamics of the Liquid State." Industrial & 
       Engineering Chemistry 35, no. 4 (1943): 398–406.
    .. [2] Martin, Joseph J., and John B. Edwards. "Correlation of Latent Heats
       of Vaporization.” AIChE Journal 11, no. 2 (1965): 331-33. 
       https://doi.org/10.1002/aic.690110226.
    '''
    Tr = T/Tc
    Trefr = T_ref/Tc
    H2 = Hvap_ref*((1.0 - Tr)/(1.0 - Trefr))**exponent
    return H2


### Heat of Fusion

CRC = 'CRC'
Hfus_methods = [CRC]


def Hfus(CASRN, AvailableMethods=False, Method=None, IgnoreMethods=[]): 
    r'''This function handles the retrieval of a chemical's heat of fusion.
    Lookup is based on CASRNs. Will automatically select a data
    source to use if no Method is provided; returns None if the data is not
    available.

    The prefered source is 'CRC'. Function has data for approximately 1100 
    chemicals.

    Parameters
    ----------
    CASRN : string
        CASRN [-]

    Returns
    -------
    Hfus : float
        Molar enthalpy of fusion at normal melting point, [J/mol]
    methods : list, only returned if AvailableMethods == True
        List of methods which can be used to obtain Tb with the given inputs

    Other Parameters
    ----------------
    Method : string, optional
        A string for the method name to use, as defined by constants in
        Hfus_methods
    AvailableMethods : bool, optional
        If True, function will determine which methods can be used to obtain
        hfus for the desired chemical, and will return methods instead of Hfus
    IgnoreMethods : list, optional
        A list of methods to ignore in obtaining the full list of methods,
        useful for for performance reasons and ignoring inaccurate methods

    Notes
    -----
    A total of one method is available for this function. They are:

        * 'CRC', a compillation of data on organics and inorganics as published 
        in [1]_.

    Examples
    --------
    >>> Hfus('7732-18-5')
    6010.0

    References
    ----------
    .. [1] Haynes, W.M., Thomas J. Bruno, and David R. Lide. CRC Handbook of
       Chemistry and Physics, 95E. Boca Raton, FL: CRC press, 2014.
    '''
    if not _phase_change_const_loaded:
        load_phase_change_constants()
    def list_methods():
        methods = []
        if CASRN in CRCHfus_data.index:
            methods.append(CRC)
        methods.append(NONE)
        if IgnoreMethods:
            for Method in IgnoreMethods:
                if Method in methods:
                    methods.remove(Method)
        return methods
    if AvailableMethods:
        return list_methods()
    if not Method:
        Method = list_methods()[0]

    if Method == CRC:
        return CRCHfus_data.at[CASRN, 'Hfus']
    elif Method == NONE:
        return None
    else:
        raise ValueError('Unrecognized method')

