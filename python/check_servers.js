const { Client, GatewayIntentBits } = require('discord.js');
require('dotenv').config();

const token = process.env.DISCORD_OCR_BOT_TOKEN;
const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.once('ready', () => {
    console.log('Bot:', client.user.tag);
    console.log('Servers:');
    client.guilds.cache.forEach(guild => {
        console.log(' -', guild.id, ':', guild.name);
    });
    client.destroy();
});

client.login(token);
