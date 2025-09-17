#!/bin/bash
cd /home/jrwest/projects/LeadVille_latest/frontend/dist
echo 'Starting React server on port 3001...'
python3 -m http.server 3001 --bind 0.0.0.0
