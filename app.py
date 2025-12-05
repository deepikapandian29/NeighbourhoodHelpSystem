from flask import Flask, render_template, request, redirect, session, flash
from db import get_connection

app = Flask(__name__)
app.secret_key = "mysecretkey123"   # important for login session


# ------------------ HOME PAGE ------------------
@app.route("/")
def home():
    return render_template("home.html")


# ------------------ REGISTER ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        address = request.form["address"]

        con = get_connection()
        cur = con.cursor()

        cur.execute(
            "INSERT INTO users (name, email, password, phone, address) VALUES (%s, %s, %s, %s, %s)",
            (name, email, password, phone, address)
        )

        con.commit()
        con.close()

        flash("Registration successful! Please log in.", "success")
        return redirect("/login")

    return render_template("register.html")


# ------------------ LOGIN ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        con = get_connection()
        cur = con.cursor(dictionary=True)

        # First check if email exists
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if not user:
            flash("Email is incorrect", "error")
            con.close()
            return redirect("/login")

        # Now check password
        if user["password"] != password:
            flash("Password is incorrect", "error")
            con.close()
            return redirect("/login")

        con.close()

        # Login successful
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["email"] = user["email"]

        # If admin login
        if user["email"] == "admin@gmail.com":
            flash("Welcome Admin!", "success")
            return redirect("/admin")

        flash("Login successful", "success")
        return redirect("/user")

    return render_template("login.html")


# ------------------ USER DASHBOARD ------------------
@app.route("/user")
def user_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT category, description, location, status, created_at
        FROM help_requests
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (session["user_id"],))
    requests = cur.fetchall()

    con.close()

    return render_template("user_dashboard.html", name=session["name"], requests=requests)


# ------------------ REQUEST HELP ------------------
@app.route("/request_help", methods=["GET", "POST"])
def request_help():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        category = request.form["category"]
        location = request.form["location"]
        description = request.form["description"]

        con = get_connection()
        cur = con.cursor()

        cur.execute(
            "INSERT INTO help_requests (user_id, category, location, description) VALUES (%s, %s, %s, %s)",
            (session["user_id"], category, location, description)
        )

        con.commit()
        con.close()

        flash("Request submitted successfully!", "success")
        return redirect("/user")

    return render_template("request_help.html")


# ------------------ BROWSE ALL REQUESTS ------------------
@app.route("/browse_requests")
def browse_requests():
    if "user_id" not in session:
        return redirect("/login")

    q = request.args.get("q", "")

    con = get_connection()
    cur = con.cursor(dictionary=True)

    if q:
        cur.execute("""
            SELECT h.*, u.name AS requester
            FROM help_requests h
            JOIN users u ON h.user_id = u.id
            WHERE h.category LIKE %s OR h.description LIKE %s OR h.location LIKE %s
            ORDER BY h.created_at DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("""
            SELECT h.*, u.name AS requester
            FROM help_requests h
            JOIN users u ON h.user_id = u.id
            ORDER BY h.created_at DESC
        """)

    requests = cur.fetchall()
    con.close()

    return render_template("view_requests.html", requests=requests, q=q)


# ------------------ VIEW ONLY MY REQUESTS ------------------
@app.route("/view_requests")
def view_my_requests():
    if "user_id" not in session:
        return redirect("/login")

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT * FROM help_requests
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (session["user_id"],))
    requests = cur.fetchall()

    con.close()

    return render_template("view_requests.html", requests=requests)


# ------------------ HELPERS PAGE ------------------
@app.route("/helpers")
def helpers():
    if "user_id" not in session:
        return redirect("/login")

    service_filter = request.args.get("service", "")

    con = get_connection()
    cur = con.cursor(dictionary=True)

    if service_filter:
        cur.execute("""
            SELECT * FROM helpers
            WHERE service_type LIKE %s
            ORDER BY name
        """, (f"%{service_filter}%",))
    else:
        cur.execute("SELECT * FROM helpers ORDER BY name")

    helpers_list = cur.fetchall()
    con.close()

    return render_template("helpers.html", helpers=helpers_list, service=service_filter)



# ------------------ ADMIN DASHBOARD ------------------
@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if session["email"] != "admin@gmail.com":
        return "You are not admin!"

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    con.close()

    return render_template("admin_dashboard.html", users=users)


# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect("/")


# -----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
