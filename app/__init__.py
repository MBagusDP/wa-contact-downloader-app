from flask import Flask
import os

def create_app():
#     home_directory = os.path.expanduser("~")
#     static_path = os.path.join(home_directory, 'Downloads').replace('\\','/')
#     print(static_path)
    app = Flask(__name__, template_folder='../templates', static_folder='../image')
    return app