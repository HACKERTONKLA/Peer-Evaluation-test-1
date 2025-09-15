from flask import Blueprint, render_template, redirect, url_for, request
from models import db, Level, Answer, Vote
from static.forms import AnswerForm

user_bp = Blueprint("user", __name__)

@user_bp.route("/")
def home():
    levels = Level.query.all()
    return render_template("index.html", levels=levels)

@user_bp.route("/level/<int:level_id>", methods=["GET", "POST"])
def level_detail(level_id):
    level = Level.query.get_or_404(level_id)
    form = AnswerForm()
    if form.validate_on_submit():
        new_answer = Answer(user="student", level_id=level.id, answer=form.answer.data)
        db.session.add(new_answer)
        db.session.commit()
        return redirect(url_for("user.level_detail", level_id=level.id))
    answers = Answer.query.filter_by(level_id=level.id).all()
    return render_template("level_detail.html", level=level, form=form, answers=answers)

@user_bp.route("/vote/<int:answer_id>/<string:vote>")
def vote_answer(answer_id, vote):
    new_vote = Vote(answer_id=answer_id, voter="student", vote=vote)
    db.session.add(new_vote)
    db.session.commit()
    return redirect(request.referrer)
