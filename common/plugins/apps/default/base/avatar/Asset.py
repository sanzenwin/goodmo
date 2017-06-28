# -*- coding: utf-8 -*-
from kbe.protocol import Property, Volatile, Type, Base, BaseMethod, BaseMethodExposed, Client, ClientMethod
from common.utils import ExpiredData, TodayData, WeekData, MonthData, YearData


class Asset:
    name = Property(
        Type=Type.UNICODE,
        Flags=Property.Flags.BASE_AND_CLIENT,
        Index=Property.Index.UNIQUE,
        DatabaseLength=20,
        Persistent=Property.Persistent.true
    )

    gold = Property(
        Type=Type.GOLD,
        Flags=Property.Flags.BASE_AND_CLIENT,
        Persistent=Property.Persistent.true
    )

    avatarCode = Property(
        Type=Type.UNICODE,
        Flags=Property.Flags.BASE_AND_CLIENT,
        Persistent=Property.Persistent.true
    )

    data = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE,
        Default={},
        Persistent=Property.Persistent.true
    )

    def __init__(self):
        super().__init__()

    def modifyName(self, changed):
        self.name = changed

    def modifyGold(self, changed):
        gold = self.gold + changed
        self.gold = max(0, gold)
