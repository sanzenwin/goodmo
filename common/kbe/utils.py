import ret_code
import KBEngine
from common.utils import server_time
from pymysql.converters import escape_str


class TimerProxy:
    DEFAULT_TIMER_ID = -1

    def __init__(self):
        super().__init__()
        self.__timer__ = {}

    def getTimerProxy(self, callback):
        return next((tid for tid, (_, call) in self.__timer__.items() if call is callback), None)

    def addTimerProxy(self, initialOffset, callback, repeatOffset=0):
        timerID = self.addTimer(initialOffset, repeatOffset, self.DEFAULT_TIMER_ID)
        self.__timer__[timerID] = [repeatOffset <= 0, callback]
        return timerID

    def delTimerProxy(self, timerID):
        timer = self.__timer__.pop(timerID, None)
        if timer is not None:
            self.delTimer(timerID)

    def clearTimerProxy(self):
        for tid in list(self.__timer__):
            self.delTimerProxy(tid)

    def onTimer(self, tid, userArg):
        if userArg == self.DEFAULT_TIMER_ID:
            callback = self.__timer__[tid][-1]
            if self.__timer__.get(tid, [False])[0]:
                del self.__timer__[tid]
            callback()

    def runInNextFrame(self, callback):
        self.addTimerProxy(0, callback)


def assetLockedCode(name):
    return getattr(ret_code, name.upper() + "_LOCKED", ret_code.ASSET_LOCKED)


def assetLackCode(name):
    return getattr(ret_code, name.upper() + "_LACK", ret_code.ASSET_LACK)


def LockAsset(*nameList):
    class Asset:
        def lockAsset(self, name):
            setattr(self, get_lockedPropertyName(name), True)

        def isAssetLocked(self, name):
            return getattr(self, get_lockedPropertyName(name), True)

        def isAsset(self, name):
            if not hasattr(self, "_lock_asset_name_set"):
                s = self._lock_asset_name_set = set()
                for c in self.mro():
                    s.update(c.__dict__.get("__lock_asset_name_set__", set()))
            return name in self._lock_asset_name_set

        def modifyAsset(self, name, changed, unlock=True):
            if unlock:
                setattr(self, get_lockedPropertyName(name), False)
            if changed == 0:
                return
            v = max(0, getattr(self, name) + changed)
            setattr(self, name, v)
            self.onModifyAttr(name, v)

        def asset(self, name):
            return getattr(self, name, 0)

        @staticmethod
        def assetLockedCode(name):
            return assetLockedCode(name)

        @staticmethod
        def assetLackCode(name):
            return assetLackCode(name)

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
            v = max(0, getattr(self, name) + changed)
            setattr(self, name, v)
            self.onModifyAttr(name, v)

        return type("lock_" + name, (object,), {
            lockedPropertyName: False,
            lockedGetMethodName: isLocked,
            lockMethodName: lock,
            modifyMethodName: modify
        })

    assert len(nameList) == len(set(nameList)), "The name of assets should be unique"
    return type("set__" + "_".join(nameList), (Asset,) + tuple(generator(name) for name in nameList),
                dict(__lock_asset_name_set__=set(nameList)))


class DatabaseBaseMixin:
    tableStr = "tbl_%s"
    fieldStr = "sm_%s"
    assignmentStr = fieldStr + " = %s"
    assignmentOriginStr = "%s = %s"
    sqlUpdateStr = "update %s set %s where %s;"
    sqlInsertStr = "insert into %s (%s) values(%s);"

    @classmethod
    def __table(cls):
        return cls.tableStr % cls.__name__

    @classmethod
    def __field(cls, m):
        return m if m == "id" else (cls.fieldStr % m)

    @classmethod
    def __assignment(cls, m):
        assignment = []
        for k, v in m.items():
            v = escape_str(v) if isinstance(v, str) else v
            a = cls.assignmentOriginStr if k == "id" else cls.assignmentStr
            assignment.append(a % (k, v))
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
            v = escape_str(v) if isinstance(v, str) else str(v)
            kk.append(cls.__field(k))
            vv.append(v)
        table = cls.__table()
        return cls.sqlInsertStr % (table, " , ".join(kk), " , ".join(vv))

    @classmethod
    def executeDatabaseUpdate(cls, assignment, condition, callback=None, threadID=-1):
        if assignment and condition:
            KBEngine.executeRawDatabaseCommand(cls.__updateSql(assignment, condition), callback, threadID,
                                               cls.dbInterfaceName)

    @classmethod
    def executeDatabaseInsert(cls, insert, callback=None, threadID=-1):
        if insert:
            KBEngine.executeRawDatabaseCommand(cls.__insertSql(insert), callback, threadID, cls.dbInterfaceName)


def internal_ip_address():
    return ".".join(reversed(list(map(str, KBEngine.address()[0].to_bytes(4, 'big')))))


def generate_pk():
    return "%s%s" % (KBEngine.genUUID64(), server_time.stamp())
