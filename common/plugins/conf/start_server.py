import KBEngine


class ShellMaker:
    cmd_template = """\
@echo off

cd ../..
set curpath=%cd%

cd ..
set KBE_ROOT=%cd%
set KBE_RES_PATH=%KBE_ROOT%/kbe/res/;%curpath%/;%curpath%/scripts/;%curpath%/res/
set KBE_BIN_PATH=%KBE_ROOT%/kbe/bin/server/

if defined uid (echo UID = %uid%) else set uid=%random%%%32760+1

cd %curpath%
call "scripts/shell/kill_server"

echo KBE_ROOT = %KBE_ROOT%
echo KBE_RES_PATH = %KBE_RES_PATH%
echo KBE_BIN_PATH = %KBE_BIN_PATH%

{apps}
"""

    app_cmd_template = """start %KBE_BIN_PATH%/%s.exe --cid=/%s --gus=%s"""

    sh_template = """\
#!/bin/sh

export KBE_ROOT=$(cd ../../; pwd)
export KBE_ASSERT_PATH=$(cd ../.; pwd)
export KBE_RES_PATH="$KBE_ROOT/kbe/res/:$KBE_ASSERT_PATH/:$KBE_ASSERT_PATH/res/:$KBE_ASSERT_PATH/scripts/"
export KBE_BIN_PATH="$KBE_ROOT/kbe/bin/server/"

echo KBE_ROOT = \"${KBE_ROOT}\"
echo KBE_RES_PATH = \"${KBE_RES_PATH}\"
echo KBE_BIN_PATH = \"${KBE_BIN_PATH}\"

sh ./kill_server.sh

{apps}
"""

    app_sh_template = """$KBE_BIN_PATH/%s --cid=%s --gus=%s&"""

    machine = "machine"
    logger = "logger"
    interfaces = "interfaces"
    dbmgr = "dbmgr"
    baseappmgr = "baseappmgr"
    cellappmgr = "cellappmgr"
    loginapp = "loginapp"
    baseapp = "baseapp"
    cellapp = "cellapp"
    bots = "bots"

    def __init__(self):
        self.origin_cid = KBEngine.genUUID64()
        self.origin_gus = KBEngine.genUUID64()

    def new_cid(self):
        self.origin_cid += 1
        return self.origin_cid

    def new_gus(self):
        self.origin_gus += 1
        return self.origin_gus

    def app_shell(self, name, cmd=True):
        app_template = self.app_cmd_template if cmd else self.app_sh_template
        return app_template % (getattr(self, name), self.new_cid(), self.new_gus())

    def apps_shell(self, name_dict, cmd=True):
        apps = []
        template = self.cmd_template if cmd else self.sh_template
        for name in sorted(name_dict):
            for i in range(name_dict[name]):
                apps.append(self.app_shell(name))
        return template.format(apps="\r\n".join(apps))


shell_maker = ShellMaker()
