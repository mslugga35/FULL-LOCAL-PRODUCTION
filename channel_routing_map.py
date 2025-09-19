#!/usr/bin/env python3
"""
SIMPLE CHANNEL ROUTING MAP
Telegram Channel ID → Folder → Discord Destination
"""

# TELEGRAM CHANNEL IDS TO FOLDER MAPPING
TELEGRAM_TO_FOLDER = {
    -1002177758646: 'paid_uatb',        # UATB → paid_uatb folder
    -1002470080886: 'paid_diamond',     # Diamond/Chamba → paid_diamond folder
    -1002592669126: 'free_cappers',     # Cappers Free → free_cappers folder
    -1001560546587: 'cappers_leaked',   # Cappers Leaked → cappers_leaked folder
    -1002608783933: 'exclusive_cappers' # Exclusive Cappers → exclusive_cappers folder
}

# FOLDER TO DISCORD DESTINATION
FOLDER_TO_DISCORD = {
    # PAID - Goes to server 675908407617650697
    'paid_uatb': {
        'server': '675908407617650697',
        'channel': '1403837637730762875',
        'webhook': 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN'
    },
    'paid_diamond': {
        'server': '675908407617650697',
        'channel': '1403837637730762875',
        'webhook': 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN'
    },

    # FREE - Goes to server 1390050801136701642
    'free_cappers': {
        'server': '1390050801136701642',
        'channel': '1403894557615325216',  # cappers free - leaks
        'transport': 'bot'
    },
    'cappers_leaked': {
        'server': '1390050801136701642',
        'channel': '1403894596186017962',  # cappers-leaked
        'transport': 'bot'
    },
    'exclusive_cappers': {
        'server': '1390050801136701642',
        'channel': '1403894653660692500',  # exclusive-cappers
        'transport': 'bot'
    }
}

# SUMMARY FOR CLARITY
"""
FLOW:
1. Telegram channel -1002177758646 (UATB) → paid_uatb folder → Discord 675908407617650697/1403837637730762875 (webhook)
2. Telegram channel -1002470080886 (Diamond) → paid_diamond folder → Discord 675908407617650697/1403837637730762875 (webhook)
3. Telegram channel -1002592669126 (Free) → free_cappers folder → Discord 1390050801136701642/1403894557615325216 (bot)
4. Telegram channel -1001560546587 (Leaked) → cappers_leaked folder → Discord 1390050801136701642/1403894596186017962 (bot)
5. Telegram channel -1002608783933 (Exclusive) → exclusive_cappers folder → Discord 1390050801136701642/1403894653660692500 (bot)
"""