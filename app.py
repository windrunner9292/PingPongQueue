from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import datetime
from datetime import timedelta

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
PLAYTIME = 25  #in min

class Users(db.Model):
    # Users table definition
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    isParticipatingLeague = db.Column(db.Integer)
    rank = db.Column(db.Integer, unique=True)
    lastResult_ranked = db.Column(db.Integer)
    streak_ranked = db.Column(db.Integer)
    wins_ranked = db.Column(db.Integer)
    losses_ranked = db.Column(db.Integer)
    lastResult_normal = db.Column(db.Integer)
    streak_normal = db.Column(db.Integer)
    wins_normal = db.Column(db.Integer)
    losses_normal = db.Column(db.Integer)

    def __repr__(self):
        return f"User('{self.username}, {self.email}, {self.isParticipatingLeague}, {self.rank}')"

class Queue(db.Model):
    # Queue table definition
    id = db.Column(db.Integer, primary_key=True)
    firstUser = db.Column(db.String(20), unique=False, nullable=False)
    secondUser = db.Column(db.String(50), unique=False, nullable=False)
    isRankedMatch = db.Column(db.Integer)
    isTournamentMatch = db.Column(db.Integer)
    QueueEndTime = db.Column(db.DateTime)

    def __repr__(self):
        return f"User('{self.username}, {self.email}')"

class Admin(db.Model):
    # admin-controlled table--
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(50))
    isRankedEnabled = db.Column(db.Integer)
    leaderBoardHeader = db.Column(db.String(50))
    challengeRestrictionEnabled = db.Column(db.Integer)

    winner_eight_nine = db.Column(db.String(50))
    winner_five_twelve = db.Column(db.String(50))
    winner_seven_ten = db.Column(db.String(50))
    winner_six_eleven = db.Column(db.String(50))

    winner_first_ro8 = db.Column(db.String(50))
    winner_second_r08 = db.Column(db.String(50))
    winner_third_ro8 = db.Column(db.String(50))
    winner_fourth_ro8 = db.Column(db.String(50))

    winner_first_semifinal = db.Column(db.String(50))
    winner_second_semifinal = db.Column(db.String(50))

    winner_final = db.Column(db.String(50))
    winner_third_fourth = db.Column(db.String(50))

    def __repr__(self):
        return f"User('{self.username}')"

def isExistingUser(username, email):
    # used for the user entry check in the db
    existingUser = Users.query.filter_by(username=username).first()
    if not existingUser:
        return False
    if existingUser.email != email:
        return False
    return True

def isExistingAdmin(username, password):
    # admin entry check
    existingUser = Admin.query.filter_by(username=username).first()
    if not existingUser:
        return False
    if existingUser.password != password:
        return False
    return True

def getAllUsers():
    # returns the current users in the table
    return sorted([user.username for user in Users.query.all()])

def getCurrentQueue():
    # returns the current users in the table
    currentQueue = [(queue.firstUser, queue.secondUser, queue.id, queue.isRankedMatch, queue.QueueEndTime, queue.isTournamentMatch) for queue in Queue.query.all()]
    currentQueue.sort(key=lambda x:x[2])
    return currentQueue

def validateRankedMatch(firstUser, secondUser):
    # checking the valid ranked match

    firstUserRank = Users.query.filter_by(username=firstUser).first().rank
    secondUserRank = Users.query.filter_by(username=secondUser).first().rank
    challengeRestrictionEnabled = getchallengeRestrictionEnabled()
    if (firstUserRank == None or secondUserRank == None):                  # making sure the rank is not NULL.
        return False
    rank_diff = abs(firstUserRank - secondUserRank)                         # used for the rank diff restriction
    max_rank_diff = 5 if challengeRestrictionEnabled == 1 else 50
    return (Users.query.filter_by(username=firstUser).first().isParticipatingLeague == 1 and 
            Users.query.filter_by(username=secondUser).first().isParticipatingLeague == 1 and rank_diff < max_rank_diff)

