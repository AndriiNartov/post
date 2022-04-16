from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config['SECRET_KEY'] = 'c2e840fa18ee3823a3db2bb6190b9e96'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db?check_same_thread=False'

db = SQLAlchemy(app, session_options={'expire_on_commit': False})

from post_site import routes
