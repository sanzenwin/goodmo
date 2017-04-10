# -*- coding: utf-8 -*-
from kbe.protocol import Property, Volatile, Type, Base, BaseMethod, BaseMethodExposed, Client, ClientMethod


class Asset(object):
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

    def modifyName(self, changed):
        self.name = changed

    def modifyGold(self, changed):
        gold = self.gold + changed
        self.gold = max(0, gold)
