#!/bin/bash

cd ../../
export KBE_ROOT=$(cd ../; pwd)
export KBE_ASSERT_PATH=$(cd .; pwd)
export KBE_RES_PATH="$KBE_ROOT/kbe/res/:$KBE_ASSERT_PATH/:$KBE_ASSERT_PATH/res/:$KBE_ASSERT_PATH/scripts/:$KBE_ASSERT_PATH/scripts/res/"
export KBE_BIN_PATH="$KBE_ROOT/kbe/bin/server/"

echo KBE_ROOT = \"${KBE_ROOT}\"
echo KBE_RES_PATH = \"${KBE_RES_PATH}\"
echo KBE_BIN_PATH = \"${KBE_BIN_PATH}\"

sh ./scripts/shell/kill_server.sh

export KBE_PLUGINS__AUTO_GENERATE="1"
export KBE_PLUGINS__ARGS=$*

$KBE_BIN_PATH/baseapp --cid=10001 --gus=1&
