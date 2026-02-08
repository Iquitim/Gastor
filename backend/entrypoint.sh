#!/bin/bash
set -e

# Run migrations (if any simple way exists, for now we rely on main.py startup)

# Run promotion script
echo "Running admin promotion script..."
python3 scripts/promote_admin.py || true

# Start application
echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
