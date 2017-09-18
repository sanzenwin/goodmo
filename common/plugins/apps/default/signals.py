from common.dispatcher import Signal

avatar_new = Signal(providing_args=['newbieData'])
avatar_created = Signal()
avatar_common_login = Signal()
avatar_quick_login = Signal()
avatar_login = Signal()

consume_data = Signal(providing_args=['data'])
