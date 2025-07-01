#!/bin/bash

# Define the base URL and the channels
BASE_URL="http://localhost:5174/send_message"
CHANNEL_IDS=(
  "e2342e61-2926-44ec-9e75-7e8e815a7f5c"
  "5d6581c4-e928-44db-ab80-12e805434180"
  "6a6dc996-e2ad-4b27-9d4a-aa6c77532b24"
)

# Function to shuffle an array
shuffle() {
  local i tmp size max rand
  size=${#array[@]}
  max=$(( 32768 / size * size ))
  for ((i=size-1; i>0; i--)); do
    while (( (rand=RANDOM) >= max )); do :; done
    rand=$(( rand % (i+1) ))
    tmp=${array[i]} array[i]=${array[rand]} array[rand]=$tmp
  done
}

# Iterate over each channel
for channel_id in "${CHANNEL_IDS[@]}"; do
  # Create a message array
  array=("Msg 1" "Msg 2" "Msg 3" "Msg 4" "Msg 5")

  # Send messages in random order
  for msg in "${array[@]}"; do
    # URL-encode message
    msg_encoded=$(echo "$msg" | sed 's/ /%20/g')
    echo "Sending to channel $channel_id: $msg"
    curl "${BASE_URL}?channel_id=${channel_id}&message=${msg_encoded}"
  done
done