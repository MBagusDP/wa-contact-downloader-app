from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../image')
    return app