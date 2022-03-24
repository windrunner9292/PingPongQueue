from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import random

""" # LOCAL configs
path = os.path.join(os.path.dirname(__file__), 'confidentialInfo.txt')
with open(path) as f:
    confidential_info = [str(content.strip()) for content in f.readlines()]

path = os.path.join(os.path.dirname(__file__), 'players.txt')
with open(path) as f:
    user_info = [content.split(",") for content in f.readlines()]

path = os.path.join(os.path.dirname(__file__), 'players_ranked.txt')
with open(path) as f:
    ranked_user_info = [content.split(",") for content in f.readlines()]

app = Flask(__name__)
app.permanent_session_lifetime = timedelta(days=5)
app.config['SQLALCHEMY_DATABASE_URI'] = confidential_info[3]
app.config['SQLALCHEMY_TRACN_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = "smtp.mail.yahoo.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = confidential_info[0]
app.config['MAIL_PASSWORD'] = confidential_info[1]
app.config['SECRET_KEY'] = confidential_info[2]
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
TokenTimer = 300 """

# PROD configs
app = Flask(__name__)
app.permanent_session_lifetime = timedelta(days=5)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DBCONNECTION']
app.config['SQLALCHEMY_TRACN_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = "smtp.mail.yahoo.com"
#app.config['MAIL_PORT'] = 465
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ['MAILUSERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAILPASSWORD']
app.config['SECRET_KEY'] = os.environ['SECRETKEY']
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
TokenTimer = 300

db = SQLAlchemy(app)
mail = Mail(app)

class Users(db.Model):
    # Users table definition
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    isParticipatingLeague = db.Column(db.Integer)
    rank = db.Column(db.Integer, unique=True)

    def __repr__(self):
        return f"User('{self.username}, {self.email}, {self.isParticipatingLeague}, {self.rank}')"

class Queue(db.Model):
    # Queue table definition
    id = db.Column(db.Integer, primary_key=True)
    firstUser = db.Column(db.String(20), unique=False, nullable=False)
    secondUser = db.Column(db.String(50), unique=False, nullable=False)
    isRankedMatch = db.Column(db.Integer)

    def __repr__(self):
        return f"User('{self.username}, {self.email}')"

def isExistingUser(username, email):
    # used for the user entry check in the db
    existingUser = Users.query.filter_by(username=username).first()
    existingEmail = Users.query.filter_by(email=email).first()
    if (existingUser or existingEmail):
        return True
    return False

def getAllUsers():
    # returns the current users in the table
    return sorted([user.username for user in Users.query.all()])

def getCurrentQueue():
    # returns the current users in the table
    return [(queue.firstUser, queue.secondUser, queue.id, queue.isRankedMatch) for queue in Queue.query.all()]

def validateRankedMatch(firstUser, secondUser):
    # checking the valid ranked match
    rank_diff = abs(Users.query.filter_by(username=firstUser).first().rank - Users.query.filter_by(username=secondUser).first().rank)
    return (Users.query.filter_by(username=firstUser).first().isParticipatingLeague == 1 and 
            Users.query.filter_by(username=secondUser).first().isParticipatingLeague == 1 and rank_diff < 5)

def getCurrentLeaderBoard():
    # getting the list of ranked players.

    rank_users = []
    for user in Users.query.all():
        if user.isParticipatingLeague == 1:
            rank_users.append((user.username, user.rank))
    rank_users.sort(key=lambda i:i[1])
    return rank_users

def swapRankings(firstPlayer, secondPlayer, isFirstWin, isSecondWin):
    # Swapping the ranking if the winner's rank is lower than loser's.

    fp_rank = Users.query.filter_by(username=firstPlayer).first().rank
    sp_rank = Users.query.filter_by(username=secondPlayer).first().rank
    if (isFirstWin):
        if(fp_rank > sp_rank):
            Users.query.filter_by(username=secondPlayer).first().rank = 99
            Users.query.filter_by(username=firstPlayer).first().rank = sp_rank
            Users.query.filter_by(username=secondPlayer).first().rank = fp_rank
            db.session.commit()
    if (isSecondWin):
        if(sp_rank > fp_rank):
            Users.query.filter_by(username=secondPlayer).first().rank = 99
            Users.query.filter_by(username=firstPlayer).first().rank = sp_rank
            Users.query.filter_by(username=secondPlayer).first().rank = fp_rank
            db.session.commit()

def getCurrentUserParticipationStatus(username):
    return Users.query.filter_by(username=username).first().isParticipatingLeague

def updateLeagueParticipation(username, flag):
    Users.query.filter_by(username=username).first().isParticipatingLeague = flag
    db.session.commit()

def updateLeagueRanking(username, rank):
    Users.query.filter_by(username=username).first().rank = rank
    db.session.commit()

def addUser(username, email, rank):
    # adds the user to the Users db
    user = Users(username=username,
                 email=email,
                 isParticipatingLeague=0,
                 rank = rank)
    db.session.add(user)
    db.session.commit()

def addQueue(firstUser, secondUser, isRankedMatch):
    # adds the row to Queue db
    queue = Queue(firstUser=firstUser,
                  secondUser=secondUser,
                  isRankedMatch=isRankedMatch)
    db.session.add(queue)
    db.session.commit()

def deleteQueue(firstUser, secondUser,queueID):
    # delete the entry from the queue
    Queue.query.filter_by(id=queueID, firstUser=firstUser, secondUser=secondUser).delete()
    db.session.commit()

def sendConfirmationEmail(username, email):
    # used for the confirmation email.
    token = s.dumps(email, salt='email-confirmed')
    msg = Message('Confirm Email', sender=app.config['MAIL_USERNAME'], recipients=[email])
    link = url_for('confirmEmail', token=token, _external=True)
    msg.body = 'Link for {} is {}'.format(username, link) + "\n If you clicked on 'start over' button, please disregard this email. "
    mail.send(msg)

def sendNotificationEmail(iteration):
    # used for the notification email.
    currentQueue = getCurrentQueue()
    recipients = [Users.query.filter_by(username=currentQueue[iteration][0]).first().email,
                  Users.query.filter_by(username=currentQueue[iteration][1]).first().email]
    msg = Message('You are up next!', sender=app.config['MAIL_USERNAME'], recipients=recipients)
    msg.body = 'This is from automated email. You guys are up next.'
    mail.send(msg)

'''Below are the Functions that interact with frontEnd directly'''

@app.route("/")
def home():
    # main landing page; renders the main page if logged in, login page otherwise.
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

    if request.method == "GET":                                     # when landing on this page using GET request
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
            session["temporary"] = True
            sendConfirmationEmail(username, email)
            flash(f"Confirmation email has been sent to {email}!", "info")
            return redirect(url_for("home"))
        else:                                                               # if username or email already exists
            flash(f"This username or email already exists.", "info")
            return render_template("signup.html")

    elif "user" in session and "temporary" not in session:                  # if there's an active session, redirect them to the main.
            flash("Already logged in!")
            return render_template("main.html")
    else:
        return render_template("signup.html")                               # when landing on this page using GET request

@app.route('/confirm_email/<token>', methods=['GET','POST'])
def confirmEmail(token):
    # this function is called when the user clicks on the confirmation email.
    try:
        if "user" in session:                                                               # if temporary user session is detected, add the user to the db.
            email = s.loads(token, salt='email-confirmed', max_age=TokenTimer)              # TokenTimer represents the time in seconds.
            addUser(session["user"], session["email"], random.randint(50,200))
            flash("Account has been successfully created for {}!".format(session["user"]), "info")
            session.pop("user", None)                                                       # then delete the temporary user session info.
            session.pop("email", None)
            session.pop("temporary", None)
        else:
            flash("The link is unavailble.", "info")                                        # if the user clicked on "start over", then this fires.
    except SignatureExpired:                                                                # if the token timer is expired, redirect to main.
        flash("The token is expired.", "info")
    return redirect(url_for("home"))

@app.route("/redirectToMain", methods=["POST","GET"])
def redirectToMain():
    # used for the redirection to prevent unwanted Form submission.
    return redirect(url_for("main"))

@app.route("/showDashboard", methods=["POST","GET"])
def redirectMainGetRequest():
    # This handles the GET request for the main page.
    user = session["user"]
    currentUsers = getAllUsers()
    currentQueue = getCurrentQueue()
    currentRankUsers = getCurrentLeaderBoard()
    isJoiningLeague = getCurrentUserParticipationStatus(user)
    return render_template("main.html", 
                currentUsers=currentUsers,
                currentQueue=currentQueue,
                currentRankUsers=currentRankUsers,
                isJoiningLeague=isJoiningLeague)

@app.route("/main", methods=["POST","GET"])
def main():
    # main page where the queue display will happen.
    if "user" in session:
        user = session["user"]
        currentUsers = getAllUsers()
        currentRankUsers = getCurrentLeaderBoard()
        isJoiningLeague = getCurrentUserParticipationStatus(user)
        if request.method == "POST":
            if request.form['action'] == 'Submit':                                      # button for adding the match to the queue
                firstPlayer = request.form["firstPlayer"]
                secondPlayer = request.form["secondPlayer"]
                isRankedMatch = "rankedMatch" in request.form
                if(isRankedMatch and not validateRankedMatch(firstPlayer,secondPlayer)):
                    flash("Invalid ranked match", 'error')
                    currentQueue = getCurrentQueue()
                    return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        isJoiningLeague=isJoiningLeague))
                if firstPlayer == secondPlayer:                                         # when accidentally adding same players
                    flash("You can't play yourself!", "error")
                    currentQueue = getCurrentQueue()
                    return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        isJoiningLeague=isJoiningLeague))
                if (isRankedMatch):
                    addQueue(firstPlayer, secondPlayer, 1)
                else:
                    addQueue(firstPlayer, secondPlayer, 0)
                currentQueue = getCurrentQueue()
                return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        isJoiningLeague=isJoiningLeague))
            if request.form['action'] == 'Game over':                                     # button for and deleting and optionally notifying the first queue.
                firstCurrentPlayer = request.form["firstCurrentPlayer"]
                secondCurrentPlayer = request.form["secondCurrentPlayer"]
                queueID = request.form["queueID"]
                sendEmailChecked = "sendEmail" in request.form
                firstWins = "firstWins" in request.form
                secondWins = "secondWins" in request.form
                currentQueue = getCurrentQueue()
                if (currentQueue[0][3]==1):
                    if (not firstWins and not secondWins):
                        flash("Winner must be chosen!",'error')
                        return redirect(url_for("main",
                                            currentUsers=currentUsers,
                                            currentQueue=currentQueue,
                                            currentRankUsers=currentRankUsers,
                                            isJoiningLeague=isJoiningLeague))
                    elif (firstWins and secondWins):
                        flash("There can only be one winner!",'error')
                        return redirect(url_for("main",
                                            currentUsers=currentUsers,
                                            currentQueue=currentQueue,
                                            currentRankUsers=currentRankUsers,
                                            isJoiningLeague=isJoiningLeague))
                    else:
                        swapRankings(firstCurrentPlayer,secondCurrentPlayer,firstWins,secondWins)
                deleteQueue(firstCurrentPlayer,secondCurrentPlayer,queueID)
                currentQueue = getCurrentQueue()
                if(sendEmailChecked):
                    flash("Email has been sent to {} and {}.".format(currentQueue[0][0],currentQueue[0][1]))
                    sendNotificationEmail(0)
                return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        isJoiningLeague=isJoiningLeague))
            if request.form['action'] == 'Delete':                                          # button for deleting the n'th queue.
                firstPlayerInQueue = request.form["firstPlayerInQueue"]
                secondPlayerInQueue = request.form["secondPlayerInQueue"]
                queueID = request.form["queueID"]
                deleteQueue(firstPlayerInQueue,secondPlayerInQueue,queueID)
                currentQueue = getCurrentQueue()
                return redirect(url_for("main", 
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        isJoiningLeague=isJoiningLeague)) 
            if request.form['action'] == 'Join the League':                                          # button for deleting the n'th queue.
                #firstPlayerInQueue = request.form["firstPlayerInQueue"]
                #secondPlayerInQueue = request.form["secondPlayerInQueue"]
                #queueID = request.form["queueID"]
                updateLeagueParticipation(user, 1)
                currentQueue = getCurrentQueue()
                return redirect(url_for("main", 
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        isJoiningLeague=isJoiningLeague))
            if request.form['action'] == 'Leave the League':                                          # button for deleting the n'th queue.
                #firstPlayerInQueue = request.form["firstPlayerInQueue"]
                #secondPlayerInQueue = request.form["secondPlayerInQueue"]
                #queueID = request.form["queueID"]
                updateLeagueParticipation(user, 0)
                currentQueue = getCurrentQueue()
                return redirect(url_for("main", 
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        isJoiningLeague=isJoiningLeague))        
        if request.method == "GET":
            return redirect(url_for("redirectMainGetRequest"))
    else:
        flash("You are not logged in!")
        return redirect(url_for("home"))

@app.route("/logout", methods=["GET","POST"])
def logout():
    # logs out the active session by clearing out the session.

    if "user" in session:
        user = session["user"]
        flash(f"You have been logged out!", "info")
    session.pop("user", None)
    session.pop("email", None)
    session.pop("temporary", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    #db.drop_all()
    #db.create_all()
    port = int(os.environ.get('PORT', 7000))
    app.run(debug=True, port = port)
    #app.run(debug=True, port = 8000)