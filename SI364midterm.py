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
        return "{} (ID: {})".format(self.name, self.id)

class User(db.Model):
    __tablename__ = "Users"
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), db.ForeignKey("names.name"))
    username = db.Column(db.String(64))
    password = db.Column(db.String(64))

    def __repr__(self):
        return "{} (UserID: {})".format(self.username, self.user_id)

class Places(db.Model):
    __tablename__ = "Places"
    location_id = db.Column(db.Integer, primary_key=True)
    zipcode = db.Column(db.Integer, unique=True)
    city = db.Column(db.String(124))

    def __repr__(self):
        return "{} (Zipcode: {})".format(self.city, self.zipcode)

class Facts(db.Model):
    __tablename__ = "Facts"
    fact_id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    place_id = db.Column(db.Integer, db.ForeignKey("Places.zipcode"))

    def __repr__(self):
        return "{} (Zipcode: {})".format(self.text, self.place_id)


###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name.",validators=[Required()])
    submit = SubmitField("Submit")

class UserForm(FlaskForm):
    name = StringField("Please enter your name.",validators=[Required()])
    username = StringField("Please enter a username:",validators=[Required(), Length(max=64, message="Username is must be less than 64 characters!")])
    zipcode = StringField("Please enter the zipcode of where you're from:", validators=[Required()])
    submit = SubmitField("Submit")

    def validate_username(self, field):
        if " " in field.data:
            raise ValidationError("Your display name must be one word!")

    def validate_password(self, field):
        if ("@" or "!" or "#" or "?" or "$") in field.data:
            raise ValidationError("Your password must contain at least one following $,!,#,@,$ characters!")

    def validate_zipcode(self, field):
        if len(field.data) != 5:
            raise ValidationError("Please enter a valid 5-digit zipcode!")

class FactForm(FlaskForm):
    text = StringField("Enter a fun fact: ", validators=[Required()])
    submit = SubmitField("Submit")


#######################
###### VIEW FXNS ######
#######################

@app.route('/', methods=['GET', 'POST'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        user = Name.query.filter_by(name=name).first()
        if user:
            return redirect(url_for('city_facts_form'))
        else:
            newname = Name(name=name)
            db.session.add(newname)
            db.session.commit()
        return redirect(url_for('user_info'))
    return render_template('base.html',form=form)

#Route to view names of all who have filled out the home form
@app.route('/names')
def all_names():
    names = Name.query.all()
    cityname = uform.zipcode.data
    return render_template('name_example.html',names=names)

#New users who come to the site will be asked to fill out their information
@app.route('/user-info', methods=['GET', 'POST'])
def user_info():
    uform = UserForm()
    if uform.validate_on_submit():
        username = uform.username.data
        password = uform.password.data
        zipcode = uform.zipcode.data
        session["zipcode"] = zipcode
        name = form.name.data
        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists! Try Another.")
        else:
            user = User(name=name, username=username, password=password, zipcode=zipcode)
            db.session.add(user)
            db.commit()
            return render_template("cityfacts-form.html", )
    return redirect(url_for("user_info"))

    errors = [v for v in uform.errors.values()]
    if len(errors) > 0:
        flash("!!!! THERE WAS AN ERROR IN YOUR SUBMISSION - " + str(errors))
    return render_template('user-info.html',form=uform)

@app.route('/cityfactsform', methods=['GET', 'POST'])
def city_facts_form():
    fform = FactForm()
    zipcode = session.get('zipcode')
    print(zipcode)
    return render_template('cityfacts-form.html', form=fform, zipcode=zipcode)

@app.route('/allfacts')
def all_facts():
    return render_template('all-facts.html')




## Code to run the application...
if __name__ == "__main__":
    db.create_all()
    app.run(use_reloader=True,debug=True)

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
