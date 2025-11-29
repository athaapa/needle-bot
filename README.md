# needle-bot

A Discord bot designed to help track and validate daily "wins" for productivity and progress tracking, particularly aimed at computer science students engaged in AI infrastructure development, LeetCode preparation, and coursework management.

## Features

- **Daily Reminders**: Sends a daily message at 9 PM asking "What moved the needle today?" to encourage logging accomplishments.
- **Win Validation**: Uses AI to validate that logged wins are output-based (e.g., problems solved, code shipped) rather than input-based (e.g., time spent studying).
- **Data Persistence**: Stores validated wins in a CSV file for long-term tracking.
- **Weekly Reflections**: Generates and sends a weekly analysis on Sundays at 8 PM, providing honest feedback on patterns, momentum, and priorities.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/athapa/needle-bot.git
   cd needle-bot
   ```

2. Install dependencies using uv (or pip):
   ```
   uv sync
   ```
   Or with pip:
   ```
   pip install -r requirements.txt
   ```

## Setup

1. Create a `.env` file in the project root with the following environment variables:
   ```
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

2. Obtain a Discord bot token:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Create a new application and add a bot.
   - Copy the bot token and paste it into the `.env` file.

3. Obtain a Groq API key:
   - Sign up at [Groq](https://groq.com/).
   - Generate an API key and add it to the `.env` file.

4. Invite the bot to your Discord server:
   - In the Discord Developer Portal, go to OAuth2 > URL Generator.
   - Select `bot` scope and appropriate permissions (e.g., Send Messages, Read Messages).
   - Use the generated URL to invite the bot to your server.

5. Update the user ID in `main.py`:
   - Replace `289145869314293760` with your Discord user ID. You can find this by enabling Developer Mode in Discord and right-clicking your username.

## Usage

Run the bot:
```
python main.py
```

The bot will:
- Send daily reminders at 9 PM.
- Validate responses to ensure they are specific, output-based wins.
- Log valid wins to `data/wins.csv`.
- Send weekly reflections on Sundays at 8 PM.

Interact with the bot via direct messages after receiving a reminder.

## Configuration

- **Test Mode**: Set `TEST_MODE = True` in `main.py` to shorten wait times for testing (reminders every 15 seconds, reflections every 30 seconds).
- **Data Directory**: Wins are stored in `data/wins.csv`. Ensure the directory is writable.

## Dependencies

- discord-py >= 2.3.2
- groq >= 0.4.0
- pandas >= 2.0.0
- python-dotenv >= 1.0.0

## License

This project is licensed under the MIT License.