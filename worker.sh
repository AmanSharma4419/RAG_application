cd "$(dirname "$0")"

. venv/bin/activate

rq worker --url redis://valkey:6379/0
