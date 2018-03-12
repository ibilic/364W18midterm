###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # Here, too
from flask_sqlalchemy import SQLAlchemy

from wtforms.fields.html5 import DateField

from twitter import Twitter, OAuth

## App setup code
app = Flask(__name__)

## All app.config values
app.config['SECRET_KEY'] = 'hard to guess string from si364'

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:si364@localhost/si364midterm"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def authentication():
    ACCESS_TOKEN = 'Enter_ACCESS_TOKEN'
    ACCESS_SECRET = 'Enter_ACCESS_SECRET'
    CONSUMER_KEY = 'Enter_CONSUMER_KEY'
    CONSUMER_SECRET = 'Enter_CONSUMER_SECRET'

    oauth = OAuth(ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
    t = Twitter(auth=oauth)
    return t

##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class TweetSearch(db.Model):
    __tablename__ = "words"
    id = db.Column(db.Integer,primary_key=True)
    words = db.Column(db.String(64))
    tweets = db.relationship('TweetInfo', backref='Name')

    def __repr__(self):
        return "{} (ID: {})".format(self.words, self.id)

class TweetInfo(db.Model):
    __tablename__ = "tweet"
    id = db.Column(db.Integer,primary_key=True)
    text = db.Column(db.String(280))
    date = db.column(db.String(11))
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'))

    def __repr__(self):
        return "{} (ID: {})".format(self.text, self.id)

class Cleaning(db.Model):
    __tablename__ = "schedule"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    # date = db.Column(db.DateTime, nullable=False,default=datetime.utcnow)
    date = db.Column(db.String(64))
    task = db.Column(db.String(64))
    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)


###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name.",validators=[Required()])
    submit = SubmitField()

class TweetForm(FlaskForm):
    def validate_word(self,field):
        if field.data[0] == '!':
            raise ValidationError('Word cannot start with !')

    word = StringField("Enter word to search twitter.",validators=[Required(),validate_word])
    submit = SubmitField()

class CleanForm(FlaskForm):
    name = StringField("Roommate Name: ",validators=[Required()])
    date = DateField("Cleaning Day: ",format='%Y-%m-%d')
    task = StringField("Enter task: ",validators=[Required()])
    submit = SubmitField()
#######################
###### VIEW FXNS ######
#######################

@app.route('/', methods=["GET","POST"])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name_data = form.name.data

        newname = Name(name=name_data)
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('base.html',form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

@app.route('/tweet', methods=["GET","POST"])
def tweetResponse():
    form = TweetForm()
    auth = authentication()

    if request.method == 'POST':
        param = form.word.data

        TweetSearchWord = TweetSearch.query.filter_by(words=param).first()
        if not TweetSearchWord:
            TweetSearchWord = TweetSearch(words=param)
            db.session.add(TweetSearchWord)
            db.session.commit()

        query = auth.search.tweets(q=param)
        for tweet in query['statuses']:
            tweet_date =  tweet['created_at'][:10]
            tweet_text = tweet['text']

            if TweetInfo.query.filter_by(text=tweet_text, word_id=TweetSearchWord.id).first() != None:
                flash("This word is already associated with this tweet, please enter another word")
                return redirect(url_for('tweetResponse'))

        table_entry = TweetInfo(word_id=TweetSearchWord.id, text=tweet_text, date=tweet_date)
        db.session.add(table_entry)
        db.session.commit()
        flash('Tweet Submitted')
    return render_template('tweetInfo.html', form=form)

@app.route('/tweetResult')
def twtresult():
    all_tweets = TweetInfo.query.all()
    tweet_things = [(tw.text, TweetSearch.query.filter_by(id=tw.word_id).first().words) for tw in all_tweets]
    return render_template('all_tweet.html',all_tweets=tweet_things,)

@app.route('/cleanPlan', methods=["GET", "POST"])
def clean():
    form = CleanForm()
    if form.validate_on_submit():
        n = form.name.data
        d = form.date.data
        t = form.task.data

        table__clean_entry = Cleaning(name=n,date=d,task=t)
        db.session.add(table__clean_entry)
        db.session.commit()
        flash('Schedule Submitted')
        return redirect(url_for('clean'))
    return render_template('cleanschedule.html', form=form)

@app.route('/schedule')
def plan():
    cleaning_data = Cleaning.query.all()
    return render_template('cleanResult.html', data = cleaning_data)

## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)