def getCurrentLeaderBoard():
    # getting the list of ranked players.

    rank_users = []
    for user in Users.query.all():
        if user.isParticipatingLeague == 1:
            rank_users.append((user.username,
                               user.rank,
                               (user.lastResult_ranked, user.streak_ranked), 
                               ))
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
    if flag == getCurrentUserParticipationStatus(username):
        return
    currentRankUsers = getCurrentLeaderBoard()
    if flag == 0:                                                           # if the user is getting removed from rank:
        Users.query.filter_by(username=username).first().rank = None        # set that user's rank to NULL first    
        userFound = False
        for user in currentRankUsers:                                       # iterate through the list
            if user[0] == username:                                         # and correct the rank by negating rank by 1 for all player that were below that player.
                userFound = True
            elif userFound:
                Users.query.filter_by(username=user[0]).first().rank -= 1
    elif flag == 1:                                                                         # if the user is getting added to the rank:
        Users.query.filter_by(username=username).first().rank = len(currentRankUsers) + 1   # that user will be put at the end of the rank.
    Users.query.filter_by(username=username).first().isParticipatingLeague = flag
    db.session.commit()

def updateLeagueRanking(username, rank):
    Users.query.filter_by(username=username).first().rank = rank
    db.session.commit()

def recordRankedStatistics(username, result):
    if Users.query.filter_by(username=username).first().lastResult_ranked == None or Users.query.filter_by(username=username).first().lastResult_ranked != result:
        Users.query.filter_by(username=username).first().lastResult_ranked = result
        Users.query.filter_by(username=username).first().streak_ranked = 1

    elif Users.query.filter_by(username=username).first().lastResult_ranked == result:
        Users.query.filter_by(username=username).first().streak_ranked += 1

    if result == 1:
        Users.query.filter_by(username=username).first().wins_ranked += 1
    else:
         Users.query.filter_by(username=username).first().losses_ranked += 1
    db.session.commit()

def recordNormalStatistics(username, result):
    if Users.query.filter_by(username=username).first().lastResult_normal == None or Users.query.filter_by(username=username).first().lastResult_normal != result:
        Users.query.filter_by(username=username).first().lastResult_normal = result
        Users.query.filter_by(username=username).first().streak_normal = 1

    elif Users.query.filter_by(username=username).first().lastResult_normal == result:
        Users.query.filter_by(username=username).first().streak_normal += 1

    if result == 1:
        Users.query.filter_by(username=username).first().wins_normal += 1
    else:
         Users.query.filter_by(username=username).first().losses_normal += 1
    db.session.commit()

def addUser(username, email):
    # adds the user to the Users db; rank is NULL by default.
    user = Users(username=username,
                 email=email,
                 isParticipatingLeague=0,
                 streak_ranked = 0,
                 wins_ranked = 0,
                 losses_ranked = 0,
                 streak_normal = 0,
                 wins_normal = 0,
                 losses_normal = 0)
    db.session.add(user)
    db.session.commit()

def deleteUser(username):
    # delete the user from the table
    Users.query.filter_by(username=username).delete()
    db.session.commit()

def addAdminUser():
    # adds the user to the admin db
    user = Admin(username = 'admin',
                 password='nlsnow-pingpong',
                 isRankedEnabled = 0,
                 leaderBoardHeader = 'Leaderboard - S4 (locked)',
                 challengeRestrictionEnabled = 0)
    db.session.add(user)
    db.session.commit()

def resultCorrection(firstUser, secondUser, isRanked, firstUserStreak=1, secondUserStreak=1):
    actualWonPlayer = Users.query.filter_by(username=firstUser).first()
    actualLostPlayer = Users.query.filter_by(username=secondUser).first()
    if isRanked:
        actualWonPlayer.wins_ranked += 1
        actualWonPlayer.losses_ranked -= 1
        actualWonPlayer.lastResult_ranked = 1
        actualWonPlayer.streak_ranked = firstUserStreak
        
        actualLostPlayer.wins_ranked -= 1
        actualLostPlayer.losses_ranked += 1
        actualLostPlayer.lastResult_ranked = 0
        actualLostPlayer.streak_ranked = secondUserStreak

    else:
        actualWonPlayer.wins_normal += 1
        actualWonPlayer.losses_normal -= 1
        actualWonPlayer.lastResult_normal = 1
        actualWonPlayer.streak_normal = firstUserStreak
        
        actualLostPlayer.wins_normal -= 1
        actualLostPlayer.losses_normal += 1
        actualLostPlayer.lastResult_normal = 0
        actualLostPlayer.streak_normal = secondUserStreak
    db.session.commit()

