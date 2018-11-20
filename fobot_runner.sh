#!/usr/bin/env bash
if pgrep -f "SCREEN -S runner_bot_fobot -d -m ./start.sh" > /dev/null
then
    echo "There is Already an instance of fobot_runner plase stop first"
else
screen -S runner_bot_fobot -d -m ./start.sh
fi