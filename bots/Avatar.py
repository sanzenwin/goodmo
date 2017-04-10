# -*- coding: utf-8 -*-
import KBEngine
from kbe.log import DEBUG_MSG, ERROR_MSG
from game.manager import manager
from ROOM import TEnterRoomData, TEvent, TBoardData, TRoomInfo
from RANK_ROOM import TRankRooms


class Room(object):
    def __init__(self):
        self.reset()

    def __str__(self):
        return "members: %s\nseats: %s" % (self.members, self.seats)

    def reset(self):
        self.hallID = 0
        self.roomID = 0
        self.members = {}
        self.seats = {}
        self.prepares = {}
        self.board = None

    def setup(self, roomInfo):
        self.reset()
        self.hallID = roomInfo.hallID
        self.roomID = roomInfo.roomID
        self.board = manager.get_board(self.hallID)(None)
        for member in roomInfo.members:
            self.members[member.id] = dict(
                guaranteeID=member.guaranteeID,
                name=member.name,
                hall=member.hall,
            )
        for i, avatarID in enumerate(roomInfo.seats):
            if avatarID:
                self.seats[avatarID] = i
        for i, x in enumerate(roomInfo.prepares):
            avatarID = roomInfo.seats[i]
            if avatarID:
                self.prepares[avatarID] = x

    def setupStartInfo(self, roomStartInfo):
        self.board = manager.get_board(self.hallID)(None)
        for i, avatarID in enumerate(roomStartInfo.seats):
            if avatarID:
                self.seats[avatarID] = i

    def enter(self, data):
        member = data.member
        self.members[member.id] = dict(
            guaranteeID=member.guaranteeID,
            name=member.name,
            hall=member.hall,
        )
        self.seats[member.id] = data.seat

    def leave(self, id_):
        self.members.pop(id_, None)
        self.seats.pop(id_, None)
        self.prepares.pop(id_, None)

    def isInRoom(self, id_):
        return id_ in self.members


class Handler(object):
    def __init__(self):
        self.handlers = {}

    def __call__(self, hallID):
        def wrapper(cls):
            self.handlers[hallID] = cls
            return cls
        return wrapper

    def get(self, hallID):
        return self.handlers[hallID]

handler = Handler()


class BoardHandler(object):
    def __init__(self, room):
        self.room = room

    def move(self, move):
        pass

    def undo_move(self):
        pass


@handler(10002)
class CchessHandler(BoardHandler):
    def move(self, move):
        self.room.board.position.move(*self.room.board.decode_move(move))
        self.room.board.record.add(move)

    def undo_move(self):
        self.room.board.record.pop()
        self.room.board.position.undo_move()


@handler(20001)
class DchessHandler(BoardHandler):
    def move(self, move):
        fx, fy, tx, ty = self.room.board.decode_move(move)
        if fx == 8:
            self.room.board.flip2(tx, ty, fy)
        else:
            self.room.board.move(fx, fy, tx, ty)
        self.room.board.record.add(move)
        self.room.board.next_turn()


@handler(30001)
class IchessHandler(BoardHandler):
    def move(self, move):
        pre_state = self.room.board.move(*self.room.board.decode_move(move))
        self.room.board.record.add((move, pre_state))
        self.room.board.next_turn()

    def undo_move(self):
        _, pre_state = self.room.board.record.pop()
        self.room.board.undo_move(pre_state)
        self.room.board.next_turn()


@handler(40001)
class OthelloHandler(BoardHandler):
    def move(self, move):
        track_list = self.room.board.move(*self.room.board.decode_move(move))
        self.room.board.record.add((move, track_list))
        self.room.board.next_turn()

    def undo_move(self):
        move, track_list = self.room.board.record.pop()
        x, y = self.room.board.decode_move(move)
        self.room.board.undo_move(track_list, x, y)
        self.room.board.next_turn()

    def pass_move(self, turn):
        self.room.board.next_turn()


@handler(50001)
class GomokuHandler(BoardHandler):
    def move(self, move):
        self.room.board.move(*self.room.board.decode_move(move))
        self.room.board.record.add(move)
        self.room.board.next_turn()

    def undo_move(self):
        self.room.board.record.pop()
        self.room.board.undo_move()
        self.room.board.next_turn()


@handler(60001)
class GobanHandler(BoardHandler):
    def move(self, move):
        track_list = self.room.board.move(*self.room.board.decode_move(move))
        self.room.board.record.add((move, track_list))
        self.room.board.next_turn()

    def undo_move(self):
        move, track_list = self.room.board.record.pop()
        x, y = self.room.board.decode_move(move)
        self.room.board.undo_move(track_list, x, y)
        self.room.board.next_turn()


