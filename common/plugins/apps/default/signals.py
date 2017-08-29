from common.dispatcher import Signal

avatar_new = Signal(providing_args=['data', 'newbieData'])
avatar_login = Signal(providing_args=['data'])
consume_data = Signal(providing_args=['data'])
