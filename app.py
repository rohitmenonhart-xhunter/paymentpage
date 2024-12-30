import os
import uuid
from flask import Flask, render_template, request, jsonify, session
from threading import Lock

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for Flask sessions

# Global variables to track users and waiting list
current_users = []
waiting_list = []
max_users = 2
lock = Lock()

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
        return render_template("waiting.html", position=waiting_list.index(user_id) + 1)

@app.route("/allow", methods=["POST"])
def allow_users():
    global current_users, waiting_list
    with lock:
        if len(waiting_list) > 0:
            to_allow = min(len(waiting_list), max_users - len(current_users))
            current_users.extend(waiting_list[:to_allow])
            waiting_list = waiting_list[to_allow:]
    return jsonify({"message": "Allowed users moved from waiting list to active users."})

@app.route("/leave", methods=["POST"])
def leave():
    global current_users
    user_id = session.get("user_id")  # Get the user's unique ID
    with lock:
        if user_id in current_users:
            current_users.remove(user_id)
    return jsonify({"message": "User left successfully."})

if __name__ == "__main__":
    # Get the port from the environment variable (default to 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
