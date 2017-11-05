import os


class ShellMaker:
    class Default(dict):
        def __missing__(self, key):
            return "{%s}" % key

    cmd_template = """\
@echo off

cd ../..
set curpath=%cd%

cd ..
set KBE_ROOT=%cd%
set KBE_RES_PATH=%KBE_ROOT%/kbe/res/;%curpath%/;%curpath%/res/;%curpath%/scripts/
set KBE_BIN_PATH=%KBE_ROOT%/kbe/bin/server/

if defined uid (echo UID = {uid}) else (echo must set UID && pause)

cd %curpath%
{kill}

echo KBE_ROOT = %KBE_ROOT%
echo KBE_RES_PATH = %KBE_RES_PATH%
echo KBE_BIN_PATH = %KBE_BIN_PATH%

{apps}
"""

    cmd_template_telnet = """\
set temp_vbs=telent_goodmo_%random%.vbs
@del %temp%\%temp_vbs%
@echo on error resume next >>%temp%\%temp_vbs%
@echo dim WshShell>>c:\%temp_vbs%
@echo Set WshShell = WScript.CreateObject("WScript.Shell")>>%temp%\%temp_vbs%
@echo WshShell.run"cmd">>c:\%temp_vbs%
@echo WshShell.AppActivate"c:\windows\system32\cmd.exe">>%temp%\%temp_vbs%
@echo WScript.Sleep 200>>%temp%\%temp_vbs%
@echo WshShell.SendKeys "telnet {ip} {port}">>%temp%\%temp_vbs%
@echo WshShell.SendKeys"{ENTER}">>%temp%\%temp_vbs%
@echo WScript.Sleep 100>>%temp%\%temp_vbs%
@echo WshShell.SendKeys"{password}">>%temp%\%temp_vbs%
@echo WshShell.SendKeys"{ENTER}">>%temp%\%temp_vbs%
@echo WScript.Sleep 100>>%temp%\%temp_vbs%
@echo WshShell.SendKeys"{ENTER}">>%temp%\%temp_vbs%
@echo WScript.Sleep 100>>%temp%\%temp_vbs%
@echo WshShell.SendKeys"{ENTER}">>%temp%\%temp_vbs%
@echo WScript.Sleep 100>>%temp%\%temp_vbs%
@echo WshShell.SendKeys"{ENTER}">>%temp%\%temp_vbs%
@echo WScript.Sleep 100>>%temp%\%temp_vbs%
@echo WshShell.SendKeys"{ENTER}">>%temp%\%temp_vbs%
@start cmd
@call %temp%\%temp_vbs%"""

    cmd_kill_str = 'call "scripts/shell/kill_server"'

    app_cmd_template = """start %KBE_BIN_PATH%/{app}.exe --cid={cid} --gus={gus}"""

    sh_template = """\
#!/bin/bash

cd ../../
export uid={uid}
export KBE_ROOT=$(cd ../; pwd)
export KBE_ASSERT_PATH=$(cd .; pwd)
export KBE_RES_PATH="$KBE_ROOT/kbe/res/:$KBE_ASSERT_PATH/:$KBE_ASSERT_PATH/res/:$KBE_ASSERT_PATH/scripts/"
export KBE_BIN_PATH="$KBE_ROOT/kbe/bin/server/"

echo UID = {uid}
echo KBE_ROOT = \"${KBE_ROOT}\"
echo KBE_RES_PATH = \"${KBE_RES_PATH}\"
echo KBE_BIN_PATH = \"${KBE_BIN_PATH}\"

{kill}

{apps}
"""

    sh_template_telnet = """\
#!/usr/bin/expect
spawn telnet {ip} {port}
send {password}\\r
interact
"""

    sh_kill_str = 'sh ./scripts/shell/kill_server.sh'

    app_sh_template = """$KBE_BIN_PATH/{app} --cid={cid} --gus={gus}&"""

    apps = (
        "machine", "logger", "interfaces", "dbmgr", "baseappmgr", "cellappmgr", "loginapp", "baseapp", "cellapp", "bots"
    )

    def __init__(self):
        self.origin_cid = 10000
        self.origin_gus = 0

    def new_cid(self):
        self.origin_cid += 1
        return self.origin_cid

    def new_gus(self):
        self.origin_gus += 1
        return self.origin_gus

    def app_shell(self, name, cmd=True):
        app_template = self.app_cmd_template if cmd else self.app_sh_template
        return app_template.format(app=name, cid=self.new_cid(), gus=self.new_gus())

    def apps_shell(self, name_dict, kill=True, cmd=True):
        apps = []
        template = self.cmd_template if cmd else self.sh_template
        kill_str = (self.cmd_kill_str if cmd else self.sh_kill_str) if kill else ""
        for name in sorted(name_dict, key=lambda x: self.apps.index(x)):
            for i in range(name_dict[name]):
                apps.append(self.app_shell(name, cmd))
        return template.format_map(
            self.Default(apps=("\r\n" if cmd else "\n").join(apps), kill=kill_str, uid=os.getenv("uid")))

    def app_telnet_shell(self, data, cmd=True):
        app_template = self.cmd_template_telnet if cmd else self.sh_template_telnet
        return app_template.format_map(self.Default(**data))


shell_maker = ShellMaker()
