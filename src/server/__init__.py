from flask import Flask
from flask_cors import CORS

from database.flask import *
from utils.constants import DB_DIR, SQL_TYPE

server = Flask(
    __name__,
    template_folder='../react/build/',
    static_folder='../react/build/static'
)
CORS(server)
server.config['SQLALCHEMY_DATABASE_URI'] = SQL_TYPE + '../' + DB_DIR + 'database.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def start_react_server(app):
    db.init_app(server)
    server.run(debug=True)


from server.views import *
