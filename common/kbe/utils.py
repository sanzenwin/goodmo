import ret_code


class TimerProxy:
    DEFAULT_TIMER_ID = -1

    def __init__(self):
        super().__init__()
        self.__timer__ = {}

    def addTimerProxy(self, initialOffset, callback, repeatOffset=0):
        timerID = self.addTimer(initialOffset, repeatOffset, self.DEFAULT_TIMER_ID)
        self.__timer__[timerID] = [repeatOffset <= 0, callback]
        return timerID

    def delTimerProxy(self, timerID):
        self.__timer__.pop(timerID, None)
        self.delTimer(timerID)

    def onTimer(self, tid, userArg):
        if userArg == self.DEFAULT_TIMER_ID:
            callback = self.__timer__[tid][-1]
            if self.__timer__.get(tid, [False])[0]:
                self.__timer__.pop(tid, None)
            callback()


def LockAsset(*nameList):
    class Asset:
        def lockAsset(self, name):
            setattr(self, get_lockedPropertyName(name), True)

        def isAssetLocked(self, name):
            return getattr(self, get_lockedPropertyName(name), True)

        def modifyAsset(self, name, changed, unlock=True):
            if unlock:
                setattr(self, get_lockedPropertyName(name), False)
            if changed == 0:
                return
            v = getattr(self, name) + changed
            setattr(self, name, max(0, v))

        def asset(self, name):
            return getattr(self, name, 0)

        def assetLockedCode(self, name):
            return getattr(ret_code, name.upper() + "_LOCKED", ret_code.ASSET_LOCKED)

        def assetLackCode(self, name):
            return getattr(ret_code, name.upper() + "_LACK", ret_code.ASSET_LACK)

    def get_lockedPropertyName(name):
        return "__" + name + "Locked"

    def get_lockedGetMethodName(name):
        return "is" + name.capitalize() + "Locked"

    def get_lockMethodName(name):
        return "lock" + name.capitalize()

    def get_modifyMethodName(name):
        return "modify" + name.capitalize()

    def generator(name):
        lockedPropertyName = get_lockedPropertyName(name)
        lockedGetMethodName = get_lockedGetMethodName(name)
        lockMethodName = get_lockMethodName(name)
        modifyMethodName = get_modifyMethodName(name)

        def lock(self):
            setattr(self, lockedPropertyName, True)

        def isLocked(self):
            return getattr(self, lockedPropertyName)

        def modify(self, changed, unlock=True):
            if unlock:
                setattr(self, lockedPropertyName, False)
            if changed == 0:
                return
            v = getattr(self, name) + changed
            setattr(self, name, max(0, v))

        return type("lock_" + name, (object,), {
            lockedPropertyName: False,
            lockedGetMethodName: isLocked,
            lockMethodName: lock,
            modifyMethodName: modify
        })

    assert len(nameList) == len(set(nameList)), "The name of assets should be unique"
    return type("set__" + "_".join(nameList), (Asset,) + tuple(generator(name) for name in nameList), {})
