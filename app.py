from flask import Flask, request, session, flash, render_template, redirect, jsonify

from os import getenv
from dotenv import load_dotenv
import redis
import re
import db
import json
import uuid


db_manager = db.Manager(getenv("DATABASE_PATH"))
app = Flask(__name__, static_url_path="")
# session stores "token" : token
# redis stores token : json-encoded account
redis_client = redis.Redis(
    host=getenv("REDIS_HOST"), port=getenv("REDIS_PORT"), decode_responses=True
)


def get_header(**kwargs):
    return render_template("header.html", **kwargs)


def get_current_user(token, isAccount=False):  # pass in session token
    if isAccount:
        jsoned = json.loads(redis_client.get(token))
        return db.Account(
            int(jsoned["id"]),
            jsoned["fname"],
            jsoned["lname"],
            jsoned["email"],
            jsoned["pw"].encode("utf-8"),
            int(jsoned["type"]),
        )
    try:
        return json.loads(redis_client.get(token))
    except:
        return None


@app.route("/")
@app.route("/index")
def home():
    account = get_current_user(session.get("token"))
    return render_template("index.html", header=get_header(account=account))


@app.route("/login", methods=["GET"])
def get_login():
    token = session.get("token")
    account = get_current_user(token)
    if account != None:  # user is logged in
        return redirect("/donate")

    return render_template("login.html", header=get_header(account=account))


@app.route("/login", methods=["POST"])
def post_login():
    # get data from form
    email = request.form["email"]
    password = request.form["password"]

    # get account
    account = db_manager.get_account(email)

    # check password
    if account != None:
        if account.check_password(password):
            # create the session token + store on redis server
            token = uuid.uuid4().hex
            session["token"] = token
            redis_client.set(token, str(account))
            if int(account.type) == 1:
                return redirect("/donate")
            elif int(account.type) == 2:
                return redirect("/shelf")
        else:
            flash("Incorrect password.")
            return redirect("/login")
    else:
        # dummy check to prevent timing attack
        account = db.Account("", "", "", "", "", "")
        account.set_new_password(
            b"$2b$12$eUhSqBS3J/ZqoZFZW/iOWe/P7JlBybwNDIZTbflwUajSqr0d6vlce", True
        )
        account.check_password(password)
        flash("Account does not exist.")
        return redirect("/login")


@app.route("/register", methods=["GET"])
def register_get():
    token = session.get("token")
    account = get_current_user(token)
    # if you're already logged in, go to donate page
    try:
        if account is not None:
            return redirect("/donate", header=get_header(account=account))
        else:
            raise Exception()
    except:
        return render_template("register.html", header=get_header(account=account))


@app.route("/register", methods=["POST"])
def post_register():
    # get form data
    password = request.form["password"]
    email = request.form["email"]
    fname = request.form["fname"]
    lname = request.form["lname"]
    atype = request.form["account_type"]

    # validate password length and content
    if (
        len(password) < 8
        or not re.search(r"[A-Z]", password)
        or not re.search(r"\d", password)
    ):
        flash(
            "Password must be at least 8 characters long, contain at least one capital letter, and one number."
        )
        return render_template("register.html")

    # validate email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash("Invalid email address.")
        return render_template("register.html")

    # hash password
    new_account = db_manager.add_account(fname, lname, email, password, atype)
    if new_account != None:

        # create token
        token = uuid.uuid4().hex
        session["token"] = token
        redis_client.set(token, str(new_account))
        if int(atype) == 1:
            return redirect("/donate")
        elif int(atype) == 2:
            return redirect("/shelf")
    else:
        flash("Account creation failed. The user may already exist.")
        return redirect("/register")


@app.route("/donate")
def get_donate():
    account = get_current_user(session.get("token"))
    if not account:
        return redirect("/")

    if account["type"] == "2":
        return redirect("/")

    book_requests = db_manager.get_all_requests()
    return render_template(
        "donate.html",
        account=account,
        book_requests=book_requests,
        header=get_header(account=account),
    )


@app.route("/donate", methods=["POST"])
def donate_post():
    token = session.get("token")
    account = get_current_user(token)

    if account == None:
        return redirect("/")

    request_id = request.form.get("request_id")

    if request_id != None:
        return redirect(f"/checkout/{request_id}")
    else:
        # some other post request from somewhere foreign
        return redirect("/")


@app.route("/checkout/<request_id>")
def checkout_get(request_id):
    account = get_current_user(session.get("token"))
    if not account:
        return redirect("/")

    return render_template(
        "checkout.html",
        account=account,
        request_id=request_id,
        header=get_header(account=account),
    )


@app.route("/checkout/<request_id>", methods=["POST"])
def checkout_post(request_id):

    account = get_current_user(session.get("token"))
    if account == None:
        return redirect("/")
    try:
        db_manager.remove_request(request_id)
        return jsonify({"success": "200"}), 200
    except:
        return jsonify({"error": "300"}), 300


@app.route("/shelf")
def get_request():
    account = get_current_user(session.get("token"), True)
    if not account:
        return redirect("/")
    if int(account.type) != 2:
        return redirect("/")
    user_requests = db_manager.get_attorney_requests(account)
    rtn = []
    for user_request in user_requests:
        rtn.append(
            db.Request(
                user_request[0],
                user_request[1],
                user_request[2],
                user_request[3],
                user_request[4],
            )
        )
    return render_template(
        "shelf.html",
        account=account,
        requests=rtn,
        header=get_header(account=account),
    )


@app.route("/shelf", methods=["PUT"])
def put_shelf():
    # get isbn and prison name
    isbn = request.form["isbn"]
    prison = request.form["prison_title"]

    account = get_current_user(session.get("token"), True)
    if account is None:
        return redirect("/")

    # add to database
    book_request = db.Request(-1, account.id, isbn, prison)
    try:
        db_manager.add_request(book_request)
        return jsonify({"success": "200"}), 200
    except Exception as e:
        return jsonify({"error": "err"}), 300


@app.route("/shelf", methods=["DELETE"])
def delete_request():
    id = request.form["id"]

    account = get_current_user(session.get("token"))
    if account == None:
        return redirect("/")
    try:
        db_manager.remove_request(id)
        return jsonify({"success": "200"}), 200
    except:
        return jsonify({"error": "300"}), 300


@app.route("/logout")
def logout():
    redis_client.delete(session["token"])
    session.pop("token")
    return redirect("/")


if __name__ == "__main__":
    load_dotenv()
    hex_key = getenv("FLASK_SECRET_KEY")
    app.secret_key = bytes.fromhex(hex_key)
    app.run(port=int(getenv("FLASK_PORT")), debug=True)
