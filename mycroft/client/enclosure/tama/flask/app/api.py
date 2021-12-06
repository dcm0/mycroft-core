#launch flask and do all the control and write on the buses and listen on the buses.
from flask import Flask, blueprints, redirect, url_for, render_template, request, Blueprint

api = Blueprint('api',__name__)

@api.route("/eyes", methods=['POST'])
def eye_update():
    if request.methods == "POST":
        if request.form.get('action1'):
            pass #do something
        elif  request.form.get('action2'):
            pass # do something else
        else:
            pass #unkown
    elif request.methods == 'GET':
        return render_template('main.html')
    
    return "done",201
