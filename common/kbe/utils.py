class TimerProxy(object):
    DEFAULT_TIMER_ID = -1

    def __init__(self):
        super().__init__()
        self.__timer__ = {}

    def addTimerProxy(self, initialOffset, callbackObj, repeatOffset=0):
        timerID = self.addTimer(initialOffset, repeatOffset, self.DEFAULT_TIMER_ID)
        self.__timer__[timerID] = [repeatOffset <= 0, callbackObj]
        return timerID

    def delTimerProxy(self, timerID):
        self.__timer__.pop(timerID, None)
        self.delTimer(timerID)

    def onTimer(self, tid, userArg):
        if userArg == self.DEFAULT_TIMER_ID:
            self.__timer__[tid][-1]()
            if self.__timer__.get(tid, [False])[0]:
                self.__timer__.pop(tid, None)
