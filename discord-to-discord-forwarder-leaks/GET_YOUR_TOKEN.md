# How to Get Your Discord User Token

## Method 1: Browser Console (Easiest)

1. Open Discord in your browser (https://discord.com/app)
2. Press `F12` or `Ctrl+Shift+I` to open Developer Tools
3. Go to the `Console` tab
4. Paste this code and press Enter:

```javascript
(webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
```

5. Copy the token that appears (it will look like: `MTE1M...` or similar)

## Method 2: Network Tab

1. Open Discord in your browser
2. Press `F12` to open Developer Tools
3. Go to the `Network` tab
4. Click on any request to Discord API
5. Look in Request Headers for `authorization: YOUR_TOKEN_HERE`

## Method 3: Application Tab

1. Open Discord in your browser
2. Press `F12` to open Developer Tools
3. Go to `Application` tab
4. Navigate to `Local Storage` → `https://discord.com`
5. Find the `token` entry
6. Copy the value (remove quotes if present)

## IMPORTANT SECURITY NOTES:

⚠️ **NEVER share your user token with anyone!**
⚠️ **This token gives full access to your Discord account**
⚠️ **If compromised, immediately change your Discord password**

Once you have your token, update the config.json file with it.