def addQueue(firstUser, secondUser, isRankedMatch, isTournamentMatch, QueueEndTime):
    # adds the row to Queue db
    queue = Queue(firstUser=firstUser,
                  secondUser=secondUser,
                  isRankedMatch=isRankedMatch,
                  isTournamentMatch=isTournamentMatch,
                  QueueEndTime=QueueEndTime)
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

def getIsRankedEnabled():
    return Admin.query.filter_by(username='admin').first().isRankedEnabled

def updateIsRankedEnabled(flag):
    Admin.query.filter_by(username='admin').first().isRankedEnabled = flag
    db.session.commit()

def getCurrentLeaderBoardHeader():
    return Admin.query.filter_by(username='admin').first().leaderBoardHeader

def updateCurrentLeaderBoardHeader(newHeader):
    Admin.query.filter_by(username='admin').first().leaderBoardHeader = newHeader
    db.session.commit()

def getchallengeRestrictionEnabled():
    return Admin.query.filter_by(username='admin').first().challengeRestrictionEnabled

def updatechallengeRestrictionEnabled(flag):
    Admin.query.filter_by(username='admin').first().challengeRestrictionEnabled = flag
    db.session.commit()

def getCurrentTimeQueueEndTimeDiffInSeconds():
    if len(getCurrentQueue()) == 0:
        return 86000
    return (getCurrentQueue()[0][4] - datetime.datetime.now()).seconds

def resetCurrentTimeQueueEndTimeDiffInSeconds():
    if len(getCurrentQueue()) == 0:
        return
    firstQueue = getCurrentQueue()[0]
    Queue.query.filter_by(id=firstQueue[2], firstUser=firstQueue[0], secondUser=firstQueue[1]).first().QueueEndTime = datetime.datetime.now()+timedelta(minutes=PLAYTIME)
    db.session.commit()

def isMatchExpired():
    if len(getCurrentQueue()) == 0:
        return False
    return True if (getCurrentQueue()[0][4] - datetime.datetime.now()).days == -1 else False

def update_winner_eight_nine(username):
    Admin.query.filter_by(username='admin').first().winner_eight_nine = username
    db.session.commit()

def update_winner_five_twelve(username):
    Admin.query.filter_by(username='admin').first().winner_five_twelve = username
    db.session.commit()

def update_winner_seven_ten(username):
    Admin.query.filter_by(username='admin').first().winner_seven_ten = username
    db.session.commit()

def update_winner_six_eleven(username):
    Admin.query.filter_by(username='admin').first().winner_six_eleven = username
    db.session.commit()

def update_winner_first_ro8(username):
    Admin.query.filter_by(username='admin').first().winner_first_ro8 = username
    db.session.commit()

def update_winner_second_r08(username):
    Admin.query.filter_by(username='admin').first().winner_second_r08 = username
    db.session.commit()

def update_winner_third_ro8(username):
    Admin.query.filter_by(username='admin').first().winner_third_ro8 = username
    db.session.commit()

def update_winner_fourth_ro8(username):
    Admin.query.filter_by(username='admin').first().winner_fourth_ro8 = username
    db.session.commit()

def update_winner_first_semifinal(username):
    Admin.query.filter_by(username='admin').first().winner_first_semifinal = username
    db.session.commit()

def update_winner_second_semifinal(username):
    Admin.query.filter_by(username='admin').first().winner_second_semifinal = username
    db.session.commit()

def update_winner_final(username):
    Admin.query.filter_by(username='admin').first().winner_final = username
    db.session.commit()

def update_winner_third_fourth(username):
    Admin.query.filter_by(username='admin').first().winner_third_fourth = username
    db.session.commit()

def resetBracket():
    Admin.query.filter_by(username='admin').first().winner_eight_nine = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_five_twelve = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_seven_ten = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_six_eleven = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_first_ro8 = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_second_r08 = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_third_ro8 = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_fourth_ro8 = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_first_semifinal = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_second_semifinal = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_final = 'TBD'
    Admin.query.filter_by(username='admin').first().winner_third_fourth = 'TBD'
    db.session.commit()

