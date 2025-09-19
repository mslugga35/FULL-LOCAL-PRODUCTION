# How to Get Your New Discord User Token

## ⚠️ IMPORTANT: Use at Your Own Risk
Using user tokens (self-bots) violates Discord's Terms of Service and can result in account termination.

## Steps to Get Your Token:

### Method 1: Browser Developer Tools
1. Open Discord in your web browser (https://discord.com/app)
2. Press `F12` or `Ctrl+Shift+I` to open Developer Tools
3. Go to the **Network** tab
4. Type something in any Discord channel
5. Look for requests to `messages` or `science`
6. Click on one of these requests
7. Go to **Request Headers**
8. Find `Authorization:` header
9. Copy the token value (starts with MTI, MTA, OTA, etc.)

### Method 2: Console Method
1. Open Discord in browser
2. Press `Ctrl+Shift+I` for Developer Tools
3. Go to **Console** tab
4. Paste this code:
```javascript
(webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
```
5. Press Enter - your token will appear

## Update Your Config:

Once you have your new token:
1. Open `C:\Users\mpmmo\discord-forwarder-production\config.json`
2. Replace the old token with your new one
3. Save the file
4. Restart the forwarder

## ⚠️ Security Tips:
- **NEVER share your token** with anyone
- **Keep it secret** - it gives full access to your account
- **Rotate regularly** if you suspect it's compromised
- Consider using a **separate account** for automation

## Alternative: Use a Bot Token Instead
For legitimate use, create a proper Discord Bot:
1. Go to https://discord.com/developers/applications
2. Create New Application
3. Go to Bot section
4. Create a Bot
5. Copy the Bot Token
6. Use the Node.js version with bot token instead