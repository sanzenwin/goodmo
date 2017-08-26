# -*- coding: utf-8 -*-
import settings
from kbe.protocol import Property, Volatile, Type, Base, BaseMethod, BaseMethodExposed, Client, ClientMethod
from common.utils import ExpiredData, TodayData, WeekData, MonthData, YearData
from kbe.utils import LockAsset


class Asset(LockAsset("gold")):
    name = Property(
        Type=Type.UNICODE,
        Flags=Property.Flags.BASE_AND_CLIENT,
        # Index=Property.Index.UNIQUE,
        DatabaseLength=settings.Avatar.nameLimit,
        Persistent=Property.Persistent.true
    )

    gold = Property(
        Type=Type.GOLD,
        Flags=Property.Flags.BASE_AND_CLIENT,
        Persistent=Property.Persistent.true
    )

    avatarUrl = Property(
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
