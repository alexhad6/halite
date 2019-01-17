#!/bin/sh

./halite --replay-directory replays/ -vvv --width 2 --height 2 "python3 MyBot.py" "python3 Opponent.py"
