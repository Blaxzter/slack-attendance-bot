import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from datetime import datetime, timedelta

load_dotenv()

# Initialize the Slack app
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Store responses and message tracking
responses = {}
message_tracking = {}  # Track the original message for each day


def get_tomorrow_date():
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d")


def create_summary_blocks(responses, tomorrow_date):
    coming = [user for user, response in responses.items() if response == "yes"]
    not_coming = [user for user, response in responses.items() if response == "no"]
    maybe = [user for user, response in responses.items() if response == "maybe"]

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Will you be coming to the office tomorrow ({tomorrow_date})? 🏢",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Yes 👍"},
                    "value": "yes",
                    "action_id": "attendance_yes",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "No 👎"},
                    "value": "no",
                    "action_id": "attendance_no",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Maybe 🤔"},
                    "value": "maybe",
                    "action_id": "attendance_maybe",
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Attendance Summary for {tomorrow_date}*\n"
                    f"Coming to office ({len(coming)}): {', '.join(coming) if coming else 'None'}\n"
                    f"Not coming ({len(not_coming)}): {', '.join(not_coming) if not_coming else 'None'}\n"
                    f"Maybe ({len(maybe)}): {', '.join(maybe) if maybe else 'None'}"
                ),
            },
        },
    ]
    return blocks


def send_attendance_poll(channel_id):
    tomorrow = get_tomorrow_date()
    # Clear previous responses for the new poll
    responses.clear()

    # Create initial message
    result = app.client.chat_postMessage(
        channel=channel_id,
        blocks=create_summary_blocks(responses, tomorrow),
        text="Will you be coming to the office tomorrow?",
    )

    # Store the message details for updates
    message_tracking[tomorrow] = {"channel": channel_id, "ts": result["ts"]}


def update_summary(body):
    tomorrow = get_tomorrow_date()
    if tomorrow in message_tracking:
        app.client.chat_update(
            channel=message_tracking[tomorrow]["channel"],
            ts=message_tracking[tomorrow]["ts"],
            blocks=create_summary_blocks(responses, tomorrow),
            text="Will you be coming to the office tomorrow?",
        )


# Handle responses
@app.action("attendance_yes")
def handle_yes(ack, body):
    ack()
    user = body["user"]["name"]
    responses[user] = "yes"
    update_summary(body)


@app.action("attendance_no")
def handle_no(ack, body):
    ack()
    user = body["user"]["name"]
    responses[user] = "no"
    update_summary(body)


@app.action("attendance_maybe")
def handle_maybe(ack, body):
    ack()
    user = body["user"]["name"]
    responses[user] = "maybe"
    update_summary(body)


# Command to trigger the poll manually
@app.command("/attendance-poll")
def create_poll(ack, body):
    ack()
    send_attendance_poll(body["channel_id"])


# Main function to run the bot
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
