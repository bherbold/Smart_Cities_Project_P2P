from flask import request, render_template
from . import bp
from app.func.test import test
import requests


@bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@bp.route('/people', methods=['GET'])
def peopel_empty():
    people = []
    return render_template('index.html', people=people)


@bp.route('/people/load', methods=['GET'])
def peopel_loaded():
    data = requests.get("http://api.open-notify.org/astros.json")
    people = test()
    return render_template('index.html', people=people, data=data.json())
