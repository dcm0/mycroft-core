from flask import Flask, blueprints, redirect, url_for, render_template, request, Blueprint

view = Blueprint('view',__name__)

@view.route("/")
def home():
    return render_template('main.html')
    