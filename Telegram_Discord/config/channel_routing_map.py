"""
Telegram Channel to Discord Target Routing Map
Maps Telegram channel IDs to Discord target identifiers
"""

# Telegram chat_id -> queue folder name (relative to message_queue)
ROUTING_MAP = {
    -1002177758646: "paid_uatb",         # UATB (Paid Picks)
    -1002470080886: "paid_diamond",      # Diamond/Chamba (Paid Picks)
    -1002592669126: "free_cappers",      # Cappers Free
    -1001560546587: "cappers_leaked",    # Cappers Leaked
    -1002608783933: "exclusive_cappers", # Exclusive Cappers
}

# Reverse mapping for lookups
DISCORD_TO_TELEGRAM = {v: k for k, v in ROUTING_MAP.items()}

def get_discord_target(telegram_channel_id):
    """Get Discord target for a Telegram channel ID"""
    return ROUTING_MAP.get(telegram_channel_id)

def get_telegram_channel(discord_target):
    """Get Telegram channel ID for a Discord target"""
    return DISCORD_TO_TELEGRAM.get(discord_target)

def get_all_telegram_channels():
    """Get all monitored Telegram channel IDs"""
    return list(ROUTING_MAP.keys())

def get_all_discord_targets():
    """Get all Discord target identifiers"""
    return list(ROUTING_MAP.values())
