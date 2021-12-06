#launch flask and do all the control and write on the buses and listen on the buses.
from flask import Flask, blueprints, redirect, url_for, render_template, request, Blueprint

app = Blueprint('api',__name__)

@app.route("/eyes", method=['POST'])
def eye_update():
    if request.method == "POST":
        if request.form.get('action1'):
            pass #do something
        elif  request.form.get('action2'):
            pass # do something else
        else:
            pass #unkown
    elif request.method == 'GET':
        return render_template('mainPage.html')
    
    return "done",201

if __name__ == "__api__":
    app.run(host="localhost", port=8000, debug=True)