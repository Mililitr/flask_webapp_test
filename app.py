from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    balance = db.Column(db.Integer, nullable=False)

    def __init__(self, username, balance):
        self.username = username
        self.balance = balance

    def add(self):
        db.session.add(self)
        db.session.commit()

    def update(self, new_username=None, new_balance=None):
        if new_username:
            self.username = new_username
        if new_balance:
            self.balance = new_balance
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return User.query.all()

    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def update_balance(username, new_balance):
        user = User.get_by_username(username)
        if user:
            user.balance = new_balance
            user.update()

import requests

def fetch_weather(city):
    api_key = "66f46fe5e696fff6f4c5873b27ca7573"
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}appid={api_key}&q={city}"
    response = requests.get(complete_url)
    data = response.json()

    if data["cod"] != "404":
        main_data = data["main"]
        current_temperature = main_data["temp"]
        return current_temperature
    else:
        return None

#temperature = fetch_weather("ulan-ude")
#if temperature is not None:
#    celsius = temperature - 273.15
#    celsius_rounded = round(celsius, 2)
#    print(f"The current temperature in Ulan-Ude is {celsius_rounded} degrees Celsius.")
#else:
#    print("City not found.")

@app.route('/')
def home():
    users = User.query.all()
    return render_template('home.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        balance = int(request.form['balance'])
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            flash(f'User {username} already exists!', 'danger')
        else:
            new_user = User(username=username, balance=balance)
            db.session.add(new_user)
            db.session.commit()
            flash(f'User {username} added successfully!', 'success')
            return redirect(url_for('home'))
    return render_template('add_user.html')

@app.route('/update_balance/<int:user_id>/<city>', methods=['GET'])
def update_balance(user_id, city):
    user = User.get_by_username(User.query.get(user_id).username)

    if not user:
        flash(f'User with id {user_id} not found.', 'danger')
        return redirect(url_for('home'))
    if user.balance < 0:
        flash(f'Balance of user {user.username} is already negative.', 'danger')
        return redirect(url_for('home'))
    
    with db.session.begin_nested():
        temperature = fetch_weather(city)
        if temperature is not None:
            temperature_celsius = temperature - 273.15
            if temperature_celsius > 0:
                user.balance -= round(temperature_celsius, 2)
                user.update()
        else:
            flash(f'City {city} not found.', 'danger')
            return redirect(url_for('home'))
    
    if user.balance < 0:
        flash(f'Balance of user {user.username} would become negative with the temperature in {city}! Balance has not been updated.', 'danger')
    else:
        flash(f'Balance of user {user.username} has been updated with the temperature in {city}!', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)