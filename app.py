from flask import Flask
from views import view_blueprint
from flask_cors import CORS

app = Flask(__name__)


def helloworld():
    return "Hello, cross-origin-world!"


def create_app():
    app_clarityppm_integration = Flask(__name__)
    app_clarityppm_integration.config['CORS_HEADERS'] = 'Content-Type'
    app_clarityppm_integration.config['DEBUG'] = True
    app_clarityppm_integration.register_blueprint(view_blueprint, url_prefix='')
    return app_clarityppm_integration


if __name__ == '__main__':
    app = create_app()
    cors = CORS(app)
    app.run(host='192.168.0.50', port=5013)
