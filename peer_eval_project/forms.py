from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class LevelForm(FlaskForm):
    question = TextAreaField("Question", validators=[DataRequired()])
    golden_answer = TextAreaField("Golden Answer", validators=[DataRequired()])
    submit = SubmitField("Save")

class AnswerForm(FlaskForm):
    answer = TextAreaField("Your Answer", validators=[DataRequired()])
    submit = SubmitField("Submit")
