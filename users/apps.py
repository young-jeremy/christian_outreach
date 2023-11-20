from django.apps import AppConfig
""""from flask import Flask, render_template, request
from flask_socketio import SocketIO
from flask import Flask, render_template, request
from flask_socketio import SocketIO
# from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
app = Flask(__name__)
socketio = SocketIO(app)

user_subscriptions = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscriptions.db'  # Change this for a production database
socketio = SocketIO(app)
# db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('videos/video_details.html')


@socketio.on('subscribe')
def handle_subscribe(data):
    username = data['username']
    activity = data['activity']

    # Store user subscription
    if username not in user_subscriptions:
        user_subscriptions[username] = []

    if activity not in user_subscriptions[username]:
        user_subscriptions[username].append(activity)

    # Notify the user that they are subscribed
    socketio.emit('subscription_response', {'message': f'You are subscribed to {activity}'}, room=request.sid)


@socketio.on('activity_notification')
def handle_activity_notification(data):
    # Broadcast activity notifications to subscribed users
    username = data['username']
    activity = data['activity']
    message = f'New {activity} from {username}'

    if username in user_subscriptions and activity in user_subscriptions[username]:
        socketio.emit('notification', {'message': message}, room=request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)"""


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
