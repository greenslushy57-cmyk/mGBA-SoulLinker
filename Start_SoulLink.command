#!/bin/bash
cd "$(dirname "$0")"

if [ -x "/opt/homebrew/bin/python3" ]; then
    PY="/opt/homebrew/bin/python3"
elif [ -x "/usr/local/bin/python3" ]; then
    PY="/usr/local/bin/python3"
elif [ -x "/Library/Frameworks/Python.framework/Versions/Current/bin/python3" ]; then
    PY="/Library/Frameworks/Python.framework/Versions/Current/bin/python3"
else
    PY="python3"
fi

"$PY" launch_soullink.py