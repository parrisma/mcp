from typing import List
import logging
import pytest
import httpx
import uuid
from json_message_keys import JsonMessageKeys
import threading
import time

# Configure logging for tests
logger = logging.getLogger("MessageWebTest")
logging.basicConfig(level=logging.DEBUG)

# Requires Web Service to be running on port 5174 local host & newly started with no state


@pytest.mark.order(1)
def test_startup():
    print("\nRunning startup...")
    assert True


@pytest.fixture
def message_client():
    base_url = "http://localhost:5174"

    def client(endpoint: str, method: str = "GET", data: dict = None, params: dict = None):
        url = f"{base_url}/{endpoint.lstrip('/')}"
        with httpx.Client() as client:
            if method == "POST":
                return client.post(url, json=data)
            else:
                return client.get(url, params=params)

    return client


@pytest.fixture(scope="session")
def message_log() -> List[str]:
    msg_log: List[str] = []
    return msg_log


@pytest.fixture(scope="session")
def message_channel_uuid() -> uuid.UUID:
    channel_id = uuid.uuid4()
    return channel_id


@pytest.mark.order(1)
def test_web_service_is_running(message_client):
    response = message_client("", method="GET")
    assert response.status_code == 200
    logger.debug("Message Web service is running and accessible.")


@pytest.mark.order(2)
def test_post_test_messages(message_client,
                            message_channel_uuid: uuid.UUID,
                            message_log: List[str]):
    for msg_num in range(1, 6):
        msg = f"{msg_num}"
        response = message_client(
            "send_message",
            method="POST",
            data={JsonMessageKeys.CHANNEL_ID_GUID.value: str(
                message_channel_uuid), JsonMessageKeys.MESSAGE.value: msg}
        )
        logger.debug(f"Posted message {msg} to channel {message_channel_uuid}")
        assert response.status_code == 200, f"Failed to post test message {msg_num}"
        response_data = response.json()
        assert response_data.get(
            JsonMessageKeys.STATUS.value) == JsonMessageKeys.OK.value, f"Message {msg_num} failed to posted successfully"
        message_log.append(msg)


@pytest.mark.order(3)
def test_get_all_messages(message_client,
                          message_channel_uuid: uuid.UUID,
                          message_log: List[str]):
    response = message_client(
        "get_message",
        method="GET",
        params={JsonMessageKeys.CHANNEL_ID_GUID.value: str(
                message_channel_uuid)}
    )
    assert response.status_code == 200, f"Failed to get messages for channel {message_channel_uuid}"
    assert JsonMessageKeys.MESSAGES.value in response.json(
    ), "Response does not contain 'messages' as expected"
    actual_messages = response.json()[JsonMessageKeys.MESSAGES.value]
    assert len(actual_messages) == len(
        message_log), "Number of messages retrieved does not match number sent"
    actual_messages = [msg.get(JsonMessageKeys.MESSAGE.value, None)
                       for msg in actual_messages]
    assert None not in actual_messages, "One or more messages returned as None"
    for expected, actual in zip(message_log, actual_messages):
        assert expected == actual, f"Message mismatch: expected '{expected}', got '{actual}'"


@pytest.mark.order(4)
def test_get_messages_after(message_client,
                            message_channel_uuid: uuid.UUID,
                            message_log: List[str]):
    # Get all messages again as a starting point
    response = message_client(
        "get_message",
        method="GET",
        params={JsonMessageKeys.CHANNEL_ID_GUID.value: str(
                message_channel_uuid)}
    )
    assert response.status_code == 200, f"Failed to get messages for channel {message_channel_uuid}"
    assert JsonMessageKeys.MESSAGES.value in response.json(
    ), "Response does not contain 'messages' as expected"
    actual_messages = response.json()[JsonMessageKeys.MESSAGES.value]
    assert len(actual_messages) == len(
        message_log), "Number of messages retrieved does not match number sent"

    # Now check that we get the right set of messages when we pass the last message UUID
    # passing last message UUID means this is the last message I saw please send me all
    # messages aster (NOT including) this message
    #
    # If the message UUID passed is the last message the get should block until a new
    # message is posted to the channel, we will cover that in a later test

    test_cases = []
    for msg_num in range(0, len(actual_messages)-1):
        test_cases.append((actual_messages[msg_num].get(JsonMessageKeys.MESSAGE_UUID.value, None),
                           [m.get(JsonMessageKeys.MESSAGE.value, None)
                            for m in actual_messages[msg_num + 1:]]))

    for message_uuid, expected_messages in test_cases:
        response = message_client(
            "get_message",
            method="GET",
            params={
                JsonMessageKeys.CHANNEL_ID_GUID.value: str(message_channel_uuid),
                JsonMessageKeys.MESSAGE_UUID.value: message_uuid
            }
        )
        assert response.status_code == 200, f"Failed to get messages after {message_uuid}"
        assert JsonMessageKeys.MESSAGES.value in response.json(
        ), "Response does not contain 'messages' as expected"
        actual_messages = response.json()[JsonMessageKeys.MESSAGES.value]
        assert len(actual_messages) == len(
            expected_messages), "Number of messages retrieved does not match number expected"
        actual_messages = [msg.get(JsonMessageKeys.MESSAGE.value, None)
                           for msg in actual_messages]
        assert None not in actual_messages, "One or more messages returned as None"
        for expected, actual in zip(expected_messages, actual_messages):
            assert expected == actual, f"Message mismatch: expected '{expected}', got '{actual}'"


