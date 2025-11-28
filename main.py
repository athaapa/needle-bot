import asyncio
import csv
import os
from datetime import datetime, time, timedelta

import discord
import groq
import pandas as pd

intents = discord.Intents.default()
intents.message_content = True

print(f"TOKEN exists: {os.getenv('DISCORD_BOT_TOKEN') is not None}")
print(f"GROQ exists: {os.getenv('GROQ_API_KEY') is not None}")

# Get token from environment variable
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not TOKEN or not GROQ_KEY:
    raise ValueError("Set DISCORD_BOT_TOKEN and GROQ_API_KEY environment variables")


client = discord.Client(intents=intents)
groq_client = groq.Client(api_key=GROQ_KEY)

REMINDER_SENT = False  # Track if we're expecting a response
TEST_MODE = False


async def validate_win(text):
    """Check if win is output-based, not just time spent"""
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
    await client.wait_until_ready()
    user = await client.fetch_user(289145869314293760)

    while not client.is_closed():
        if TEST_MODE:
            await asyncio.sleep(30)  # 5 seconds instead of calculated time
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

        # Read wins.csv from past week
        df = pd.read_csv("wins.csv", names=["date", "win"])
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent = df[df["date"] >= week_ago]

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
            await asyncio.sleep(15)  # 5 seconds instead of calculated time
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
    client.loop.create_task(daily_reminder())  # Start reminder loop
    client.loop.create_task(weekly_reflection())  # Start reminder loop


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

        with open("wins.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d"), message.content])

        await message.add_reaction("✅")  # Confirm logged
        REMINDER_SENT = False


client.run(TOKEN)
