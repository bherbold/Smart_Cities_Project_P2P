from flask import Flask, send_from_directory, render_template
from .pages import bp
from flask_cors import CORS


def create_app():
    app = Flask(__name__, static_url_path='')
    CORS(app)

    @app.route('/assets/<path:path>')
    def send_file(path):
        return send_from_directory('assets', path)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    app.register_blueprint(bp)

    return app