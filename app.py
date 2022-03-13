from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

# this file is to be ignored
path = os.path.join(os.path.dirname(__file__), 'confidentialInfo.txt')
with open(path) as f:
    confidential_info = [content.strip() for content in f.readlines()]

# configs for the db
app = Flask(__name__)
app.permanent_session_lifetime = timedelta(days=5)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACN_MODIFICATIONS'] = False

# configs for the email
app.config['MAIL_SERVER'] = "smtp.mail.yahoo.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = confidential_info[0]
app.config['MAIL_PASSWORD'] = confidential_info[1]
app.config['SECRET_KEY'] = confidential_info[2]
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

db = SQLAlchemy(app)
mail = Mail(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"User('{self.username}, {self.email}')"

def isExistingUser(username, email):
    # used for the user entry check in the db
    existingUser = Users.query.filter_by(username=username).first()
    existingEmail = Users.query.filter_by(email=email).first()
    if (existingUser or existingEmail):
        return True
    return False

def addUser(username, email):
    user = Users(username=username, email=email)
    db.session.add(user)
    db.session.commit()

def sendEmail(email):
    token = s.dumps(email, salt='email-confirmed')
    msg = Message('Confirm Email', sender=app.config['MAIL_USERNAME'], recipients=[email])
    link = url_for('confirmEmail', token=token, _external=True)
    msg.body = 'Your link is {}'.format(link)
    mail.send(msg)

@app.route("/")
def home():
    # main landing page

    return render_template("index.html")

@app.route('/login', methods = ['GET','POST'])
def login():
    # workflow when 'Log In' is clicked.

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        if (not isExistingUser(username, email)):                   # when the user doesn't exist
            flash("The username does not exist. Please sign up.")
            return render_template("index.html") 
        else:                                                       # when the user does exist
            session.permanent = True
            session["user"] = username
            session["email"] = email
            flash("Login Successful!")
            return redirect(url_for("main"))

    if request.method == "GET":                                     # when landing on this page using URL, not POST request
        if "user" in session:                                       # if there is a active session
            flash("Already logged in!")
            return render_template("main.html")
        else:
            flash("Please login.")
            return render_template("index.html")

@app.route("/signup", methods=["POST","GET"])
def signup():
    # workflow when 'Sign Up' is clicked.

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]

        if (not isExistingUser(username, email)):                           # if there is no existing user, send a confirmation email.
            session["user"] = username                                      # when the user clicks on the link, the user will be added.
            session["email"] = email
            sendEmail(email)
            flash(f"Confirmation email has been sent to {email}!", "info")
            return redirect(url_for("home"))
        else:
            flash(f"This username or email already exists.", "info")
            return render_template("signup.html")

    elif "user" in session:                                                 # if there's an active session, redirect them to the main.
            flash("Already logged in!")
            return render_template("main.html")

    else:
        return render_template("signup.html")                               # when landing on this page using URL, not POST request

@app.route('/confirm_email/<token>', methods=['GET','POST'])
def confirmEmail(token):
    # this function is called when the user clicks on the confirmation email.

    try:
        email = s.loads(token, salt='email-confirmed', max_age=120)
        addUser(session["user"], session["email"])
        flash("Account has been successfully created for {}!".format(session["user"]), "info")
        session.pop("user", None)
        session.pop("email", None)
    except SignatureExpired:                # if the token timer is expired.
        return 'The token is expired'
    return redirect(url_for("home"))

@app.route("/main", methods=["POST","GET"])
def main():
    # main page where the queue display will happen.

    if "user" in session:
        user = session["user"]

        return render_template("main.html")
    else:
        flash("You are not logged in!")
        return redirect(url_for("home"))    

@app.route("/logout", methods=["GET","POST"])
def logout():
    # logs out the active session by clearing out the session.

    if "user" in session:
        user = session["user"]
        flash(f"You have been logged out, {user}!", "info")
    session.pop("user", None)
    session.pop("email", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    db.drop_all()
    db.create_all()
    app.run(debug=True, port = 9999)