class Avatar(KBEngine.Entity):
    hallID = 0
    interval = (0, 0)

    def __init__(self):
        super(Avatar, self).__init__()
        self.is_over = True
        self.callback_id = 0
        self.room = Room()
        self.init_hall()
        self.handler = handler.get(self.hallID)(self.room)

        def match():
            self.base.reqEnterMatch(self.hallID)
        KBEngine.callback(3, match)

    def init_hall(self):
        self.hallID = 10002

    def onEnterSpace(self):
        """
        KBEngine method.
        这个entity进入了一个新的space
        """
        DEBUG_MSG("%s::onEnterSpace: %i" % (self.__class__.__name__, self.id))

    def onLeaveSpace(self):
        """
        KBEngine method.
        这个entity将要离开当前space
        """
        DEBUG_MSG("%s::onLeaveSpace: %i" % (self.__class__.__name__, self.id))

    def onBecomePlayer(self):
        """
        KBEngine method.
        当这个entity被引擎定义为角色时被调用
        """
        DEBUG_MSG("%s::onBecomePlayer: %i" % (self.__class__.__name__, self.id))

    def onLogOnAttempt(self, isSelf, ip):
        DEBUG_MSG("%s::onLogOnAttempt: %i, %s, %s" % (self.__class__.__name__, self.id, isSelf, ip))

    def onRetCode(self, retCode):
        ERROR_MSG("%s::onRetCode: %i, %i" % (self.__class__.__name__, self.id, retCode))

    def onEnterRoomAuthFailed(self):
        ERROR_MSG("%s::onEnterRoomAuthFailed: %i" % (self.__class__.__name__, self.id))

    def onEnterMatch(self, hallID):
        DEBUG_MSG("%s::onEnterMatch: %i, %s" % (self.__class__.__name__, self.id, hallID))

    def onLeaveMatch(self):
        DEBUG_MSG("%s::onLeaveRoom: %i" % (self.__class__.__name__, self.id))

    def onRankRoomList(self, rankRooms):
        DEBUG_MSG("%s::onRankRoomList: %i, %s" % (self.__class__.__name__, self.id, rankRooms))
        rankRooms = TRankRooms().createFromRecursionDict(rankRooms)

    def onReceiveRoom(self, roomInfo):
        DEBUG_MSG("%s::onReceiveRoom: %i, %s" % (self.__class__.__name__, self.id, roomInfo))
        self.room.setup(TRoomInfo().createFromRecursionDict(roomInfo))
        self.send_event('prepare', True)

    def onRoomReceiveEvent(self, event):
        DEBUG_MSG("%s::onRoomReceiveEvent: %i, %s" % (self.__class__.__name__, self.id, event))
        event = TEvent().createFromRecursionDict(event)
        action, args = event.func, event.param
        action_method = getattr(self, 'event__' + action)
        action_method(*args)

    def event__prepare(self, avatarID, x):
        DEBUG_MSG("%s::event__prepare: %i, %s, %s" % (self.__class__.__name__, self.id, avatarID, x))
        self.room.prepares[avatarID] = bool(x)
        if all(self.room.prepares.values()) and len(self.room.prepares) == 2 and self.room.seats[self.id] == 0:
            self.send_event('config', [0, 0, 1])

    def event__config(self, data):
        ERROR_MSG("%s::event__config: %i, %s" % (self.__class__.__name__, self.id, data))
        if self.room.seats[self.id] != 0:
            self.send_event('rsp_config')

    def onRoomStart(self, boardData):
        DEBUG_MSG("%s::onRoomStart: %i, %s" % (self.__class__.__name__, self.id, boardData))
        self.is_over = False
        self.room.board.reset()
        boardData = TBoardData().createFromRecursionDict(boardData)
        if self.room.seats[self.id] == len(boardData.moves) % 2:
            self.timer_random_move()

    def onEnterRoom(self, enterRoomData):
        DEBUG_MSG("%s::onEnterRoom: %i, %s" % (self.__class__.__name__, self.id, enterRoomData))
        enterRoomData = TEnterRoomData().createFromRecursionDict(enterRoomData)
        self.room.enter(enterRoomData)

    def onLeaveRoom(self, avatarID, code):
        DEBUG_MSG("%s::onLeaveRoom: %i, %s, %s" % (self.__class__.__name__, self.id, avatarID, code))
        self.room.leave(avatarID)
        if self.id == avatarID:
            self.base.reqEnterMatch(self.hallID)

    def onRoomLoginIn(self, avatarID):
        DEBUG_MSG("%s::onRoomLoginIn: %i, %s" % (self.__class__.__name__, self.id, avatarID))

    def onRoomLoginOut(self, avatarID):
        DEBUG_MSG("%s::onRoomLoginOut: %i, %s" % (self.__class__.__name__, self.id, avatarID))

    def onRoomWatchers(self, memberList):
        DEBUG_MSG("%s::onRoomWatchers: %i, %s" % (self.__class__.__name__, self.id, memberList))

    def onRoomWatchersCount(self, count):
        DEBUG_MSG("%s::onRoomWatchersCount: %i, %s" % (self.__class__.__name__, self.id, count))

    def onFollow(self, avatarID):
        DEBUG_MSG("%s::onFollow: %i, %s" % (self.__class__.__name__, self.id, avatarID))

    def onUnollow(self, avatarID):
        DEBUG_MSG("%s::onFollow: %i, %s" % (self.__class__.__name__, self.id, avatarID))

    def onFollowing(self, avatarInfoList):
        DEBUG_MSG("%s::onFollow: %i, %s" % (self.__class__.__name__, self.id, avatarInfoList))

    def onFollower(self, avatarInfoList):
        DEBUG_MSG("%s::onFollow: %i, %s" % (self.__class__.__name__, self.id, avatarInfoList))

    def onFriend(self, avatarInfoList):
        DEBUG_MSG("%s::onFollow: %i, %s" % (self.__class__.__name__, self.id, avatarInfoList))

    def send_event(self, *eventContent):
        event = TEvent()
        event.func = eventContent[0]
        event.param = eventContent[1:]
        self.base.reqRoomEvent(event.asDict())

    def random_move(self):
        move = self.room.board.random_move()
        if move is None:
            ERROR_MSG('move is None\nroom: %s, fen is %s' % (self.room.roomID, self.room.board.position.fen()))
            return
        self.send_event('move', move)

    def event__over(self, winner, reason, bills):
        DEBUG_MSG("winner is %s, reason is %s" % (winner, reason))
        self.is_over = True
        if self.callback_id:
            KBEngine.cancelCallback(self.callback_id)
            self.callback_id = 0

        def prepare():
            if self.room.isInRoom(self.id):
                self.send_event('prepare', True)
        import random
        KBEngine.callback(random.uniform(*self.interval), prepare)

    def event__move(self, avatarID, move, time_info):
        DEBUG_MSG("%s move is %s" % (avatarID, self.room.board.decode_move(move)))
        self.handler.move(move)
        if avatarID != self.id and not self.is_over:
            self.timer_random_move()

    def event__pass_move(self, turn):
        DEBUG_MSG("pass move turn %s" % turn)
        self.handler.pass_move(turn)
        if self.callback_id:
            KBEngine.cancelCallback(self.callback_id)
            self.callback_id = 0
        if len(self.room.board.moves) % 2 == self.room.seats[self.id]:
            self.timer_random_move()

    def timer_random_move(self):
        def random_move():
            if self.callback_id:
                self.callback_id = 0
            self.random_move()

        import random
        self.callback_id = KBEngine.callback(random.uniform(*self.interval), random_move)

    def event__req_peace(self, avatarID, peace_round):
        if self.id != avatarID:
            if self.callback_id:
                KBEngine.cancelCallback(self.callback_id)
                self.callback_id = 0
            self.send_event('rsp_peace')

    def event__req_undo_move(self, avatarID):
        if self.id != avatarID:
            if self.callback_id:
                KBEngine.cancelCallback(self.callback_id)
                self.callback_id = 0
            self.handler.undo_move()
            self.send_event('rsp_undo_move')

    def event__rsp_undo_move(self, avatarID, time_info):
        pass

    def event__time(self, time_info):
        pass


class PlayerAvatar(Avatar):
    def __init__(self):
        pass

    def onEnterSpace(self):
        """
        KBEngine method.
        这个entity进入了一个新的space
        """
        DEBUG_MSG("%s::onEnterSpace: %i" % (self.__class__.__name__, self.id))

        # 注意：由于PlayerAvatar是引擎底层强制由Avatar转换过来，__init__并不会再调用
        # 这里手动进行初始化一下
        self.__init__()

    def onLeaveSpace(self):
        """
        KBEngine method.
        这个entity将要离开当前space
        """
        DEBUG_MSG("%s::onLeaveSpace: %i" % (self.__class__.__name__, self.id))
