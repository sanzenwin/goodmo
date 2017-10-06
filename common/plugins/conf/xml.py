import os
import random
import string
import collections
from copy import deepcopy


class Config:
    default = dict(
        gameUpdateHertz=60,
        publish=dict(
            state=0
        ),
        dbmgr=dict(
            databaseInterfaces=dict(
                default=dict(
                    auth=dict(
                        username="root",
                        password="123456",
                        encrypt="true"
                    ),
                    databaseName=""
                )
            )
        ),
        loginapp=dict(
            externalAddress=""
        ),
        baseapp=dict(
            externalAddress="",
            backupPeriod=500
        ),
        bots=dict(
            account_infos=dict(
                account_name_prefix="bot_",
                account_name_suffix_inc=1
            )
        )
    )

    telnet_service = dict(
        port=0,
        password="",
        default_layer="python"
    )

    telnet_apps = ("loginapp", "dbmgr", "interfaces", "logger", "baseapp", "cellapp", "bots")

    @staticmethod
    def check_dict(d):
        return isinstance(d, collections.Mapping)

    def update_recursive(self, d, u):
        for k, v in u.items():
            if self.check_dict(v) and self.check_dict(d.get(k)):
                self.update_recursive(d[k], v)
            else:
                d[k] = v
        return d

    @staticmethod
    def new_password(length=20):
        return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])

    @staticmethod
    def dict_path(data, path, default=None):
        lst = path.split(".")
        for key in lst:
            data = data.get(key, default)
            if data is default:
                break
        return data

    def get_default(self):
        return deepcopy(self.default)

    def get_default_with_telnet(self, one_password=True):
        password = self.new_password()
        port_start = random.randint(40000, 60000)
        port_step = random.randint(100, 1000)
        cfg = self.get_default()
        for index, app in enumerate(self.telnet_apps):
            port = port_start + port_step * index
            if not one_password:
                password = self.new_password()
            telnet = deepcopy(self.telnet_service)
            telnet.update(dict(port=port, password=password))
            cfg = self.update_recursive(cfg, {app: dict(telnet_service=telnet)})
        return cfg

    def final(self, data, encrypt_func):
        databases = self.dict_path(data, "dbmgr.databaseInterfaces", dict())
        for v in databases.values():
            name = v.get("databaseName")
            auth = v.get("auth")
            if name is not None:
                v["databaseName"] = "goodmo__%s__%s" % (os.getenv("uid"), name)
            if auth is not None:
                if auth.get("encrypt") == "true":
                    password = auth.get("password")
                    if password is not None:
                        auth["password"] = encrypt_func(password)
        return data


config = Config()
