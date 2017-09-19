from common.dispatcher import Signal

avatar_newbie = Signal(providing_args=['newbieData'])
avatar_created = Signal()

avatar_common_login = Signal()
avatar_quick_login = Signal()
avatar_login = Signal()

avatar_logout = Signal()

avatar_modify = Signal(providing_args=['key', 'value'])
avatar_modify_multi = Signal(providing_args=['data'])

avatar_consume = Signal(providing_args=['data'])
