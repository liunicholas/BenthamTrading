from flask import Flask, send_from_directory
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS  # comment this on deployment
from benthamTradingAPI.HelloApiHandler import HelloApiHandler

app = Flask(__name__, static_url_path='', static_folder='frontend/build')
CORS(app)  # comment this on deployment
api = Api(app)


@app.route("/", defaults={'path': ''})
def serve(path):
    return send_from_directory(app.static_folder, 'index.html')


api.add_resource(HelloApiHandler, '/flask/hello')
# import random
# from flask import Flask, render_template
# import trader as trader

# app = Flask(__name__)


# @app.route('/')
# def home():
#     return render_template('index.html')


# @app.route('/get_data')
# def get_data():
#     # Generate random data
#     random_number = random.randint(1, 100)

#     return str(random_number)  # Return the updated data

# if __name__ == '__main__':
#     app.run(debug=True)
