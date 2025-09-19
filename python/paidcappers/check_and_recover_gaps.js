#!/usr/bin/env node

const fs = require('fs');

// Configuration
const CONFIG = {
    checkWindowMinutes: 30,
    recoveryWindowHours: 2,
    logFile: '/root/bots/paidcappers/gap_detection.log',
    lastCheckFile: '/root/bots/paidcappers/last_gap_check.json',
    minRecoveryIntervalMinutes: 10
};

function log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level}] ${message}\n`;
    console.log(logMessage.trim());
    try {
        fs.appendFileSync(CONFIG.logFile, logMessage);
    } catch (error) {
        console.error('Failed to write to log file:', error.message);
    }
}

function shouldRunRecovery() {
    try {
        if (!fs.existsSync(CONFIG.lastCheckFile)) {
            return true;
        }
        const data = JSON.parse(fs.readFileSync(CONFIG.lastCheckFile, 'utf8'));
        if (!data.lastRecovery) {
            return true;
        }
        const lastRecovery = new Date(data.lastRecovery);
        const minInterval = CONFIG.minRecoveryIntervalMinutes * 60 * 1000;
        return (Date.now() - lastRecovery.getTime()) > minInterval;
    } catch (error) {
        return true;
    }
}

async function checkBotHealth() {
    const { exec } = require('child_process');
    return new Promise((resolve) => {
        exec('pm2 status paidcappers-bot', (error, stdout) => {
            if (error || !stdout.includes('online')) {
                resolve({ healthy: false });
                return;
            }
            resolve({ healthy: true });
        });
    });
}

async function runRecovery() {
    const { spawn } = require('child_process');
    return new Promise((resolve) => {
        log(`Starting recovery for last ${CONFIG.recoveryWindowHours} hours`);
        const recovery = spawn('node', ['catchup_missed_messages.js', CONFIG.recoveryWindowHours.toString()], {
            cwd: '/root/bots/paidcappers',
            stdio: 'pipe'
        });
        
        let output = '';
        recovery.stdout.on('data', (data) => { output += data.toString(); });
        
        recovery.on('close', (code) => {
            if (code === 0) {
                const messageCount = (output.match(/\[SENT\]/g) || []).length;
                log(`Recovery completed. Recovered ${messageCount} messages.`);
                
                // Update last recovery time
                const data = { lastCheck: new Date().toISOString(), lastRecovery: new Date().toISOString() };
                try {
                    fs.writeFileSync(CONFIG.lastCheckFile, JSON.stringify(data, null, 2));
                } catch (e) {}
                
                resolve({ success: true, messageCount });
            } else {
                resolve({ success: false });
            }
        });
        
        setTimeout(() => {
            recovery.kill();
            resolve({ success: false, error: 'timeout' });
        }, 5 * 60 * 1000);
    });
}

async function main() {
    try {
        log('=== Starting automated gap detection ===');
        
        const healthCheck = await checkBotHealth();
        if (!healthCheck.healthy) {
            log('Bot health check failed. Triggering recovery.');
            if (shouldRunRecovery()) {
                await runRecovery();
            } else {
                log('Skipping recovery due to minimum interval');
            }
            return;
        }
        
        log('Bot appears healthy.');
        
        // Update last check time
        try {
            const data = { lastCheck: new Date().toISOString() };
            fs.writeFileSync(CONFIG.lastCheckFile, JSON.stringify(data, null, 2));
        } catch (e) {}
        
    } catch (error) {
        log(`Error in gap detection: ${error.message}`, 'ERROR');
    }
}

main().then(() => process.exit(0)).catch(() => process.exit(1));
