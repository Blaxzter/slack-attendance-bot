# Slack Attendance Bot

<p align="center">
  <img src="./logo.png" width="200" alt="logo">
</p>


A simple Slack bot that helps track office attendance by creating polls and collecting responses from team members.

## Features

- Create attendance polls with a simple slash command (`/attendance-poll`)
- Three response options: Yes 👍, No 👎, Maybe 🤔
- Real-time updating summary of responses
- Single message interface - no spam!

## Setup

### Prerequisites

- Python 3.7+
- uv
- A Slack workspace where you can install apps

### Installation

1. Clone the repository and install dependencies:
```bash
git clone [your-repo-url]
cd slack-attendance-bot
uv sync
```

2. Create a new Slack app at https://api.slack.com/apps

3. Configure your Slack app:
   - Enable Socket Mode
   - Add Bot Token Scopes:
     - `chat:write`
     - `commands`
     - `users:read`
   - Create a slash command: `/attendance-poll`

4. Create a `.env` file with your tokens:
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```

### Running the Bot

```bash
python bot.py
```

## Usage

1. Add the bot to your desired channels
2. Type `/attendance-poll` to create a new attendance poll
3. Team members can click buttons to indicate their attendance
4. The summary updates automatically as people respond

## Environment Variables

- `SLACK_BOT_TOKEN`: Your bot's user token (starts with `xoxb-`)
- `SLACK_APP_TOKEN`: Your app-level token for Socket Mode (starts with `xapp-`)

## Notes

- The bot tracks responses for one day at a time
- A new poll clears previous responses
- All responses update the original message to avoid channel clutter

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT