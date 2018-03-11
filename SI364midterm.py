###############################
####### SETUP (OVERALL) #######
###############################

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

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} -- (Search #: {})".format(self.name, self.id)

class User(db.Model):
    __tablename__ = "Users"
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    username = db.Column(db.String(64))

    def __repr__(self):
        return "{} (UserID {})".format(self.username, self.user_id)

class Places(db.Model):
    __tablename__ = "Places"
    zipcode = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(124))

    def __repr__(self):
        return "{} (Zipcode: {})".format(self.city, self.zipcode)

class Facts(db.Model):
    __tablename__ = "Facts"
    fact_id = db.Column(db.Integer, primary_key=True)
    fact = db.Column(db.Text)
    place_id = db.Column(db.Integer, db.ForeignKey("Places.zipcode"))
    poster_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"))

    def __repr__(self):
        return "{} (Zipcode: {})".format(self.fact, self.place_id)


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

# @app.route('/', methods=['GET', 'POST'])
# def home():
#     form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
#     if form.validate_on_submit():
#         name = form.name.data
#         user = Name.query.filter_by(name=name).first()
#         if user:
#             return redirect(url_for('city_facts_form'))
#         else:
#             newname = Name(name=name)
#             db.session.add(newname)
#             db.session.commit()
#         return redirect(url_for('user_info'))
#     return render_template('base.html',form=form)

#Main function
@app.route('/', methods=['GET', 'POST'])
def index():
    form = UserForm()
    if form.validate_on_submit():
        name = form.name.data.rstrip()
        username = form.username.data
        zipcode = form.zipcode.data
        fact = form.fact.data
        if User.query.filter_by(name=name, username=username).first():
            user = User.query.filter_by(name=name, username=username).first()
            print("User already exists!")
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
            url = "http://maps.googleapis.com/maps/api/geocode/json?address=" + zipcode
            data = requests.get(url)
            city = data.json()["results"][0]["formatted_address"]
            place = Places(zipcode=zipcode, city=city)
            db.session.add(place)
            db.session.commit()
            flash("New place added!")
            newfact = Facts(fact=fact, place_id=place.zipcode, poster_id=user.user_id)
            db.session.add(newfact)
            db.session.commit()
            flash("Added new fact!")
            return redirect(url_for("index"))

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("ERROR(S) IN FORM SUBMISSION! - " + str(errors))
    return render_template('base.html', form=form)

#View All Facts that have been submitted.
@app.route('/allfacts')
def all_facts():
    allfacts = Facts.query.all()
    facts = []
    for i in allfacts:
        place = Places.query.filter_by(zipcode=i.place_id).first()
        facts.append((i.fact,place.city))
    length = len(facts)
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

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("ERROR(S) IN FORM SUBMISSION! - " + str(errors))
    return render_template('zip-search.html', form=form)


#Additional WTForm that uses GET to add name to db and brings user to new page.
#The new page will display any name matches, as well as a list of search history (duplicate name searches will be incliuded.)
@app.route('/name-search', methods=['POST', 'GET'])
def name_search():
    form = NameForm()
    return render_template("name-search.html", form=form)

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

#Route to view names of all who have filled out the home form
@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

## Code to run the application...
if __name__ == "__main__":
    db.create_all()
    app.run(use_reloader=True,debug=True)

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
