#!/bin/bash
# Fix the websocket.ts syntax error on line 199
# Run this script on the Pi to fix the immediate issue

echo "Fixing websocket.ts syntax error..."

cd /home/jrwest/projects/LeadVille

# First, let's see the current problematic line
echo "Current problematic line:"
sed -n '199p' frontend/src/utils/websocket.ts

# Fix the syntax error by replacing the malformed console.log
sed -i '199s/.*/    console.log('\''Attempting to reconnect ('\'' + this.reconnectAttempts + '\''\/'\''\'' + this.config.maxReconnectAttempts + '\'')...'\'');/' frontend/src/utils/websocket.ts

echo "Fixed line:"
sed -n '199p' frontend/src/utils/websocket.ts

echo "Websocket syntax error fixed!"
echo "Now restart the frontend dev server:"
echo "cd /home/jrwest/projects/LeadVille/frontend && npm run dev"