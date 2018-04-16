from common.dispatcher import Signal

database_completed = Signal()
redis_completed = Signal()
mongodb_completed = Signal()

baseapp_ready = Signal()
baseapp_completed = Signal()

global_data_change = Signal(providing_args=['key', 'value'])
global_data_del = Signal(providing_args=['key'])

entity_auto_load_completed = Signal()
