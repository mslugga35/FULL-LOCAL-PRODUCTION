#!/usr/bin/env python3
"""
Discord Forwarding Configuration
Routes messages to correct Discord servers and channels
"""

# Discord Webhook Configuration
DISCORD_WEBHOOKS = {
    # Server 675908407617650697 - For UATB, Diamond/Chamba, Paid Cappers
    'uatb': 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN',
    'diamond': 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN',
    'paid_diamond': 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN',
    'paid_uatb': 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN',

    # Server 1390050801136701642 - For Free/Leaked Cappers
    # Need to get webhooks for these channels:
    # - 1403894557615325216 (cappers free - leaks)
    # - 1403894596186017962 (cappers-leaked)
    # - 1403894653660692500 (exclusive-cappers)
    'free_cappers': None,  # TODO: Add webhook for channel 1403894557615325216
    'paid_chamba': None,   # TODO: Add webhook for channel 1403894596186017962
}

# Server mapping for reference
DISCORD_SERVERS = {
    '675908407617650697': {
        'name': 'Paid Server',
        'channels': {
            '1403837637730762875': 'main-channel'
        },
        'receives': ['UATB', 'Diamond', 'Chamba', 'Paid Cappers']
    },
    '1390050801136701642': {
        'name': 'Free/Leaks Server',
        'channels': {
            '1403894557615325216': 'cappers-free-leaks',
            '1403894596186017962': 'cappers-leaked',
            '1403894653660692500': 'exclusive-cappers'
        },
        'receives': ['Free Cappers', 'Leaked', 'Exclusive (free)']
    }
}

# Channel to folder mapping (matches message_processor_windows.py)
CHANNEL_TO_FOLDER = {
    # UATB variants -> Server 675908407617650697
    'UATB': 'uatb',
    '🌐 UATB 🌐': 'uatb',

    # Diamond/Chamba variants -> Server 675908407617650697
    'DIAMOND': 'diamond',
    'DIAMOND 💎 VIP PACKAGE': 'diamond',
    'Diamond/Chamba': 'diamond',

    # Free Cappers -> Server 1390050801136701642
    'Cappers Free': 'free_cappers',
    'CAPPERS FREE💥': 'free_cappers',
    'CBlez Bets (FREE)': 'free_cappers',

    # Leaked/Exclusive (now free) -> Server 1390050801136701642
    'Cappers Leaked': 'free_cappers',
    'HANDICAPPERS LEAKED🔥': 'free_cappers',
    'Exclusive Cappers': 'free_cappers',
    '***EXCLUSIVE PLAYS***': 'free_cappers',
}