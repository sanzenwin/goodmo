import ret_code
import KBEngine
from pymysql.converters import escape_str


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


class DatabaseBaseMixin:
    tableStr = "tbl_%s"
    assignmentStr = "sm_%s = %s"
    sqlUpdateStr = "update %s set %s where %s;"
    sqlInsertStr = "insert into %s (%s) values(%s);"

    @classmethod
    def __table(cls):
        return cls.tableStr % cls.__name__

    @classmethod
    def __assignment(cls, m):
        assignment = []
        for k, v in m.items():
            v = escape_str(v) if isinstance(v, str) else v
            assignment.append(cls.assignmentStr % (k, v))
        return assignment

    @classmethod
    def __updateSql(cls, m, n):
        table = cls.__table()
        assignment = " , ".join(cls.__assignment(m))
        condition = " and ".join(cls.__assignment(n))
        return cls.sqlUpdateStr % (table, assignment, condition)

    @classmethod
    def __insertSql(cls, m):
        kk = []
        vv = []
        for k, v in m.items():
            v = escape_str(v) if isinstance(v, str) else v
            kk.append(k)
            vv.append(v)
        table = cls.__table()
        return cls.sqlInsertStr % (table, " , ".join(kk), " , ".join(vv))

    @classmethod
    def executeDatabaseUpdate(cls, assignment, condition, callback=None, threadID=-1):
        KBEngine.executeRawDatabaseCommand(cls.__updateSql(assignment, condition), callback, threadID,
                                           cls.dbInterfaceName)

    @classmethod
    def executeDatabaseInsert(cls, insert, callback=None, threadID=-1):
        KBEngine.executeRawDatabaseCommand(cls.__insertSql(insert), callback, threadID, cls.dbInterfaceName)