def updateBracket(winner_eight_nine,winner_five_twelve,winner_seven_ten,winner_six_eleven,winner_first_ro8,winner_second_r08,winner_third_ro8,winner_fourth_ro8,winner_first_semifinal,winner_second_semifinal,winner_final):
    Admin.query.filter_by(username='admin').first().winner_eight_nine = winner_eight_nine
    Admin.query.filter_by(username='admin').first().winner_five_twelve = winner_five_twelve
    Admin.query.filter_by(username='admin').first().winner_seven_ten = winner_seven_ten
    Admin.query.filter_by(username='admin').first().winner_six_eleven = winner_six_eleven
    Admin.query.filter_by(username='admin').first().winner_first_ro8 = winner_first_ro8
    Admin.query.filter_by(username='admin').first().winner_second_r08 = winner_second_r08
    Admin.query.filter_by(username='admin').first().winner_third_ro8 = winner_third_ro8
    Admin.query.filter_by(username='admin').first().winner_fourth_ro8 = winner_fourth_ro8
    Admin.query.filter_by(username='admin').first().winner_first_semifinal = winner_first_semifinal
    Admin.query.filter_by(username='admin').first().winner_second_semifinal = winner_second_semifinal
    Admin.query.filter_by(username='admin').first().winner_final = winner_final
    #Admin.query.filter_by(username='admin').first().winner_third_fourth = winner_third_fourth
    db.session.commit()

def getBracket():
    return [Admin.query.filter_by(username='admin').first().winner_eight_nine,Admin.query.filter_by(username='admin').first().winner_five_twelve,
            Admin.query.filter_by(username='admin').first().winner_seven_ten,Admin.query.filter_by(username='admin').first().winner_six_eleven,
            Admin.query.filter_by(username='admin').first().winner_first_ro8,Admin.query.filter_by(username='admin').first().winner_second_r08,
            Admin.query.filter_by(username='admin').first().winner_third_ro8,Admin.query.filter_by(username='admin').first().winner_fourth_ro8,
            Admin.query.filter_by(username='admin').first().winner_first_semifinal,Admin.query.filter_by(username='admin').first().winner_second_semifinal,
            Admin.query.filter_by(username='admin').first().winner_final,Admin.query.filter_by(username='admin').first().winner_third_fourth]

'''Below are the Functions that interact with frontEnd directly'''

@app.route("/")
def home():
    # main landing page; renders the main page if logged in, login page otherwise.
    if "user" in session:
        return redirect(url_for("main"))
    else:
        return render_template("index.html")

@app.route('/login', methods = ['GET','POST'])
def login():
    # workflow when 'Log In' is clicked.

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        if (not isExistingUser(username, email)):                   # when the user doesn't exist
            flash("The username/email pair is not found.")
            return render_template("index.html") 
        else:                                                       # when the user does exist
            session.permanent = True
            session["user"] = username
            session["email"] = email
            session["temporary"] = False
            flash("Login Successful!")
            return redirect(url_for("main"))

    if request.method == "GET":                                     # when landing on this page using GET request
        if "user" in session:                                       # if there is a active session
            flash("Already logged in!")
            return render_template("main.html")
        else:
            flash("Please login.")
            return render_template("index.html")

@app.route('/hallOfFame', methods = ['GET'])
def hallOfFame():
    # workflow when 'Hall of Fame' is clicked.

    if request.method == "GET":                                     # when landing on this page using GET request
        if "user" in session:                                       # if there is a active session
            return render_template("hallOfFame.html")
        else:
            flash("Please login.")
            return render_template("index.html")

@app.route('/bracket', methods = ['GET','POST'])
def bracket():
    # workflow when 'Bracket' is clicked.

    currentRankUsers = getCurrentLeaderBoard()
    currentBracket = getBracket()
    if request.method == "GET":                                     # when landing on this page using GET request
        if "user" in session:                                       # if there is a active session
            return render_template("bracket.html",
                                    currentRankUsers=currentRankUsers,
                                    currentBracket=currentBracket)
        else:
            flash("Please login.")
            return render_template("index.html")
    if request.method == "POST":
        if request.form['action'] == 'Update':
            winner_eight_nine = request.form['winner_eight_nine']
            winner_five_twelve = request.form['winner_five_twelve']
            winner_seven_ten = request.form['winner_seven_ten']
            winner_six_eleven = request.form['winner_six_eleven']
            winner_first_ro8 = request.form['winner_first_ro8']
            winner_second_r08 = request.form['winner_second_r08']
            winner_third_ro8 = request.form['winner_third_ro8']
            winner_fourth_ro8 = request.form['winner_fourth_ro8']
            winner_first_semifinal = request.form['winner_first_semifinal']
            winner_second_semifinal = request.form['winner_second_semifinal']
            winner_final = request.form['winner_final']
            #winner_third_fourth = request.form['winner_third_fourth']
            updateBracket(winner_eight_nine,winner_five_twelve,winner_seven_ten,winner_six_eleven,
                          winner_first_ro8,winner_second_r08,winner_third_ro8,winner_fourth_ro8,
                          winner_first_semifinal,winner_second_semifinal,winner_final)
            currentBracket = getBracket()
            flash(f"Bracket info is updated.", "info")
            return render_template("bracket.html",
                                    currentRankUsers=currentRankUsers,
                                    currentBracket=currentBracket)

