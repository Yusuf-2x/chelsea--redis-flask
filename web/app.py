from flask import Flask, request, render_template
from sqlalchemy import text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
import os
import time

app = Flask(__name__)

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DB = os.getenv("MYSQL_DB", "chelsea")
MYSQL_USER = os.getenv("MYSQL_USER", "chelsea")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "chelsea_password")

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def init_db(max_retries: int = 10, delay_seconds: int = 2) -> None:
    """Ensure schema exists, with simple retry so MySQL has time to start."""
    attempts = 0
    while True:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS chelsea_stats (
                            id INT PRIMARY KEY,
                            visits INT NOT NULL DEFAULT 0,
                            last_score VARCHAR(50) DEFAULT NULL
                        )
                        """
                    )
                )
                conn.execute(
                    text(
                        """
                        INSERT INTO chelsea_stats (id, visits, last_score)
                        VALUES (1, 0, NULL)
                        ON DUPLICATE KEY UPDATE id = id
                        """
                    )
                )
            break
        except OperationalError:
            attempts += 1
            if attempts >= max_retries:
                # Let the app start; routes will handle DB-offline cases.
                break
            time.sleep(delay_seconds)


init_db()

@app.get("/")
def home():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT last_score FROM chelsea_stats WHERE id = 1")
            ).scalar()
        last_score = result or "Not set yet"
    except Exception:
        last_score = "Not set yet (DB offline)"
    return render_template("home.html", last_score=last_score)

@app.get("/count")
def count():
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO chelsea_stats (id, visits, last_score)
                    VALUES (1, 1, NULL)
                    ON DUPLICATE KEY UPDATE visits = visits + 1
                    """
                )
            )
            new_count = conn.execute(
                text("SELECT visits FROM chelsea_stats WHERE id = 1")
            ).scalar()
    except Exception:
        new_count = "N/A (DB offline)"
    return render_template("count.html", count=new_count)

@app.get("/score")
def score():
    value = request.args.get("value")
    try:
        if value:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        UPDATE chelsea_stats
                        SET last_score = :value
                        WHERE id = 1
                        """
                    ),
                    {"value": value},
                )
            current = value
        else:
            with engine.connect() as conn:
                current = conn.execute(
                    text("SELECT last_score FROM chelsea_stats WHERE id = 1")
                ).scalar()
    except Exception:
        current = None
    return render_template("score.html", current_score=current or "Not set yet")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)