@pytest.mark.order(5)
def test_get_blocking_get(message_client,
                          message_channel_uuid: uuid.UUID,
                          message_log: List[str]):
    # Get all messages again as a starting point
    response = message_client(
        "get_message",
        method="GET",
        params={JsonMessageKeys.CHANNEL_ID_GUID.value: str(
                message_channel_uuid)}
    )
    assert response.status_code == 200, f"Failed to get messages for channel {message_channel_uuid}"
    assert JsonMessageKeys.MESSAGES.value in response.json(
    ), "Response does not contain 'messages' as expected"
    actual_messages = response.json()[JsonMessageKeys.MESSAGES.value]
    assert len(actual_messages) == len(
        message_log), "Number of messages retrieved does not match number sent"

    # Now check blocking, So if the message UUID passed is the last message the get should block until a new
    # message is posted to the channel
    # To do this we will raise a timer thread to post a new message after a short delay and then ask for the
    # messages after the last message UUID. This should block until the new message is posted, we will know
    # this because we will record the time before the blocking get and the time after and assert that this
    # is at least the delay we set in the timer thread

    # Get the last message UUID
    last_message_uuid = actual_messages[-1].get(
        JsonMessageKeys.MESSAGE_UUID.value)
    delay_seconds = 1.5  # Delay before posting a new message

    # Create a timer thread to post a new message after delay
    def delayed_post():
        time.sleep(delay_seconds)
        new_message = "Delayed message for blocking test"
        message_client(
            "send_message",
            method="POST",
            data={JsonMessageKeys.CHANNEL_ID_GUID.value: str(message_channel_uuid),
                  JsonMessageKeys.MESSAGE.value: new_message}
        )
        message_log.append(new_message)
        logger.debug(
            f"Posted delayed message to channel {message_channel_uuid}")

    # Start the timer thread
    timer_thread = threading.Thread(target=delayed_post)
    timer_thread.daemon = True
    timer_thread.start()

    # Measure time for the blocking get
    start_time = time.time()
    response = message_client(
        "get_message",
        method="GET",
        params={
            JsonMessageKeys.CHANNEL_ID_GUID.value: str(message_channel_uuid),
            JsonMessageKeys.MESSAGE_UUID.value: last_message_uuid
        }
    )
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Verify response and timing
    assert response.status_code == 200, "Blocking get request failed"
    assert JsonMessageKeys.MESSAGES.value in response.json(), "Response missing messages key"

    # Verify we got exactly one new message
    actual_messages = response.json()[JsonMessageKeys.MESSAGES.value]
    assert len(
        actual_messages) == 1, f"Expected 1 new message, got {len(actual_messages)}"

    # Verify the delay - we should have blocked for at least the delay_seconds
    assert elapsed_time >= delay_seconds, f"Request completed too quickly ({elapsed_time}s < {delay_seconds}s)"

    # Verify message content
    received_message = actual_messages[0].get(JsonMessageKeys.MESSAGE.value)
    assert received_message == message_log[
        -1], f"Message mismatch: expected '{message_log[-1]}', got '{received_message}'"

    logger.debug(
        f"Blocking get took {elapsed_time:.2f} seconds, delay was {delay_seconds} seconds")
