from flask import Blueprint

bp = Blueprint('pages', __name__)

from .public import *