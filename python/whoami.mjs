#!/usr/bin/env node
// Bot Identity Checker - Know which bot is actually running

import { Client, GatewayIntentBits } from 'discord.js';
import dotenv from 'dotenv';

dotenv.config();

const tokens = {
    'DISCORD_SENDER_TOKEN': process.env.DISCORD_SENDER_TOKEN,
    'DISCORD_OCR_BOT_TOKEN': process.env.DISCORD_OCR_BOT_TOKEN,
    'DISCORD_BOT_TOKEN': process.env.DISCORD_BOT_TOKEN
};

console.log('🤖 BOT IDENTITY CHECK');
console.log('====================\n');

for (const [name, token] of Object.entries(tokens)) {
    if (!token) {
        console.log(`❌ ${name}: Not configured`);
        continue;
    }
    
    const client = new Client({
        intents: [GatewayIntentBits.Guilds]
    });
    
    try {
        await client.login(token);
        
        console.log(`✅ ${name}:`);
        console.log(`   Name: ${client.user.tag}`);
        console.log(`   ID: ${client.user.id}`);
        console.log(`   Guilds: ${client.guilds.cache.size}`);
        
        // Check if in specific server
        const targetGuild = '675908407617650697';
        const guild = client.guilds.cache.get(targetGuild);
        if (guild) {
            console.log(`   ✅ In target server: ${guild.name}`);
        } else {
            console.log(`   ❌ NOT in target server ${targetGuild}`);
        }
        
        await client.destroy();
    } catch (error) {
        console.log(`❌ ${name}: Invalid token or error`);
        console.log(`   Error: ${error.message}`);
    }
    
    console.log();
}

console.log('====================');
console.log('Use DISCORD_SENDER_TOKEN for discord_sender.js');
console.log('Use DISCORD_OCR_BOT_TOKEN for ocr_processor.js');