"""
  Copyright (c) 2016- by Dietmar W Weiss

  This is free software; you can redistribute it and/or modify it
  under the terms of the GNU Lesser General Public License as
  published by the Free Software Foundation; either version 3.0 of
  the License, or (at your option) any later version.

  This software is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
  Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with this software; if not, write to the Free
  Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
  02110-1301 USA, or see the FSF site: http://www.fsf.org.

  Version:
      2019-09-17 DWW
"""

import types
import inspect
from collections import OrderedDict
import numpy as np
from typing import Optional, Sequence, Tuple, Union


def deg2rad(deg: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts angles from degrees to radians
    """
    return np.radians(deg)


def rad2deg(rad: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts angles from degrees to radians
    """
    return np.degrees(rad)


def C2K(C: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts temperature from Celsius to Kelvin
    """
    return np.asanyarray(C) + 273.15


def K2C(K: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts temperature from Kelvin to Celsius
    """
    return np.asanyarray(K) - 273.15


def F2C(F: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts temperature from Fahrenheit to Celsius
    """
    return (np.asanyarray(F) - 32) / 1.8


def C2F(C: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts temperature from Celsius to Fahrenheit
    """
    return 1.8 * np.asanyarray(C) + 32


def F2K(F: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts temperature from Fahrenheit to Kelvin
    """
    return C2K(F2C(np.asanyarray(F)))


def K2F(K: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts temperature from Kelvin to Fahrenheit
    """
    return C2F(K2C(np.asanyarray(K)))


def Pa2bar(pa: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts pressure from [Pascal] to [bar]
    """
    return np.asanyarray(pa) * 1e-5


def ksi2Pa(ksi: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts pressure from [ksi] (pounds per square inch) to [Pascal]
    """
    return np.asanyarray(ksi) * 6.894745e+6


def msi2Pa(msi: Union[float, np.ndarray]) -> np.ndarray:
    """
    Converts pressure from [msi] (megapounds per square inch) to [Pascal]
    """
    return np.asanyarray(msi) * 6.894745e+9


class Parameter(object):
    """
    Defines a parameter with:
      - identifier (raw string and and latex version),
      - actual value,
      - reference value,
      - absolute/relative flag,
      - unit,
      - operational range,
      - tolerated range, 
      - expected range,
      - accuracy (absolute, relative to reading '%',
                  relative to full scale '%FS'),
      - repeatability,
      - sampling rate,
      - rate-of-change (d(Parameter)/dt)
      - trust score

    Note:
      - val (float):     actual value of parameter with unit 'self.unit'
      - ref (float):     reference value of parameter with unit 'self.unit'
      - absolute (bool): if True, temperatures are in Kelvin and pressure
                         is not relative (not gauge pressure)
      - member function __call__() returns self.val
    """

    def __init__(self, identifier: str='Parameter',
                 unit: str='/',
                 absolute: bool=True,
                 latex: Optional[str]=None,
                 val: Optional[float]=None,
                 ref: Optional[float]=None,
                 comment: Optional[str]=None) -> None:
        self.comment: str = comment if comment is not None else ''
        self.identifier: str = identifier
        self.unit: str = unit
        if self.unit[0] != '[':
            self.unit = '[' + self.unit
        if self.unit[-1] != ']':
            self.unit = self.unit + ']'
        self.absolute: bool = bool(absolute)

        self.val: float = val if val is not None else 0.
        self.ref: float = ref if ref is not None else self.val
        self._operational: Tuple[float, float] = (min(0., self.val),
                                                  max(0., self.val))
        self._tolerated: Tuple[float, float] = self._operational
        self._expected: Tuple[float, float] = self._tolerated

        # Latex symbol, e.g. '$\varrho$'
        if latex:
            self.latex: str = latex
        else:
            self.latex: str = self.identifier
        if len(self.latex) > 0:
            if self.latex[0] != '$':
                self.latex = '$' + self.latex
            if self.latex[-1] != '$':
                self.latex = self.latex + '$'

        # accuracy can be:
        # - absolute (e.g. '1.2'),
        # - relative to reading (e.g. '1.2%') or
        # - relative to full scale (e.g. '1.2%FS')
        self._accuracy: Tuple[str, str] = ('-1%', '+1%')

        # repeatability can be:
        # - absolute (e.g. '1.2'),
        # - relative to full scale (e.g. '1.2%FS')
        self._repeatability: Tuple[str, str, str] = ('-0.01', '0.01', '95%')

        self.sampling: float = 100.                              # [1/s]
        self.rate_of_change: float = 0.                # [(self.unit)/s]
        self.trust_score: int = 10  # confidence, 10: excellent, 0: poor

    def __call__(self) -> float:
        return self.val

    @property
    def accuracy(self) -> Tuple[str, str]:
        return self._accuracy

    @accuracy.setter
    def accuracy(self, value: Union[str, Tuple[float, float]]) -> None:
        """
        Note:
            accuracy is stored as 2-tuple of str
            
            foo = Parameter()
            foo.accuracy = '1%'
            foo.accuracy = '3.0'
            foo.accuracy = ('-1.2', '3%')
        """
        value = np.atleast_1d(value)
        if len(value) >= 1:
            x0 = str(value[0]).upper()
        else:
            x0 = '0'
        if len(value) >= 2:
            self._accuracy = (x0, str(value[1]).upper())
        elif len(value) == 1:
            self._accuracy = ('-' + x0, x0)
        else:
            assert 0

    @property
    def repeatability(self) -> Tuple[str, str, str]:
        return self._repeatability

    @repeatability.setter
    def repeatability(self, value: Union[str, Tuple[str, str], 
                                         Tuple[str, str, str]]) -> None:
        """
        Note:
            Repeatability is stored as string
        """
        value = np.atleast_1d(value)
        if len(value) >= 1:
            x0 = str(value[0]).upper()
        else:
            x0 = '0'
        if len(value) == 3:
            self._repeatability = value
            p = str(value[2])
            if p[-1] != '%':
                p += '%'
            if p[0] == '-':
                p = p[1:]
            self._repeatability = (x0, str(value[1]).upper(), p)
        elif len(value) == 2:
            self._repeatability = (x0, str(value[1]).upper(), '95%')
        elif len(value) == 1:
            self._repeatability = ('-' + x0, x0, '95%')
        else:
            assert 0

    @property
    def operational(self) -> Tuple[float, float]:
        return self._operational

    @operational.setter
    def operational(self, value: Union[float, Sequence[float]]) -> None:
        value = np.atleast_1d(value)
        if len(value) >= 1:
            x0 = float(value[0])
        else:
            x0 = 0.
        if len(value) >= 2:
            x1 = float(value[1])
            if x0 < x1:
                self._operational = (x0, x1)
            else:
                self._operational = (x1, x0)
        else:
            if 0. < x0:
                self._operational = (0., x0)
            else:
                self._operational = (x0, 0.)

    @property
    def tolerated(self) -> Tuple[float, float]:
        return self._tolerated

    @tolerated.setter
    def tolerated(self, value: Union[float, Sequence[float]]) -> None:
        value = np.atleast_1d(value)
        if len(value) >= 1:
            x0 = float(value[0])
        else:
            x0 = 0.
        if len(value) >= 2:
            x1 = float(value[1])
            if x0 < x1:
                self._tolerated = (x0, x1)
            else:
                self._tolerated = (x1, x0)
        else:
            if 0. < x0:
                self._tolerated = (0., x0)
            else:
                self._tolerated = (x0, 0.)
    @property
    def expected(self) -> Tuple[float, float]:
        return self._expected

    @expected.setter
    def expected(self, value: Union[float, Sequence[float]]) -> None:
        value = np.atleast_1d(value)
        if len(value) >= 1:
            x0 = float(value[0])
        else:
            x0 = 0.
        if len(value) >= 2:
            x1 = float(value[1])
            if x0 < x1:
                self._expected = (x0, x1)
            else:
                self._expected = (x1, x0)
        else:
            if 0. < x0:
                self._expected = (0., x0)
            else:
                self._expected = (x0, 0.)

    def __str__(self) -> str:
        s = '\n{'
        d = OrderedDict(sorted(self.__dict__.items()))
        for key, val in d.items():
            s += "  '" + key + "': "
            if isinstance(val, str):
                s += "'" + str(val) + "'"
            elif isinstance(val, types.FunctionType):
                c = ''
                for x in inspect.getsourcelines(val)[0]:
                    c += str(x).strip()
                c = c[c.index('=')+2:]
                c = c.replace('\\', '')
                c = c.replace('+ ', '+').replace(' +', '+')
                c = c.replace('- ', '-').replace(' -', '-')
                c = c.replace('* ', '*').replace(' *', '*')
                c = c.replace('/ ', '/').replace(' /', '/')
                s += c
            else:
                s += str(val)
            s += ',\n '
        s += '}'
        return s