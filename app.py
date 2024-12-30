import os
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, abort, url_for

app = Flask(__name__)

# Global variables to store links and their expiration
links = {}

@app.route("/")
def home():
    # Generate a unique link
    user_id = str(uuid.uuid4())
    expiration_time = datetime.now() + timedelta(minutes=5)
    links[user_id] = expiration_time

    # Generate unique link URL
    link_url = url_for("payment", user_id=user_id, _external=True)

    return render_template("index.html", link_url=link_url)


@app.route("/payment/<user_id>")
def payment(user_id):
    # Check if the link is valid
    if user_id not in links:
        return abort(404, description="Invalid payment link.")

    # Check if the link has expired
    if datetime.now() > links[user_id]:
        return abort(403, description="Payment link has expired.")

    # Render payment page
    return render_template(
        "payment.html",
        message="Your payment link is valid. Please proceed with payment.",
    )



@app.errorhandler(404)
def page_not_found(e):
    return (
        "<h1>404 Not Found</h1><p>The payment link you are trying to access is invalid.</p>",
        404,
    )


@app.errorhandler(403)
def link_expired(e):
    return (
        "<h1>403 Forbidden</h1><p>The payment link has expired. Please request a new one.</p>",
        403,
    )


if __name__ == "__main__":
    # Get the port from the environment variable (default to 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
