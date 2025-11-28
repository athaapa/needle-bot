import asyncio
import csv
import os
from datetime import datetime, time, timedelta

import discord
import groq
import pandas as pd
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
groq_client: groq.Client | None = None

REMINDER_SENT = False  # Track if we're expecting a response
TEST_MODE = False

# --- DATA PERSISTENCE SETUP ---
# This points to "data/wins.csv".
# On Railway, make sure you mount the volume to "/app/data"
DATA_DIR = "data"
CSV_FILE = os.path.join(DATA_DIR, "wins.csv")

# Ensure the directory exists immediately
os.makedirs(DATA_DIR, exist_ok=True)


def init_csv():
    """Creates the CSV with headers if it doesn't exist."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "win"])
            print(f"Created new CSV at {CSV_FILE}")


async def validate_win(text):
    """Check if win is output-based, not just time spent"""
    assert groq_client is not None
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You validate daily wins. Output-based wins are specific completions (problems solved, code shipped, concepts implemented). Input-based non-wins are vague time spent (studied X hours, worked on Y). Respond with 'VALID' or 'INVALID: [reason]'.",
            },
            {"role": "user", "content": f"Win: {text}"},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


async def weekly_reflection():
    assert groq_client is not None
    await client.wait_until_ready()
    # Replace with your actual User ID
    user = await client.fetch_user(289145869314293760)

    while not client.is_closed():
        if TEST_MODE:
            await asyncio.sleep(30)
        else:
            now = datetime.now()
            # Sunday 8 PM
            days_until_sunday = (6 - now.weekday()) % 7
            target = datetime.combine(now.date(), time(20, 0)) + timedelta(
                days=days_until_sunday
            )

            if now > target:
                target += timedelta(days=7)

            wait_seconds = (target - now).total_seconds()
            await asyncio.sleep(wait_seconds)

        # --- UPDATED CSV READING LOGIC ---
        if os.path.exists(CSV_FILE):
            # Read from the persistent data file
            df = pd.read_csv(CSV_FILE, names=["date", "win"], header=0)
        else:
            # Handle case where no data exists yet
            df = pd.DataFrame({"date": [], "win": []})

        # Filter for the last week
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent = df[df["date"] >= week_ago]

        if recent.empty:
            wins_text = "No wins recorded this week."
        else:
            wins_text = "\n".join(recent["win"].tolist())

        # LLM analyzes
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You analyze weekly progress logs for a CS student building AI infra, doing LeetCode prep, and managing coursework. Be brutally honest about patterns, momentum, and priorities. KEEP RESPONSE UNDER 300 WORDS.",
                },
                {
                    "role": "user",
                    "content": f"Here are this week's wins:\n{wins_text}\n\nWhat patterns do you see? What should I prioritize next week?",
                },
            ],
            temperature=0.7,
        )

        await user.send(
            f"**Weekly Reflection:**\n{response.choices[0].message.content}"
        )


async def daily_reminder():
    global REMINDER_SENT
    await client.wait_until_ready()
    user = await client.fetch_user(289145869314293760)

    while not client.is_closed():
        if TEST_MODE:
            await asyncio.sleep(15)
        else:
            now = datetime.now()
            target = datetime.combine(now.date(), time(21, 0))  # 9 PM

            if now > target:
                target += timedelta(days=1)  # Next day if past 9 PM

            wait_seconds = (target - now).total_seconds()
            await asyncio.sleep(wait_seconds)

        await user.send("What moved the needle today?")
        REMINDER_SENT = True


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    init_csv()  # Initialize the persistent CSV
    client.loop.create_task(daily_reminder())
    client.loop.create_task(weekly_reflection())


@client.event
async def on_message(message):
    global REMINDER_SENT

    # Ignore bot's own messages
    if message.author == client.user:
        return

    # Only log DM replies after reminder was sent
    if isinstance(message.channel, discord.DMChannel) and REMINDER_SENT:
        validation = await validate_win(message.content)
        if validation is None:
            await message.channel.send("Validation failed. Please try again.")
            return

        if validation.startswith("INVALID"):
            await message.channel.send(
                f"⚠️ {validation}\nWhat specifically did you complete?"
            )
            return

        # Write to the persistent CSV file
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d"), message.content])

        await message.add_reaction("✅")  # Confirm logged
        REMINDER_SENT = False


if __name__ == "__main__":
    load_dotenv()

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    GROQ_KEY = os.getenv("GROQ_API_KEY")

    if not TOKEN or not GROQ_KEY:
        raise ValueError("Set DISCORD_BOT_TOKEN and GROQ_API_KEY environment variables")

    groq_client = groq.Client(api_key=GROQ_KEY)
    client.run(TOKEN)
