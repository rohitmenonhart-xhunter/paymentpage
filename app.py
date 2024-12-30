import os
import uuid
from flask import Flask, render_template, request, jsonify, session, abort, Response
from threading import Lock
import time

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for Flask sessions

# Global variables to track users and waiting list
current_users = []
waiting_list = []
max_users = 2
lock = Lock()

# Secret key for the `/allow` endpoint
ALLOWED_SECRET_KEY = "super_secret_key"


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


@app.route("/allow", methods=["POST"])
def allow_users():
    global current_users, waiting_list

    # Validate the secret key
    secret_key = request.headers.get("Authorization")
    if secret_key != ALLOWED_SECRET_KEY:
        abort(403, description="Forbidden: Invalid secret key")

    with lock:
        if len(waiting_list) > 0:
            to_allow = min(len(waiting_list), max_users - len(current_users))
            current_users.extend(waiting_list[:to_allow])
            waiting_list = waiting_list[to_allow:]
    return jsonify({
        "message": "Allowed users moved from waiting list to active users.",
        "current_users": current_users,
        "waiting_list": waiting_list,
    })


@app.route("/leave", methods=["POST"])
def leave():
    global current_users, waiting_list
    user_id = session.get("user_id")  # Get the user's unique ID

    with lock:
        if user_id in current_users:
            current_users.remove(user_id)

        if user_id in waiting_list:
            waiting_list.remove(user_id)

    return jsonify({
        "message": "User left successfully.",
        "current_users": current_users,
        "waiting_list": waiting_list,
    })


@app.route("/status")
def status():
    """SSE endpoint to send real-time updates to users."""
    def generate():
        user_id = session.get("user_id")
        while True:
            with lock:
                # Check if the user is now in the current_users list
                is_allowed = user_id in current_users
                position = waiting_list.index(user_id) + 1 if user_id in waiting_list else -1
            yield f"data: {{\"is_allowed\": {str(is_allowed).lower()}, \"position\": {position}}}\n\n"
            time.sleep(1)

    return Response(generate(), content_type="text/event-stream")


if __name__ == "__main__":
    # Get the port from the environment variable (default to 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
