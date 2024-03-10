from flask import Flask,render_template,request,redirect,url_for,session
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm,CSRFProtect
from wtforms import StringField,SubmitField,PasswordField,EmailField
from wtforms.validators import DataRequired
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user,login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
import os

notes = []

app = Flask(__name__)
bootstrap = Bootstrap5(app)

app.config["SECRET_KEY"] = os.environ.get('FLASK_KEY')
csrf = CSRFProtect(app)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI","sqlite:///lists.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin,db.Model):
    __tablename__ = "users"
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    email:Mapped[str]=mapped_column(String(100),unique=True)
    password:Mapped[str] = mapped_column(String(100))
    username:Mapped[str] = mapped_column(String(100))
    notes = relationship("Notes",back_populates="userNote")

class Notes(UserMixin,db.Model):
    __tablename__ = "notes"
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    note:Mapped[str] = mapped_column(String(300))
    userId:Mapped[int] = mapped_column(Integer,db.ForeignKey('users.id'))
    userNote = relationship("User",back_populates="notes")

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar()

class LoginForm(FlaskForm):

    email= StringField("Email",validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Submit")

class RegistrationForm(FlaskForm):
    username = StringField("UserName",validators=[DataRequired()])
    email= EmailField("Email",validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Submit")

class ListForm(FlaskForm):
    note = StringField("Write Your Task",validators=[DataRequired()])
    submit=SubmitField("Save")




@app.route('/', methods=["POST","GET"])
def login_page():
    wrong_info = False
    user_exist = False
    login_form = LoginForm()
    if request.method == "POST":
        email = login_form.email.data
        password = login_form.password.data
        login_form.email.data = ""
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            if user.password == password:
                login_user(user)
                return redirect(url_for('user_page'))
            else:
                wrong_info = True
        else:
            user_exist = True
    return render_template("login.html",form=login_form,loggedIn=current_user.is_authenticated,wrong_info = wrong_info,user_exist = user_exist)

@app.route('/signup',methods=["POST","GET"])
def signup_page():
    user_present = False
    signup_form = RegistrationForm()
    if request.method == "POST":
        email = signup_form.email.data
        password = signup_form.password.data
        username = signup_form.username.data
        signup_form.email.data = ""
        signup_form.username = ""

        user_exist = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user_exist:
            user_present = True
        else:
            user = User(
                email=email,
                password=password,
                username=username
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('user_page'))
    return render_template("signup.html",form=signup_form,loggedIn=current_user.is_authenticated,user_present = user_present)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/user')
@login_required
def user_page():
    all_notes = db.session.execute(db.select(Notes).where(Notes.userId == current_user.id)).scalars()
    return render_template('user.html',loggedIn=current_user.is_authenticated,notes = all_notes,current_user=current_user)

@app.route('/newnote',methods=["POST","GET"])
@login_required
def newnote():
    list_notes = ListForm()
    if request.method == "POST":
        new_note = Notes(
            note= list_notes.note.data,
            userId = current_user.id
        )
        db.session.add(new_note)
        db.session.commit()
        return redirect(url_for('user_page'))
    return render_template('newnote.html',form=list_notes,loggedIn=current_user.is_authenticated)

@app.route('/delete/<int:id>')
def deletenote(id):
    delete_note = db.session.execute(db.select(Notes).where(Notes.id == id)).scalar()
    db.session.delete(delete_note)
    db.session.commit()
    return redirect(url_for('user_page'))

if __name__ == "__main__":
    app.run(debug=True)