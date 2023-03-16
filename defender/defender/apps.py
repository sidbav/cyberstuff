import lief
# import pandas as pd
from flask import Flask, jsonify, request
from defender.models.attribute_extractor import *


def create_app(model, threshold):
    app = Flask(__name__)
    app.config['model'] = model

    # analyse a sample
    @app.route('/', methods=['POST'])
    def post():
        # curl -XPOST --data-binary @somePEfile http://127.0.0.1:8080/ -H "Content-Type: application/octet-stream"
        if request.headers['Content-Type'] != 'application/octet-stream':
            resp = jsonify({'error': 'expecting application/octet-stream'})
            resp.status_code = 400  # Bad Request
            return resp

        bytez = request.data

        try:
            custom_ext = CustomExtractor(bytez)
            model = app.config['model']
            result = custom_ext.custom_predict_sample(model)
            result_prob = custom_ext.custom_predict_with_threshold(model)
            result = int(result)

            print('LABEL = ', result)
            print('LABEL PROB = ', result_prob)
        except (lief.bad_format, lief.read_out_of_bound) as e:
            print("Error:", e)
            result = 1


        if not isinstance(result, int) or result not in {0, 1}:
            resp = jsonify({'error': 'unexpected model result (not in [0,1])'})
            resp.status_code = 500  # Internal Server Error
            return resp

        resp = jsonify({'result': result})
        resp.status_code = 200
        return resp

    # get the model info
    @app.route('/model', methods=['GET'])
    def get_model():
        # curl -XGET http://127.0.0.1:8080/model
        resp = jsonify(app.config['model'].model_info())
        resp.status_code = 200
        return resp

    return app