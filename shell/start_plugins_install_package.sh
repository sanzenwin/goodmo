#!/bin/sh

export KBE_ROOT=$(cd ../../../; pwd)
export KBE_ASSERT_PATH=$(cd ../../.; pwd)
export KBE_RES_PATH="$KBE_ROOT/kbe/res/:$KBE_ASSERT_PATH/:$KBE_ASSERT_PATH/res/:$KBE_ASSERT_PATH/scripts/"
export KBE_BIN_PATH="$KBE_ROOT/kbe/bin/server/"

echo KBE_ROOT = \"${KBE_ROOT}\"
echo KBE_RES_PATH = \"${KBE_RES_PATH}\"
echo KBE_BIN_PATH = \"${KBE_BIN_PATH}\"

sh ./kill_server.sh

export KBE_PLUGINS__INSTALL_THIRD_PACKAGE="1"

$KBE_BIN_PATH/baseapp --cid=10001 --gus=1&
