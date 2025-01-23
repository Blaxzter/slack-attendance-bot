import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

# Initialize the Slack app
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Store responses and message tracking
responses = {}
message_tracking = {}  # Track the original message for each day


def get_tomorrow_date():
    berlin_tz = pytz.timezone('Europe/Berlin')
    tomorrow = datetime.now(berlin_tz) + timedelta(days=1)
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


def send_attendance_poll():
    try:
        # Get all users in the workspace
        result = app.client.users_list()
        users = result["members"]
        
        tomorrow = get_tomorrow_date()
        # Clear previous responses for the new poll
        responses.clear()
        
        for user in users:
            # Skip bots, deleted users, and slackbot
            if (user["is_bot"] or 
                user.get("deleted", False) or 
                user["name"] == "slackbot"):
                continue
                
            try:
                # Open DM channel with user
                dm_channel = app.client.conversations_open(users=user["id"])
                channel_id = dm_channel["channel"]["id"]
                
                # Send message to DM channel
                result = app.client.chat_postMessage(
                    channel=channel_id,
                    blocks=create_summary_blocks(responses, tomorrow),
                    text="Will you be coming to the office tomorrow?"
                )
                
                # Store the message details for updates
                if tomorrow not in message_tracking:
                    message_tracking[tomorrow] = {}
                message_tracking[tomorrow][user["id"]] = {"channel": channel_id, "ts": result["ts"]}
            except Exception as e:
                print(f"Error sending message to user {user['name']}: {e}")
            
    except Exception as e:
        print(f"Error sending attendance poll: {e}")


def update_all_summaries(tomorrow_date=None):
    if tomorrow_date is None:
        tomorrow_date = get_tomorrow_date()
        
    if tomorrow_date in message_tracking:
        for user_id, msg_info in message_tracking[tomorrow_date].items():
            try:
                app.client.chat_update(
                    channel=msg_info["channel"],
                    ts=msg_info["ts"],
                    blocks=create_summary_blocks(responses, tomorrow_date),
                    text="Will you be coming to the office tomorrow?"
                )
            except Exception as e:
                print(f"Error updating message for user {user_id}: {e}")


# Handle responses
@app.action("attendance_yes")
def handle_yes(ack, body):
    ack()
    user = body["user"]["name"]
    responses[user] = "yes"
    update_all_summaries()  # Update messages for all users


@app.action("attendance_no")
def handle_no(ack, body):
    ack()
    user = body["user"]["name"]
    responses[user] = "no"
    update_all_summaries()  # Update messages for all users


@app.action("attendance_maybe")
def handle_maybe(ack, body):
    ack()
    user = body["user"]["name"]
    responses[user] = "maybe"
    update_all_summaries()  # Update messages for all users


# Command to trigger the poll manually
@app.command("/attendance-poll")
def create_poll(ack, body):
    ack()
    send_attendance_poll()


def schedule_daily_poll():
    scheduler = BackgroundScheduler()
    berlin_tz = pytz.timezone('Europe/Berlin')
    
    # Schedule the job to run at 18:00 Berlin time
    scheduler.add_job(
        send_attendance_poll,
        'cron',
        hour=18,
        minute=0,
        timezone=berlin_tz
    )
    
    scheduler.start()


def delete_previous_messages(tomorrow_date=None):
    try:
        if tomorrow_date is None:
            tomorrow_date = get_tomorrow_date()
            
        if tomorrow_date in message_tracking:
            for user_id, msg_info in message_tracking[tomorrow_date].items():
                try:
                    app.client.chat_delete(
                        channel=msg_info["channel"],
                        ts=msg_info["ts"]
                    )
                except Exception as e:
                    print(f"Error deleting message for user {user_id}: {e}")
            
            del message_tracking[tomorrow_date]
            responses.clear()
            return True
        return False
    except Exception as e:
        print(f"Error in delete_previous_messages: {e}")
        return False


def get_attendance_stats():
    tomorrow = get_tomorrow_date()
    total_users = len(responses)
    coming = len([u for u, r in responses.items() if r == "yes"])
    not_coming = len([u for u, r in responses.items() if r == "no"])
    maybe = len([u for u, r in responses.items() if r == "maybe"])
    no_response = len(message_tracking.get(tomorrow, {})) - total_users
    
    return {
        "date": tomorrow,
        "total_responses": total_users,
        "coming": coming,
        "not_coming": not_coming,
        "maybe": maybe,
        "no_response": no_response if no_response >= 0 else 0
    }


# New command to force create a new poll
@app.command("/new-poll")
def force_new_poll(ack, body, respond):
    ack()
    try:
        # Delete previous poll if exists
        delete_previous_messages()
        # Send new poll
        send_attendance_poll()
        respond("New attendance poll has been created and sent to all users.")
    except Exception as e:
        respond(f"Error creating new poll: {e}")


# Command to delete the current poll
@app.command("/delete-poll")
def delete_poll(ack, body, respond):
    ack()
    if delete_previous_messages():
        respond("Previous attendance poll has been deleted.")
    else:
        respond("No active poll found to delete.")


# Command to get current statistics
@app.command("/attendance-stats")
def get_stats(ack, body, respond):
    ack()
    stats = get_attendance_stats()
    respond(
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Attendance Statistics for {stats['date']}*\n"
                           f"• Total Responses: {stats['total_responses']}\n"
                           f"• Coming: {stats['coming']}\n"
                           f"• Not Coming: {stats['not_coming']}\n"
                           f"• Maybe: {stats['maybe']}\n"
                           f"• No Response: {stats['no_response']}"
                }
            }
        ]
    )


# Command to show help
@app.command("/attendance-help")
def show_help(ack, respond):
    ack()
    help_text = """
*Available Commands:*
• `/attendance-poll` - Manually trigger attendance poll
• `/new-poll` - Force create a new poll (deletes previous one)
• `/delete-poll` - Delete the current active poll
• `/attendance-stats` - Show current attendance statistics
• `/attendance-help` - Show this help message

*How it works:*
• Bot automatically sends attendance polls at 18:00 (Berlin time)
• Each user receives a private message with the poll
• Responses are collected and summarized
• You can use the commands above to manage the polls
"""
    respond(
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": help_text
                }
            }
        ]
    )


# Main function to run the bot
if __name__ == "__main__":
    # Start the scheduler
    schedule_daily_poll()
    
    # Start the bot
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
