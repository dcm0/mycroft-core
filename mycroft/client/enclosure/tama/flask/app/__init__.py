from flask import Flask, redirect, url_for, render_template, request,Blueprint
from flask.scaffold import F
def create_app():
    app = Flask(__name__)

    with app.app_context():
        from .views import view
        from .api import api
        app.register_blueprint(view,url_prefix='/')
        app.register_blueprint(api,url_prefix='/api')

    return app
        