@app.route('/adminLogin', methods = ['GET','POST'])
def adminLogin():
    # workflow when 'Log In' is clicked for Admin.

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if (not isExistingAdmin(username, password)):                   # when the user doesn't exist
            flash("The username/password pair is not found.")
            return render_template("adminSignin.html") 
        else:                                                       # when the user does exist
            session.permanent = True
            session["user"] = username
            session["email"] = None
            session["temporary"] = False
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
        if ' ' in username:
            flash(f"Username must not contain space!", "info")
            return render_template("signup.html")

        if (not isExistingUser(username, email)):                           # if there is no existing user, send a confirmation email.
            #session["user"] = username                                      # when the user clicks on the link, the user will be added.
            #session["email"] = email
            #session["temporary"] = True
            #sendConfirmationEmail(username, email)
            addUser(username, email)
            #flash(f"Confirmation email has been sent to {email}!", "info")
            flash(f"Account is created for {username}!", "info")
            return redirect(url_for("home"))
        else:                                                               # if username or email already exists
            flash(f"This username or email already exists.", "info")
            return render_template("signup.html")

    elif "user" in session and "temporary" not in session:                  # if there's an active session, redirect them to the main.
            flash("Already logged in!")
            return render_template("main.html")
    else:
        return render_template("signup.html")                               # when landing on this page using GET request

@app.route("/profile", methods = ['GET','POST'])
def profile():
    if "user" in session:
        username = session["user"]
        isUserParticipatingLeague = getCurrentUserParticipationStatus(username)
        if request.method == "GET":                                                         # grabs the statistic info and displays it
                streakFlag_normal = Users.query.filter_by(username=username).first().lastResult_normal
                streak_normal = Users.query.filter_by(username=username).first().streak_normal
                wins_normal = Users.query.filter_by(username=username).first().wins_normal
                losses_normal = Users.query.filter_by(username=username).first().losses_normal
                totalGames_normal = wins_normal + losses_normal
                winRate_normal = round(wins_normal/(totalGames_normal)*100, 2) if totalGames_normal != 0 else 0
                
                streakFlag_ranked = Users.query.filter_by(username=username).first().lastResult_ranked
                streak_ranked = Users.query.filter_by(username=username).first().streak_ranked
                wins_ranked = Users.query.filter_by(username=username).first().wins_ranked
                losses_ranked = Users.query.filter_by(username=username).first().losses_ranked
                totalGames_ranked = wins_ranked + losses_ranked
                winRate_ranked = round(wins_ranked/(totalGames_ranked)*100, 2) if totalGames_ranked != 0 else 0

                return render_template("profile.html", isUserParticipatingLeague=isUserParticipatingLeague,
                                                    streakFlag_normal=streakFlag_normal,
                                                    streak_normal=streak_normal,
                                                    wins_normal=wins_normal,
                                                    losses_normal=losses_normal,
                                                    winRate_normal=winRate_normal,
                                                    streakFlag_ranked=streakFlag_ranked,
                                                    streak_ranked=streak_ranked,
                                                    wins_ranked=wins_ranked,
                                                    losses_ranked=losses_ranked,
                                                    winRate_ranked=winRate_ranked)
        elif request.method == "POST":
            if request.form['action'] == 'Join the League':                        
                updateLeagueParticipation(username, 1)
                return redirect(url_for("profile"))
            elif request.form['action'] == 'Leave the League':                                         
                updateLeagueParticipation(username, 0)
                return redirect(url_for("profile"))
    else:
        flash("You are not logged in!")
        return redirect(url_for("home"))



