#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/libs
# 设置 XDG_DATA_HOME 以避免 CrewAI 在受限环境下的权限问题
export XDG_DATA_HOME=$(pwd)/.local/share
mkdir -p $XDG_DATA_HOME
# 禁用 CrewAI 遥测以避免在 Streamlit 线程中出现 signal 错误
export CREWAI_TELEMETRY_OPT_OUT=true
python3 -m streamlit run app.py --server.port 9527 --global.developmentMode=false
