# -*- coding: utf-8 -*-
"""Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2021, Caleb Bell <Caleb.Andrew.Bell@gmail.com>

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

import pytest

from fluids.numerics import assert_close, assert_close1d
from chemicals.identifiers import check_CAS, int_to_CAS, CAS_to_int
import numpy as np
import chemicals

int64_dtype = np.dtype(np.int64)
@pytest.mark.slow
def test_CAS_numbers_valid_and_unique():
    chemicals.complete_lazy_loading()
    for k, df in chemicals.data_reader.df_sources.items():
        if df.index.dtype is int64_dtype:
            CASs = [int_to_CAS(v) for v in df.index]
        else:
            CASs = df.index.values.tolist()
        assert df.index.is_unique
        for CAS in CASs:
            assert check_CAS(CAS)
            CAS_int = CAS_to_int(CAS)
            # Check that the CAS number fits in a 64 bit int
            assert CAS_int < 9223372036854775807