@app.route("/admin", methods = ['GET','POST'])
def admin():
    if "user" in session:
        username = session["user"]
        isRankedEnabled = getIsRankedEnabled()
        leaderBoardHeader = getCurrentLeaderBoardHeader()
        challengeRestrictionEnabled = getchallengeRestrictionEnabled()
        currentUsers = getAllUsers()
        if request.method == "GET":
            if username == 'admin':
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)
            else:
                return redirect(url_for("home"))
        if request.method == "POST":
            if request.form['action'] == 'Turn off ranked game mode':
                updateIsRankedEnabled(0)
                isRankedEnabled = getIsRankedEnabled()
                flash("Ranked game is now turned off.")
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)
            elif request.form['action'] == 'Turn on ranked game mode':
                updateIsRankedEnabled(1)
                isRankedEnabled = getIsRankedEnabled()
                flash("Ranked game is now turned on.")
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)

            elif request.form['action'] == 'Turn off challenge restriction':
                updatechallengeRestrictionEnabled(0)
                challengeRestrictionEnabled = getchallengeRestrictionEnabled()
                flash("Challenge restriction is now turned off.")
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)
            elif request.form['action'] == 'Turn on challenge restriction':
                updatechallengeRestrictionEnabled(1)
                challengeRestrictionEnabled = getchallengeRestrictionEnabled()
                flash("Challenge restriction is now turned on.")
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)
            elif request.form['action'] == 'Submit':
                if request.form['newHeader'] != '':
                    updateCurrentLeaderBoardHeader(request.form['newHeader'])
                flash("Table header is updated.")
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)
            elif request.form['action'] == 'Add':
                if request.form['username'] != '' and request.form['email'] != '':
                    username = request.form['username']
                    email = request.form['email']
                    if (not isExistingUser(username, email)):
                        addUser(username, email)
                        flash("{} is added.".format(username))
                    else:
                        flash("Either username or email already exists.")
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)
            elif request.form['action'] == 'Delete':
                username = request.form['userToDelete']
                if username not in currentUsers:
                    flash("{} doesn't exist.".format(username))
                    return render_template("admin.html",
                                            isRankedEnabled=isRankedEnabled,
                                            leaderBoardHeader=leaderBoardHeader,
                                            challengeRestrictionEnabled=challengeRestrictionEnabled)
                if Users.query.filter_by(username=username).first().isParticipatingLeague == 1:
                    updateLeagueParticipation(username,0)
                deleteUser(username)
                flash("{} is deleted.".format(username))
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)
            elif request.form['action'] == 'Reset ranked game participations':
                currentRankUsers = getCurrentLeaderBoard()[::-1]
                for user in currentRankUsers:
                    updateLeagueParticipation(user[0],0)
                flash("Ranked participation is cleared.")
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)
            elif request.form['action'] == 'Reset bracket':
                resetBracket()
                flash("Bracket is cleared.")
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)
            elif request.form['action'] == 'Swap':
                firstUser = request.form['firstUser']
                secondUser = request.form['secondUser']
                if firstUser not in currentUsers or secondUser not in currentUsers:
                    flash("One or more user(s) doesn't exist.".format(firstUser,secondUser))
                    return render_template("admin.html",
                                            isRankedEnabled=isRankedEnabled,
                                            leaderBoardHeader=leaderBoardHeader,
                                            challengeRestrictionEnabled=challengeRestrictionEnabled)
                firstUserRank = Users.query.filter_by(username=firstUser).first().rank
                secondUserRank = Users.query.filter_by(username=secondUser).first().rank
                if firstUserRank > secondUserRank:
                    swapRankings(firstUser,secondUser,1,0)
                else:
                    swapRankings(firstUser,secondUser,0,1)
                flash("Rank is swapped for {} and {}.".format(firstUser,secondUser))
                return render_template("admin.html",
                                        isRankedEnabled=isRankedEnabled,
                                        leaderBoardHeader=leaderBoardHeader,
                                        challengeRestrictionEnabled=challengeRestrictionEnabled)        
    else:
        flash("You are not logged in!")
        return redirect(url_for("home"))

@app.route("/adminSignIn", methods = ['GET','POST'])
def adminSignIn():
    return render_template("adminSignIn.html")

