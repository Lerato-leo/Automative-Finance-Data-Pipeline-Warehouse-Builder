#!/bin/bash
LOGFILE="logs/notify.log"
mkdir -p logs
STATUS=$1
MESSAGE=$2
if [ "$STATUS" == "success" ]; then
    echo "$(date) SUCCESS: $MESSAGE" >> $LOGFILE
else
    echo "$(date) FAILURE: $MESSAGE" >> $LOGFILE
fi
# Optionally: integrate with AWS SNS, Slack, or email
