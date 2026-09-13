"""
Fetches headlines from RSS feeds (no API key needed) and hands them
to the LLM to summarize conversationally.
"""

import feedparser
import config
from llm import ask_llm


def get_headlines(topic: str = "top", count: int = 5) -> list:
    url = config.NEWS_RSS_FEEDS.get(topic, config.NEWS_RSS_FEEDS["top"])
    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries[:count]]


def news_briefing(topic: str = "top", use_ai_wrapper: bool = False) -> str:
    headlines = get_headlines(topic)
    if not headlines:
        return "Couldn't fetch news right now — check your internet connection."

    # Default: read back the REAL headlines directly. No AI involved, no
    # risk of invented details. This is the trustworthy option.
    if not use_ai_wrapper:
        listed = "\n".join(f"{i+1}. {h}" for i, h in enumerate(headlines))
        return f"Here are today's top {topic} headlines:\n{listed}"

    # Optional: let the AI add light conversational framing, but with a
    # strict instruction not to invent any name, event, or detail that
    # isn't literally in the headline list below.
    prompt = (
        "Below is a list of REAL headlines. Read them out in a friendly, "
        "conversational tone, as a short spoken briefing.\n"
        "STRICT RULES:\n"
        "- Do NOT add any name, event, company, or fact that is not "
        "literally present in the headlines below.\n"
        "- Do NOT speculate or infer anything beyond what's written.\n"
        "- If a headline is unclear, just read it close to as-is rather "
        "than guessing what it means.\n\n"
        "Headlines:\n" + "\n".join(f"- {h}" for h in headlines)
    )
    return ask_llm(prompt)