@app.route('/confirm_email/<token>', methods=['GET','POST'])
def confirmEmail(token):
    # this function is called when the user clicks on the confirmation email.
    try:
        if "user" in session:                                                               # if temporary user session is detected, add the user to the db.
            email = s.loads(token, salt='email-confirmed', max_age=TokenTimer)              # TokenTimer represents the time in seconds.
            addUser(session["user"], session["email"])
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
    if "user" in session:
        user = session["user"]
        currentUsers = getAllUsers()
        currentQueue = getCurrentQueue()
        currentRankUsers = getCurrentLeaderBoard()
        isRankedEnabled = getIsRankedEnabled()
        leaderBoardHeader = getCurrentLeaderBoardHeader()
        remainingTime = getCurrentTimeQueueEndTimeDiffInSeconds()
        matchExpired = isMatchExpired()
        """ if matchExpired:
                firstCurrentPlayer = currentQueue[0][0]
                secondCurrentPlayer = currentQueue[0][1]
                queueID = currentQueue[0][2]
                currentQueue = getCurrentQueue()
                currentQueueSize = len(currentQueue)
                deleteQueue(firstCurrentPlayer,secondCurrentPlayer,queueID)
                currentQueue = getCurrentQueue()
                if(currentQueueSize != 1):
                        flash("Email has been sent to {} and {}.".format(currentQueue[0][0],currentQueue[0][1]))
                        sendNotificationEmail(0)
                        return redirect(url_for("main",
                                            currentUsers=currentUsers,
                                            currentQueue=currentQueue,
                                            currentRankUsers=currentRankUsers,
                                            leaderBoardHeader=leaderBoardHeader,
                                            isRankedEnabled=isRankedEnabled,
                                            remainingTime=remainingTime)) """
        return render_template("main.html", 
                    currentUsers=currentUsers,
                    currentQueue=currentQueue,
                    currentRankUsers=currentRankUsers,
                    leaderBoardHeader=leaderBoardHeader,
                    isRankedEnabled=isRankedEnabled,
                    remainingTime=remainingTime)
    else:
        flash("You are not logged in!")
        return redirect(url_for("home"))

