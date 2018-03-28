from kbe.protocol import Type, Property, Client, ClientMethod, Base, BaseMethodExposed


class RobotBackend:
    robotMark = Property(
        Type=Type.BOOL,
        Flags=Property.Flags.BASE,
        Persistent=Property.Persistent.true
    )
