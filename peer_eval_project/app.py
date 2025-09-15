from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# ---------------------
# App setup
# ---------------------
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# ---------------------
# Models
# ---------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="user")  # admin / user
    coin = db.Column(db.Integer, default=Config.STARTER_COIN)

class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    golden_answer = db.Column(db.String(500), nullable=False)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey("level.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / approved / rejected

# ---------------------
# Login manager
# ---------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------
# DB Init
# ---------------------
with app.app_context():
    db.create_all()
    # สร้าง Admin จาก config ถ้ายังไม่มี
    if not User.query.filter_by(role="admin").first():
        admin = User(
            username=Config.ADMIN_USERNAME,
            password=generate_password_hash(Config.ADMIN_PASSWORD),
            role="admin",
            coin=0
        )
        db.session.add(admin)
        db.session.commit()
    # สร้าง Level ตัวอย่าง
    if Level.query.count() == 0:
        db.session.add(Level(question="print('Hello World')?", golden_answer="Hello World"))
        db.session.add(Level(question="2 + 2 = ?", golden_answer="4"))
        db.session.commit()

# ---------------------
# Routes
# ---------------------

# Home / Index
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for("register"))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role="user", coin=Config.STARTER_COIN)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.")
        return redirect(url_for("login"))
    return render_template("register.html")

# User Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, role="user").first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")

# Admin Login
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = User.query.filter_by(username=username, role="admin").first()
        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for("dashboard"))
        flash("Invalid admin credentials")
    return render_template("admin_login.html")

# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        levels = Level.query.all()
        users = User.query.filter(User.role=="user").all()
        return render_template("admin_dashboard.html", levels=levels, users=users)
    else:
        levels = Level.query.all()
        return render_template("user_dashboard.html", levels=levels)

# Admin Level Management
@app.route("/create-level", methods=["POST"])
@login_required
def create_level():
    if current_user.role != "admin":
        flash("Not authorized")
        return redirect(url_for("dashboard"))
    question = request.form["question"]
    golden_answer = request.form["golden_answer"]
    level = Level(question=question, golden_answer=golden_answer)
    db.session.add(level)
    db.session.commit()
    flash("Level created!")
    return redirect(url_for("dashboard"))

@app.route("/edit-level/<int:level_id>", methods=["POST"])
@login_required
def edit_level(level_id):
    if current_user.role != "admin":
        flash("Not authorized")
        return redirect(url_for("dashboard"))
    level = Level.query.get_or_404(level_id)
    level.question = request.form["question"]
    level.golden_answer = request.form["golden_answer"]
    db.session.commit()
    flash("Level updated!")
    return redirect(url_for("dashboard"))

@app.route("/delete-level/<int:level_id>")
@login_required
def delete_level(level_id):
    if current_user.role != "admin":
        flash("Not authorized")
        return redirect(url_for("dashboard"))
    level = Level.query.get_or_404(level_id)
    db.session.delete(level)
    db.session.commit()
    flash("Level deleted!")
    return redirect(url_for("dashboard"))

# Level submission
@app.route("/level/<int:level_id>", methods=["GET", "POST"])
@login_required
def level_view(level_id):
    level = Level.query.get_or_404(level_id)
    answers = Answer.query.filter_by(level_id=level.id).all()
    if request.method == "POST":
        if current_user.coin < 1:
            flash("Not enough coin to submit answer")
            return redirect(url_for("level_view", level_id=level.id))
        content = request.form["answer"]
        answer = Answer(content=content, user_id=current_user.id, level_id=level.id)
        current_user.coin -= 1
        db.session.add(answer)
        db.session.commit()
        flash("Answer submitted! 1 coin deducted.")
        return redirect(url_for("level_view", level_id=level.id))
    return render_template("level.html", level=level, answers=answers)

# Admin view answers per level
@app.route("/level-answers/<int:level_id>")
@login_required
def level_answers(level_id):
    if current_user.role != "admin":
        flash("Not authorized")
        return redirect(url_for("dashboard"))

    level = Level.query.get_or_404(level_id)
    answers = Answer.query.filter_by(level_id=level.id).all()
    return render_template("admin_level_answers.html", level=level, answers=answers)

# Approve/Reject
@app.route("/approve/<int:answer_id>")
@login_required
def approve(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    if current_user.role == "admin" or (current_user.role == "user" and current_user.id != answer.user_id):
        answer.status = "approved"
        current_user.coin += 1
        db.session.commit()
        flash("Answer approved! 1 coin added to you.")
    return redirect(url_for("level_view", level_id=answer.level_id))

@app.route("/reject/<int:answer_id>")
@login_required
def reject(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    if current_user.role == "admin" or (current_user.role == "user" and current_user.id != answer.user_id):
        answer.status = "rejected"
        db.session.commit()
        flash("Answer rejected!")
    return redirect(url_for("level_view", level_id=answer.level_id))

# Update user coin (Admin)
@app.route("/update-coin/<int:user_id>", methods=["POST"])
@login_required
def update_coin(user_id):
    if current_user.role != "admin":
        flash("Not authorized")
        return redirect(url_for("dashboard"))
    user = User.query.get_or_404(user_id)
    coin_change = int(request.form["coin"])
    user.coin += coin_change
    if user.coin < 0:
        user.coin = 0
    db.session.commit()
    flash(f"{user.username} coin updated!")
    return redirect(url_for("dashboard"))

# ---------------------
if __name__ == "__main__":
    app.run(debug=True)
