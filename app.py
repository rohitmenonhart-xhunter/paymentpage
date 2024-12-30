import os
import uuid
import time
from flask import Flask, render_template, session
from threading import Lock, Thread

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for Flask sessions

# Global variables to track users and waiting list
current_users = []
waiting_list = []
max_users = 2
lock = Lock()


def manage_waiting_list():
    """Background thread to manage waiting list and allow users every 10 minutes."""
    global current_users, waiting_list

    while True:
        time.sleep(600)  # Wait for 10 minutes
        with lock:
            if len(waiting_list) > 0:
                to_allow = min(len(waiting_list), max_users)
                current_users.extend(waiting_list[:to_allow])
                waiting_list = waiting_list[to_allow:]


@app.route("/")
def home():
    global current_users, waiting_list

    # Assign a unique user ID if not already assigned
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    user_id = session["user_id"]

    with lock:
        if user_id not in current_users and len(current_users) < max_users:
            current_users.append(user_id)
        elif user_id not in waiting_list:
            waiting_list.append(user_id)

    # Check if the user is allowed
    if user_id in current_users:
        return render_template("payment.html", user_id=user_id)
    else:
        position = waiting_list.index(user_id) + 1
        return render_template("waiting.html", position=position)


@app.route("/leave", methods=["POST"])
def leave():
    global current_users, waiting_list
    user_id = session.get("user_id")  # Get the user's unique ID

    with lock:
        if user_id in current_users:
            current_users.remove(user_id)

        if user_id in waiting_list:
            waiting_list.remove(user_id)

    return {"message": "User left successfully."}


if __name__ == "__main__":
    # Start the background thread for automatic user movement
    Thread(target=manage_waiting_list, daemon=True).start()

    # Get the port from the environment variable (default to 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
