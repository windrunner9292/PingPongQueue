from enum import unique
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"User('{self.username}, {self.email}')"

def isExistingUser(username, email):
    existingUser = User.query.filter_by(username=username).first()
    existingEmail = User.query.filter_by(email=email).first()
    if (existingUser or existingEmail):
        return True
    return False
    
#Registration username password
def addUser(username, email):
    user = User(username=username, email=email)
    db.session.add(user)
    db.session.commit()

def passUser(password):
    if password is True:
        password = User(password=password)
        db.session.add(password)
        db.session.commit()

def getAllUsers():
    # returns the current users in the table
    
    return User.query.all()

####

@app.route('/', methods = ['GET','POST'])
def index():
    successMessage = ""
    return render_template("index.html",
                            successMessage=successMessage)

# used as a login page.
@app.route('/logIn', methods = ['GET','POST'])
def logIn():
    username = request.form['username'] #get the data input
    
    # login page can be landed in one of two ways: 1) by clicking submit button with username value, 2) and by clicking "Log in" button.
    # Therefore, if the username is NOT empty, add the username into the database upon the landing of the login.
    # if they land this page by clicking "Log in" button, no logic is needed.

    return render_template("ratingPage.html")

@app.route('/signup', methods = ['GET','POST'])
def goToSignUpPage():
    errorMessage = ""
    return render_template("signup.html",
                            errorMessage=errorMessage)

@app.route('/signup/result', methods = ['GET','POST'])
def signUp():
    username = request.form['username']    
    email = request.form['email']
    if (isExistingUser(username, email)):
        errorMessage = "The user already exists"
        return render_template("signup.html",
                                errorMessage=errorMessage)
    addUser(username, email)
    successMessage = "The user is successfully added."
    return render_template("index.html",
                            successMessage=successMessage)

# used as a main rating page.
@app.route('/viewRatingPage', methods = ['GET','POST'])
def viewRatingPage():
    # this page gets called by clicking submit button from the login page.
    # take the user input, check if it exists in the database, and if so, render the ratingPage.html.
    # if user doesn't exist, the following must happen per 교수님: "If the login fails, there should be some visual indication on the site 
    #                                                               that an invalid username was entered. 
    #                                                               An error message should be displayed to the user at minimum."
    # if the user doesn't exist:
    #    return render_template("errorPage.html")

    # relational database

    return render_template("ratingPage.html")

if __name__ == "__main__":
    #print(getAllUsers())
    db.drop_all()
    db.create_all()
    app.run(debug = True, port = 8000)  # turn this on to run the server
    #db.session.query(User).delete() # empties the table
    #getAllUsers()
    #db.create_all()
