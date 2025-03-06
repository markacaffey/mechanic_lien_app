from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required
from models import db, User

auth_blueprint = Blueprint("auth", __name__)
bcrypt = Bcrypt()

@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    """User Login Route"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            session["member_db"] = user.member_db  # Store user's database in session
            flash("✅ Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Invalid credentials, try again!", "danger")

    return render_template("login.html")

@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    """User Registration Route"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        member_db = f"databases/{username}.db"  # Assign unique database for each user

        if User.query.filter_by(username=username).first():
            flash("❌ Username already exists!", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, password=hashed_password, member_db=member_db)
        
        db.session.add(new_user)
        db.session.commit()

        flash("✅ Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_blueprint.route("/logout")
@login_required
def logout():
    """Logout Route"""
    logout_user()
    flash("✅ Logged out successfully.", "info")
    return redirect(url_for("auth.login"))
