#!/bin/bash

CHANNEL_ID="e2342e61-2926-44ec-9e75-7e8e815a7f5c"
URL="http://localhost:5174/get_message?channel_id=$CHANNEL_ID"

while true; do
  curl -s "$URL"
  sleep 1  # Optional: add delay to reduce request spamming
done

