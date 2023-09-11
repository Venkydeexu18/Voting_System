from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'Deekshith__18'

instance_path = os.path.join(app.root_path, 'instance')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if not os.path.exists(instance_path):
    os.makedirs(instance_path)

db = SQLAlchemy(app)

class User(db.Model):
    aadhar = db.Column(db.String(12), primary_key=True)
    name = db.Column(db.String(50))

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vote = db.Column(db.String(50))
    aadhar = db.Column(db.String(10), db.ForeignKey('user.aadhar'))
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'aadhar' not in session:
            return redirect(url_for('registration'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        aadhar = request.form['aadhar']
        name = request.form['name']

        user = User.query.filter_by(aadhar=aadhar).first()
        if user:
            error = 'This Aadhar number already voted. Please choose a different username.'
            return render_template('registration.html', error=error)

        new_user = User(aadhar=aadhar, name=name)
        db.session.add(new_user)
        db.session.commit()

        session['aadhar'] = aadhar
        session['name'] = name
        return redirect(url_for('vote'))

    return render_template('registration.html')


@app.route('/vote', methods=['GET', 'POST'])
@login_required
def vote():
    aadhar = session.get('aadhar')

    if aadhar:
        user = User.query.filter_by(aadhar=aadhar).first()

        if request.method == 'POST':
            if user and not Vote.query.filter_by(aadhar=aadhar).first():
                vote = request.form['vote']
                new_vote = Vote(vote=vote, aadhar=aadhar, date=datetime.utcnow())
                db.session.add(new_vote)
                db.session.commit()
                return render_template('success.html')
            else:
                return redirect(url_for('registration'))
        else:
            politicians = [
                {'id': 1, 'name': 'Deekshith (A|X)', 'logo': '/static/ax.png'},
                {'id': 2, 'name': 'Narendra Modi (BJP)', 'logo': '/static/bjp.png'},
                {'id': 3, 'name': 'Rahul Gandhi (Congress)', 'logo': '/static/congress.svg'},
                {'id': 4, 'name': 'Pawan Kalyan (Janasena)', 'logo': '/static/janasena.jpeg'},
                {'id': 5, 'name': 'Chandrababu Naidu (TDP)', 'logo': '/static/tdp.png'},
                {'id': 6, 'name': 'Jagan (YSRCP)', 'logo': '/static/ysrcp.jpg'},
                {'id': 7, 'name': 'NOTA' , 'logo': '/static/nota.jpg'}
            ]
            return render_template('vote.html', politicians=politicians)
    else:
        return redirect(url_for('registration'))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == 'venkydeexu@ax.com' and password == 'vd18':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = 'Invalid email or password.'
            return render_template('admin_login.html', error=error)

    return render_template('admin_login.html')

@app.route('/admin/panel', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))

    votes = Vote.query.all()

    vote_count = {}
    for vote in votes:
        if vote.vote in vote_count:
            vote_count[vote.vote] += 1
        else:
            vote_count[vote.vote] = 1

    winner = max(vote_count, key=vote_count.get) if vote_count else None
    users = User.query.all()
    return render_template('admin_panel.html', users=users, votes=votes, vote_count=vote_count, winner=winner)


@app.route('/admin/user/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        aadhar = request.form['aadhar']
        name = request.form['name']

        user = User.query.filter_by(aadhar=aadhar).first()
        if user:
            error = 'User with the provided Aadhar number already exists.'
            return render_template('add_user.html', error=error)

        new_user = User(aadhar=aadhar, name=name)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('admin'))

    return render_template('add_user.html')


@app.route('/admin/user/edit/<string:aadhar>', methods=['GET', 'POST'])
def edit_user(aadhar):
    user = User.query.get(aadhar)

    if not user:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        user.name = request.form['name']
        db.session.commit()
        return redirect(url_for('admin'))

    return render_template('edit_user.html', user=user)


@app.route('/admin/user/delete/<string:aadhar>', methods=['POST'])
def delete_user(aadhar):
    user = User.query.get(aadhar)

    if not user:
        return redirect(url_for('admin'))

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin/vote/add', methods=['GET', 'POST'])
def add_vote():
    if request.method == 'POST':
        vote = request.form['vote']
        aadhar = request.form['aadhar']

        user = User.query.filter_by(aadhar=aadhar).first()
        if not user:
            error = 'User with the provided Aadhar number does not exist.'
            return render_template('add_vote.html', error=error)

        existing_vote = Vote.query.filter_by(aadhar=aadhar).first()
        if existing_vote:
            error = 'User with the provided Aadhar number has already voted.'
            return render_template('add_vote.html', error=error)

        new_vote = Vote(vote=vote, aadhar=aadhar, date=datetime.utcnow())
        db.session.add(new_vote)
        db.session.commit()

        return redirect(url_for('admin'))

    return render_template('add_vote.html')


@app.route('/admin/vote/edit/<int:id>', methods=['GET', 'POST'])
def edit_vote(id):
    vote = Vote.query.get(id)

    if not vote:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        vote.vote = request.form['vote']
        db.session.commit()
        return redirect(url_for('admin'))

    return render_template('edit_vote.html', vote=vote)


@app.route('/admin/vote/delete/<int:id>', methods=['POST'])
def delete_vote(id):
    vote = Vote.query.get(id)

    if not vote:
        return redirect(url_for('admin'))

    db.session.delete(vote)
    db.session.commit()
    return redirect(url_for('admin'))


if __name__ == '__main__':  
    app.run()
