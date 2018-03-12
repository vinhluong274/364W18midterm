## Import statements
import os, requests, json
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, StringField, SubmitField, RadioField, DateField, IntegerField, BooleanField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length, Email, Regexp # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True
## All app.config values
app.config['SECRET_KEY'] = "hardtoguessstring"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://vinhluong@localhost/364midterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)
manager = Manager(app)


######################################
######## HELPER FXNS (If any) ########
######################################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


##################
##### MODELS #####
##################
#Four Models Total
#This model stores any name that is entered into the Name Search Form.
#This model will allow unlimited duplicates.
class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} -- (Search # {})".format(self.name, self.id)

#This model stores users' name and desired username.
class User(db.Model):
    __tablename__ = "Users"
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    username = db.Column(db.String(64))

    def __repr__(self):
        return "{} (UserID {})".format(self.username, self.user_id)

#This database will store facts about certain places. It has a many to one relationship with the places model below.
class Facts(db.Model):
    __tablename__ = "Facts"
    fact_id = db.Column(db.Integer, primary_key=True)
    fact = db.Column(db.Text)
    place_id = db.Column(db.Integer, db.ForeignKey("Places.zipcode"))
    poster_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"))

    def __repr__(self):
        return "{} (Zipcode: {})".format(self.fact, self.place_id)

#This stores information about zipcodes and names of the cities those codes belong to. This has a one to many relationship with the Facts model.
#One place can have many interesting facts.
class Places(db.Model):
    __tablename__ = "Places"
    zipcode = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(124))

    def __repr__(self):
        return "{} (Zipcode: {})".format(self.city, self.zipcode)

###################
###### FORMS ######
###################

#This was the original Form included with the code.
#I changed it to be a search form that stores all searches. That way, users can add as many duplicates as they want.
class NameForm(FlaskForm):
    name = StringField("Search facts by name: ",validators=[Required()])
    submit = SubmitField("Search")

class UserForm(FlaskForm):
    name = StringField("Please enter your name: ",validators=[Required()])
    username = StringField("Please enter a username: ",validators=[Required(), Length(max=64, message="Username is must be less than 64 characters!")])
    zipcode = StringField("Please enter the zipcode of where you're from: ", validators=[Required()])
    fact = StringField("Enter a fun fact: ", validators=[Required()])
    submit = SubmitField("Submit")

    def validate_username(self, field):
        if len(field.data.split()) > 1:
            raise ValidationError("Your username must be one word!")

    def validate_zipcode(self, field):
        if len(field.data) != 5:
            raise ValidationError("Please enter a valid 5-digit zipcode!")

class ZipForm(FlaskForm):
    zipcode = StringField("Search facts by zipcode: ", validators=[Required()])
    submit = SubmitField("Search")

    def validate_zipcode(self, field):
        if len(field.data) != 5:
            raise ValidationError("Please enter a valid 5-digit zipcode!")

#######################
###### VIEW FXNS ######
#######################