@app.route("/main", methods=["POST","GET"])
def main():
    # main page where the queue display will happen.
    if "user" in session:
        user = session["user"]
        currentUsers = getAllUsers()
        currentRankUsers = getCurrentLeaderBoard()
        isRankedEnabled = getIsRankedEnabled()
        leaderBoardHeader = getCurrentLeaderBoardHeader()
        currentQueue = getCurrentQueue()
        remainingTime = getCurrentTimeQueueEndTimeDiffInSeconds()
        if request.method == "POST":
            if request.form['action'] == 'Submit':                                      # button for adding the match to the queue
                firstPlayer = request.form["firstPlayer"]
                secondPlayer = request.form["secondPlayer"]
                isRankedMatch = "rankedMatch" in request.form
                isTournamentGame = "tourneyGame" in request.form
                if(isRankedMatch and not validateRankedMatch(firstPlayer,secondPlayer)):
                    flash("Invalid ranked match", 'error')
                    currentQueue = getCurrentQueue()
                    return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        leaderBoardHeader=leaderBoardHeader,
                                        isRankedEnabled=isRankedEnabled,
                                        remainingTime=remainingTime))
                if firstPlayer == secondPlayer:                                         # when accidentally adding same players
                    flash("You can't play yourself!", "error")
                    currentQueue = getCurrentQueue()
                    return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        leaderBoardHeader=leaderBoardHeader,
                                        isRankedEnabled=isRankedEnabled,
                                        remainingTime=remainingTime))
                if firstPlayer not in currentUsers or secondPlayer not in currentUsers:                 # when accidentally adding unregistered user
                    flash("Unregistered user.", "error")
                    currentQueue = getCurrentQueue()
                    return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        leaderBoardHeader=leaderBoardHeader,
                                        isRankedEnabled=isRankedEnabled,
                                        remainingTime=remainingTime))
                if (isRankedMatch):
                    addQueue(firstPlayer, secondPlayer, 1, 0, datetime.datetime.now()+timedelta(minutes=PLAYTIME))
                elif (not isRankedMatch and isTournamentGame):
                    addQueue(firstPlayer, secondPlayer, 0, 1, datetime.datetime.now()+timedelta(minutes=PLAYTIME))
                else:
                    addQueue(firstPlayer, secondPlayer, 0, 0, datetime.datetime.now()+timedelta(minutes=PLAYTIME))
                currentQueue = getCurrentQueue()
                return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        leaderBoardHeader=leaderBoardHeader,
                                        isRankedEnabled=isRankedEnabled,
                                        remainingTime=remainingTime))
            elif request.form['action'] == 'Game over':                                     # button for and deleting and optionally notifying the first queue.
                firstCurrentPlayer = request.form["firstCurrentPlayer"]
                secondCurrentPlayer = request.form["secondCurrentPlayer"]
                queueID = request.form["queueID"]
                dontSendEmailChecked = "dontSendEmail" in request.form
                dontRecordStatsChecked = "dontRecordStats" in request.form
                firstWins = "firstWins" in request.form
                secondWins = "secondWins" in request.form
                currentQueue = getCurrentQueue()
                currentQueueSize = len(currentQueue)
                if dontRecordStatsChecked:
                    deleteQueue(firstCurrentPlayer,secondCurrentPlayer,queueID)
                    currentQueue = getCurrentQueue()
                    resetCurrentTimeQueueEndTimeDiffInSeconds()
                    if(not dontSendEmailChecked and currentQueueSize != 1):
                        flash("Email has been sent to {} and {}.".format(currentQueue[0][0],currentQueue[0][1]))
                        sendNotificationEmail(0)
                    return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        leaderBoardHeader=leaderBoardHeader,
                                        isRankedEnabled=isRankedEnabled,
                                        remainingTime=remainingTime))
                #if (currentQueue[0][3]==1):                                                 # if the match is ranked:
                if (not firstWins and not secondWins):
                    flash("Winner must be chosen!",'error')
                    return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        leaderBoardHeader=leaderBoardHeader,
                                        isRankedEnabled=isRankedEnabled,
                                        remainingTime=remainingTime))
                elif (firstWins and secondWins):
                    flash("There can only be one winner!",'error')
                    return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        leaderBoardHeader=leaderBoardHeader,
                                        isRankedEnabled=isRankedEnabled,
                                        remainingTime=remainingTime))
                else:
                    if (currentQueue[0][3]==1):
                        swapRankings(firstCurrentPlayer,secondCurrentPlayer,firstWins,secondWins)
                        if firstWins:
                            recordRankedStatistics(firstCurrentPlayer, 1)
                            recordRankedStatistics(secondCurrentPlayer, 0)
                        else:
                            recordRankedStatistics(firstCurrentPlayer, 0)
                            recordRankedStatistics(secondCurrentPlayer, 1)
                    else:
                        if firstWins:
                            recordNormalStatistics(firstCurrentPlayer, 1)
                            recordNormalStatistics(secondCurrentPlayer, 0)
                        else:
                            recordNormalStatistics(firstCurrentPlayer, 0)
                            recordNormalStatistics(secondCurrentPlayer, 1)
                deleteQueue(firstCurrentPlayer,secondCurrentPlayer,queueID)
                currentQueue = getCurrentQueue()
                resetCurrentTimeQueueEndTimeDiffInSeconds()
                if(not dontSendEmailChecked and currentQueueSize != 1):
                    flash("Email has been sent to {} and {}.".format(currentQueue[0][0],currentQueue[0][1]))
                    sendNotificationEmail(0)
                return redirect(url_for("main",
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        leaderBoardHeader=leaderBoardHeader,
                                        isRankedEnabled=isRankedEnabled,
                                        remainingTime=remainingTime))
            elif request.form['action'] == 'Delete':                                          # button for deleting the n'th queue.
                firstPlayerInQueue = request.form["firstPlayerInQueue"]
                secondPlayerInQueue = request.form["secondPlayerInQueue"]
                queueID = request.form["queueID"]
                deleteQueue(firstPlayerInQueue,secondPlayerInQueue,queueID)
                currentQueue = getCurrentQueue()
                return redirect(url_for("main", 
                                        currentUsers=currentUsers,
                                        currentQueue=currentQueue,
                                        currentRankUsers=currentRankUsers,
                                        leaderBoardHeader=leaderBoardHeader,
                                        isRankedEnabled=isRankedEnabled,
                                        remainingTime=remainingTime))       
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
    #db.drop_all()        #DO NOT use this except Fred
    #db.create_all()      #DO NOT use this except Fred
    port = int(os.environ.get('PORT', 7000))  #PROD
    app.run(debug=True, port = port)          #PROD
    #app.run(debug=True, port = 8000)         #LOCAL
    #print("test")