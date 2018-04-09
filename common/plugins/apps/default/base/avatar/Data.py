# -*- coding: utf-8 -*-
from kbe.protocol import Property, Type
from common.utils import SteadyData, TodayData, WeekData, MonthData, YearData, ExpiredData


class Data:
    _steadyData = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE,
        Default={},
        Persistent=Property.Persistent.true
    )

    _todayData = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE,
        Default={},
        Persistent=Property.Persistent.true
    )

    _weekData = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE,
        Default={},
        Persistent=Property.Persistent.true
    )

    _monthData = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE,
        Default={},
        Persistent=Property.Persistent.true
    )

    _yearData = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE,
        Default={},
        Persistent=Property.Persistent.true
    )

    def __init__(self):
        super().__init__()
        self.steadyData = SteadyData(self._steadyData)
        self.todayData = TodayData(self._todayData)
        self.weekData = WeekData(self._weekData)
        self.monthData = MonthData(self._monthData)
        self.yearData = YearData(self._yearData)
        self.onlineData = ExpiredData({})

    def modifySteadyData(self, method, key, value=None):
        getattr(self.steadyData, method)(key, value)

    def modifyDateData(self, t, method, key, value=None, expired=None):
        obj = getattr(self, "%sData" % t)
        getattr(obj, method)(key, value, expired)
