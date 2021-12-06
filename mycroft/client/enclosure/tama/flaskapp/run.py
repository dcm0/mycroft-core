from flask import Flask, redirect, url_for, render_template, request
from flask.scaffold import F
from app import create_app

app = create_app()

#This run only for debug 
if __name__ == "__main__":
    app.run(port= 3000, debug=True)

