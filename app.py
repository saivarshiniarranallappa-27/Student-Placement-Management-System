from flask import Flask, render_template, request, session, redirect
import sqlite3
import os

app = Flask(__name__)

app.secret_key = "placement123"

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Database Create
def init_db():

    conn = sqlite3.connect("placement.db")

    c = conn.cursor()

    # Students Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        email TEXT,

        password TEXT,

        resume TEXT
    )
    """)

    # Companies Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS companies (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        company_name TEXT,

        role TEXT,

        package TEXT
    )
    """)

    # Applications Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS applications (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        student_name TEXT,

        company_name TEXT,

        status TEXT
    )
    """)

    # Admin Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        password TEXT
    )
    """)

    # Default Admin
    c.execute("SELECT COUNT(*) FROM admin")

    admin_count = c.fetchone()[0]

    if admin_count == 0:

        c.execute("""
        INSERT INTO admin
        (username, password)

        VALUES
        ('admin', 'admin123')
        """)

    # Sample Companies
    c.execute("SELECT COUNT(*) FROM companies")

    count = c.fetchone()[0]

    if count == 0:

        c.execute("""
        INSERT INTO companies
        (company_name, role, package)

        VALUES
        ('Infosys', 'Python Developer', '4 LPA')
        """)

        c.execute("""
        INSERT INTO companies
        (company_name, role, package)

        VALUES
        ('TCS', 'Web Developer', '3.5 LPA')
        """)

        c.execute("""
        INSERT INTO companies
        (company_name, role, package)

        VALUES
        ('Wipro', 'Frontend Developer', '5 LPA')
        """)

    conn.commit()

    conn.close()


# Run Database
init_db()


# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# Register
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")

        email = request.form.get("email")

        password = request.form.get("password")

        resume = request.files["resume"]

        filename = resume.filename

        resume.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        conn = sqlite3.connect("placement.db")

        c = conn.cursor()

        c.execute("""
        INSERT INTO students
        (name, email, password, resume)

        VALUES (?, ?, ?, ?)
        """, (name, email, password, filename))

        conn.commit()

        conn.close()

        return "Registration Successful"

    return render_template("register.html")


# Student Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")

        password = request.form.get("password")

        conn = sqlite3.connect("placement.db")

        c = conn.cursor()

        c.execute("""
        SELECT * FROM students
        WHERE email=? AND password=?
        """, (email, password))

        user = c.fetchone()

        conn.close()

        if user:

            session["student_name"] = user[1]

            return redirect("/dashboard")

        else:

            return "Invalid Email or Password"

    return render_template("login.html")


# Student Dashboard
@app.route("/dashboard")
def dashboard():

    # Check login
    if "student_name" not in session:
        return redirect("/login")

    # Student name
    name = session["student_name"]

    # Search value
    search = request.args.get("search")

    # Database connect
    conn = sqlite3.connect("placement.db")

    c = conn.cursor()

    # If search entered
    if search:

        c.execute("""
        SELECT * FROM companies
        WHERE company_name LIKE ?
        OR role LIKE ?
        """, ('%' + search + '%',
              '%' + search + '%'))

    # If no search
    else:

        c.execute("""
        SELECT * FROM companies
        """)

    # Fetch companies
    companies = c.fetchall()

    conn.close()

    # Open dashboard page
    return render_template(
        "dashboard.html",
        name=name,
        companies=companies
    )


# Apply Company
@app.route("/apply/<company_name>")
def apply(company_name):

    # Check login
    if "student_name" not in session:
        return redirect("/login")

    student_name = session["student_name"]

    # Database connect
    conn = sqlite3.connect("placement.db")

    c = conn.cursor()

    # Check already applied or not
    c.execute("""
    SELECT * FROM applications
    WHERE student_name=? AND company_name=?
    """, (student_name, company_name))

    existing_application = c.fetchone()

    # If already applied
    if existing_application:

        conn.close()

        return "You already applied for this company"

    # Insert application
    c.execute("""
    INSERT INTO applications
    (student_name, company_name, status)

    VALUES (?, ?, ?)
    """, (student_name, company_name, "Pending"))

    conn.commit()

    conn.close()

    return "Applied Successfully"


# My Applications
@app.route("/my-applications")
def my_applications():

    if "student_name" not in session:
        return redirect("/login")

    student_name = session["student_name"]

    conn = sqlite3.connect("placement.db")

    c = conn.cursor()

    c.execute("""
    SELECT * FROM applications
    WHERE student_name=?
    """, (student_name,))

    applications = c.fetchall()

    conn.close()

    return render_template(
        "applications.html",
        applications=applications
    )


# Admin Login
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")

        conn = sqlite3.connect("placement.db")

        c = conn.cursor()

        c.execute("""
        SELECT * FROM admin
        WHERE username=? AND password=?
        """, (username, password))

        admin = c.fetchone()

        conn.close()

        if admin:

            session["admin"] = admin[1]

            return redirect("/admin-dashboard")

        else:

            return "Invalid Admin Credentials"

    return render_template("admin_login.html")


# Admin Dashboard
@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin-login")

    conn = sqlite3.connect("placement.db")

    c = conn.cursor()

    c.execute("SELECT * FROM companies")

    companies = c.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        companies=companies
    )


# Add Company
@app.route("/add-company", methods=["GET", "POST"])
def add_company():

    if "admin" not in session:
        return redirect("/admin-login")

    if request.method == "POST":

        company_name = request.form.get("company_name")

        role = request.form.get("role")

        package = request.form.get("package")

        conn = sqlite3.connect("placement.db")

        c = conn.cursor()

        c.execute("""
        INSERT INTO companies
        (company_name, role, package)

        VALUES (?, ?, ?)
        """, (company_name, role, package))

        conn.commit()

        conn.close()

        return redirect("/admin-dashboard")

    return render_template("add_company.html")
# Delete Company
@app.route("/delete-company/<int:id>")
def delete_company(id):

    # Check admin login
    if "admin" not in session:
        return redirect("/admin-login")

    # Database connect
    conn = sqlite3.connect("placement.db")

    c = conn.cursor()

    # Delete company
    c.execute("""
    DELETE FROM companies
    WHERE id=?
    """, (id,))

    conn.commit()

    conn.close()

    return redirect("/admin-dashboard")


# View Applications
@app.route("/view-applications")
def view_applications():

    # Check admin login
    if "admin" not in session:
        return redirect("/admin-login")

    # Database connect
    conn = sqlite3.connect("placement.db")

    c = conn.cursor()

    # Get applications
    c.execute("""
    SELECT * FROM applications
    """)

    applications = c.fetchall()

    conn.close()

    return render_template(
        "view_applications.html",
        applications=applications
    )


# Update Status
@app.route("/update-status/<int:id>/<status>")
def update_status(id, status):

    # Check admin login
    if "admin" not in session:
        return redirect("/admin-login")

    # Database connect
    conn = sqlite3.connect("placement.db")

    c = conn.cursor()

    # Update application status
    c.execute("""
    UPDATE applications
    SET status=?
    WHERE id=?
    """, (status, id))

    conn.commit()

    conn.close()

    # Redirect back
    return redirect("/view-applications")


# Logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# Run App
if __name__ == "__main__":
    app.run(debug=True)