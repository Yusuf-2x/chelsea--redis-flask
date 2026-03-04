from flask import Flask, request
from redis import Redis
import os

app = Flask(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

r = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

VISITS_KEY = "chelsea_hub_visits"
SCORE_KEY = "chelsea_hub_last_score"

@app.get("/")
def home():
    last_score = r.get(SCORE_KEY) or "Not set yet"
    return (
        "Chelsea Matchday Hub 🔵\n\n"
        "Routes:\n"
        " - /count  -> visit counter\n"
        " - /score?value=2-0  -> set last score\n"
        " - /score            -> view last score\n\n"
        f"Last score: {last_score}\n"
    )

@app.get("/count")
def count():
    new_count = r.incr(VISITS_KEY)
    return f"Turnstile count: {new_count} ✅ (refresh to increase)\n"

@app.get("/score")
def score():
    value = request.args.get("value")
    if value:
        r.set(SCORE_KEY, value)
        return f"Saved last score as: {value}\n"
    current = r.get(SCORE_KEY)
    return f"Last score is: {current or 'Not set yet'}\n"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)