#Main function. This is the home page and presents users with a form that asks for their name, username, zipcode, and a fun fact for the zipcode area they entered.
#Depending on whether the user, username, or zipcode already exists in the databases a message will be displayed on the same page explaining such. New names, usernames, and zipcodes will be added to the database.
#If there is a new zipcode, the function will make a request to Google's Goecoding API to gather city, state, and country details about the zipcode entered.
#If name, username, zipcode, and fact entered all exist in the databases and are connected to the same user, the function will not store the data, but display that it was already entered.
#No Identical Submission allowed.
@app.route('/', methods=['GET', 'POST'])
def index():
    form = UserForm()
    if form.validate_on_submit():
        name = form.name.data.rstrip()
        username = form.username.data
        zipcode = form.zipcode.data
        fact = form.fact.data
        if (User.query.filter_by(name=name, username=username).first()) and (Facts.query.filter_by(fact=fact, place_id=zipcode).first()):
            flash("An identical submission has already been made!")
            return render_template('home.html', form=form)
        else:
            if User.query.filter_by(name=name, username=username).first():
                user = User.query.filter_by(name=name, username=username).first()
                flash("User already exists")
            else:
                user = User(name=name, username=username)
                db.session.add(user)
                db.session.commit()
                flash("New user info added!")
            if (Places.query.filter_by(zipcode=zipcode).first()):
                flash("Zipcode of place already stored!")
                place = Places.query.filter_by(zipcode=zipcode).first()
                newfact = Facts(fact=fact, place_id=place.zipcode, poster_id=user.user_id)
                db.session.add(newfact)
                db.session.commit()
                flash("Added new fact!")
            else:
                url ="https://maps.googleapis.com/maps/api/geocode/json?address="+ zipcode + "&key=AIzaSyDn5BePWvs0CpWjZoSKyYaHSZYQSqCHpAc"
                data = requests.get(url)
                city = data.json()["results"][0]["formatted_address"]
                place = Places(zipcode=zipcode, city=city)
                db.session.add(place)
                db.session.commit()
                flash("New zipcode added!")
                newfact = Facts(fact=fact, place_id=place.zipcode, poster_id=user.user_id)
                db.session.add(newfact)
                db.session.commit()
                flash("Added new fact!")
                return render_template('home.html', form=form)
    errors = form.errors.values()
    if len(errors) > 0:
        for i in errors:
            flash("Error in Submission: " + str(i))
    return render_template('home.html', form=form)

#View All Facts that have been submitted.
@app.route('/allfacts')
def all_facts():
    allfacts = Facts.query.all()
    facts = []
    for i in allfacts:
        place = Places.query.filter_by(zipcode=i.place_id).first()
        facts.append((i.fact,place.city))
    length = len(facts)
    print(facts)
    return render_template('all-facts.html', facts=facts, length=length)

#Additional WTForm to that uses POST to search facts by zipcode and displays results them on the same page.
@app.route('/zipcode-search', methods=['POST', 'GET'])
def zip_search():
    form = ZipForm()
    if form.validate_on_submit():
        zipcode = form.zipcode.data
        results = Facts.query.filter_by(place_id=zipcode).all()
        print(len(results))
        if results:
            for i in results:
                place = Places.query.filter_by(zipcode=i.place_id).first()
                flash("{} -- {}".format(i.fact, place.city))
            return redirect(url_for("zip_search"))
        else:
            flash("No facts matching {}".format(zipcode))
            return redirect(url_for("zip_search"))

    errors = form.errors.values()
    if len(errors) > 0:
        for i in errors:
            flash("Error in Submission: " + str(i))
    return render_template('zip-search.html', form=form)


#Additional WTForm that uses GET to add name to db and brings user to new page.
#The new page will display any name matches, as well as a list of search history (duplicate name searches will be incliuded.)
@app.route('/name-search', methods=['POST', 'GET'])
def name_search():
    form = NameForm()
    return render_template("name-search.html", form=form)

#This is the redirect page for the previous function. It will use data from the previous form to query the database and display any facts entered by the name searched.
@app.route('/name-results', methods=['POST', 'GET'])
def name_results():
    name = request.args["name"]
    newname = Name(name=name)
    db.session.add(newname)
    db.session.commit()
    results = User.query.filter_by(name=name).all()
    facts = []
    for user in results:
        poster = Facts.query.filter_by(poster_id=user.user_id).first()
        place = Places.query.filter_by(zipcode=poster.place_id).first()
        facts.append((poster.fact, place.city))
    length=len(facts)
    return render_template("name-results.html", name=name, length=length, facts=facts)

#Route to view all of the names that have been entered into the name search form. Duplicates are allowed. This is a slight adaptation of the code that was given to us.
@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

## Code to run the application...
# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
if __name__ == "__main__":
    db.create_all()#creates all the databases needed if not any
    app.run(use_reloader=True,debug=True)
