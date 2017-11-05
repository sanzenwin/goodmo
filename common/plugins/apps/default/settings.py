# coding:utf-8
from plugins.conf import Str, SettingsNode, SettingsEntity, EqualizationMixin


class PlayerManager(SettingsEntity, EqualizationMixin):
    equalization__mod_base = 1

    def equalization_list(self):
        return [[i] for i in range(self.equalization__mod_base)]

    def equalization(self, guarantee_id):
        return [self.mod(guarantee_id, self.equalization__mod_base)]


class Account(SettingsEntity):
    avatarTotalLimit = 1
    removeAvatarEnabled = False
    type = ("tourist", "email", "phone", "weixin", "qq", "weibo",)
    needWebAuth = True
    url = SettingsNode(
        authUser=r"http://127.0.0.1:8000/account/auth_user/",
        editUser=r"http://127.0.0.1:8000/account/edit_user/",
        operateUser=r"http://127.0.0.1:8000/account/operate_user/",
        verify=r"http://127.0.0.1:8000/account/verify/",
        emailCode=r"http://127.0.0.1:8000/account/email_code/",
        phoneCode=r"http://127.0.0.1:8000/account/phone_code/",
        syncData=r"http://127.0.0.1:8000/account/sync_data/",
        openUrl=r"http://127.0.0.1:8000/account/open_url/",
    )


class Avatar(SettingsEntity):
    namePrefix = "玩家"
    nameIndexRadix = 15682357
    delayDestroySeconds = 5 * 60
    nameLengthUpLimit = 20
    gold64 = False
    uploadSizeUpLimit = 2 ** 10 ** 2  # 1Mb
    newbieData = SettingsNode(gold=0)


class Guarantee(SettingsEntity):
    delayDestroySeconds = 5 * 60


class RetCode(SettingsNode):
    ACCOUNT_CREATE_AVATAR_TOP_LIMIT = Str("角色数目已达到上限，无法创建新的角色")
    ACCOUNT_REMOVE_AVATAR_FAILED = Str("未开放删除角色功能")

    GOLD_LACK = Str("金币不足")
    GOLD_LOCKED = Str("金币已经锁定，其他操作未完成")

    ASSET_LACK = Str("资源不足")
    ASSET_LOCKED = Str("资源已经锁定，其他操作未完成")

    ARGS_ERROR = Str("参数错误")
