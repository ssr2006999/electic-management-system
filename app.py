from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "shruti_manaswi"

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT,
        address TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS electricians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        skill_level TEXT,
        availability TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        customer_id INTEGER,
        electrician_id INTEGER,
        status TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (id),
        FOREIGN KEY (electrician_id) REFERENCES electricians (id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS billing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        amount REAL NOT NULL,
        payment_status TEXT,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        message TEXT,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    """)
    conn.commit()
    conn.close()

create_tables()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password),
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another.", "danger")
            return redirect(url_for("register"))
        finally:
            conn.close()
            
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/customers", methods=["GET", "POST"])
def customers():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    if request.method == "POST":
        name = request.form.get("name")
        contact = request.form.get("contact")
        address = request.form.get("address")
        if name:
            conn.execute(
                "INSERT INTO customers (name, contact, address) VALUES (?, ?, ?)",
                (name, contact, address),
            )
            conn.commit()
            flash("New customer added successfully!", "success")
            return redirect(url_for("customers"))

    all_customers = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    conn.close()
    bg_image_url = url_for('static', filename='images/customer_icon.png')
    return render_template("customers.html", customers=all_customers, page_background_image=bg_image_url)

@app.route("/electricians", methods=["GET", "POST"])
def electricians():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    if request.method == "POST":
        name = request.form.get("name")
        skill_level = request.form.get("skill_level")
        availability = request.form.get("availability")
        if name:
            conn.execute(
                "INSERT INTO electricians (name, skill_level, availability) VALUES (?, ?, ?)",
                (name, skill_level, availability),
            )
            conn.commit()
            flash("New electrician added successfully!", "success")
            return redirect(url_for("electricians"))

    all_electricians = conn.execute("SELECT * FROM electricians ORDER BY name").fetchall()
    conn.close()
    bg_image_url = url_for('static', filename='images/electrician_icon.png')
    return render_template("electricians.html", electricians=all_electricians, page_background_image=bg_image_url)

@app.route("/projects", methods=["GET", "POST"])
def projects():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    if request.method == "POST":
        project_name = request.form.get("project_name")
        customer_id = request.form.get("customer_id")
        electrician_id = request.form.get("electrician_id")
        status = request.form.get("status")
        if project_name and customer_id and electrician_id and status:
            conn.execute(
                "INSERT INTO projects (project_name, customer_id, electrician_id, status) VALUES (?, ?, ?, ?)",
                (project_name, customer_id, electrician_id, status),
            )
            conn.commit()
            flash("New project created successfully!", "success")
            return redirect(url_for("projects"))

    all_projects = conn.execute("""
        SELECT p.id, p.project_name, c.name AS customer_name, e.name AS electrician_name, p.status
        FROM projects p
        LEFT JOIN customers c ON p.customer_id = c.id
        LEFT JOIN electricians e ON p.electrician_id = e.id
        ORDER BY p.id DESC
    """).fetchall()
    all_customers = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    all_electricians = conn.execute("SELECT * FROM electricians ORDER BY name").fetchall()
    conn.close()
    bg_image_url = url_for('static', filename='images/projects_icon.png')
    return render_template("projects.html", projects=all_projects, customers=all_customers, electricians=all_electricians, page_background_image=bg_image_url)

@app.route("/billing", methods=["GET", "POST"])
def billing():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    if request.method == "POST":
        project_id = request.form.get("project_id")
        amount = request.form.get("amount")
        payment_status = request.form.get("payment_status")
        if project_id and amount and payment_status:
            conn.execute(
                "INSERT INTO billing (project_id, amount, payment_status) VALUES (?, ?, ?)",
                (project_id, amount, payment_status),
            )
            conn.commit()
            flash("Billing record added successfully!", "success")
            return redirect(url_for("billing"))

    all_billing = conn.execute("""
        SELECT b.id, p.project_name, b.amount, b.payment_status
        FROM billing b
        LEFT JOIN projects p ON b.project_id = p.id
        ORDER BY b.id DESC
    """).fetchall()
    all_projects = conn.execute("SELECT * FROM projects ORDER BY project_name").fetchall()
    conn.close()
    bg_image_url = url_for('static', filename='images/billing_icon.png')
    return render_template("billing.html", billing=all_billing, projects=all_projects, page_background_image=bg_image_url)

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    if request.method == "POST":
        project_id = request.form.get("project_id")
        message = request.form.get("message")
        if project_id and message:
            conn.execute(
                "INSERT INTO feedback (project_id, message) VALUES (?, ?)",
                (project_id, message),
            )
            conn.commit()
            flash("Feedback submitted successfully!", "success")
            return redirect(url_for("feedback"))

    all_feedback = conn.execute("""
        SELECT f.id, p.project_name, f.message
        FROM feedback f
        LEFT JOIN projects p ON f.project_id = p.id
        ORDER BY f.id DESC
    """).fetchall()
    all_projects = conn.execute("SELECT * FROM projects ORDER BY project_name").fetchall()
    conn.close()
    bg_image_url = url_for('static', filename='images/feedback_icon.png')
    return render_template("feedback.html", feedback=all_feedback, projects=all_projects, page_background_image=bg_image_url)

if __name__ == "__main__":
    app.run(debug=True)
