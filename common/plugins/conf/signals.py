from common.dispatcher import Signal

plugins_completed = Signal()
change_newbie_data = Signal(providing_args=['data'])
