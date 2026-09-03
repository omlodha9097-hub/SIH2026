#!/bin/bash
echo "Starting local server for frontend..."
echo "Access the Farmer Portal at: http://localhost:8000/farmer-app"
echo "Access the Admin Dashboard at: http://localhost:8000/admin-dashboard"
python3 -m http.server 8000
