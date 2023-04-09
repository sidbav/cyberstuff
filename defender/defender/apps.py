import lief
# import pandas as pd
from flask import Flask, jsonify, request
from defender.models.attribute_extractor import *
import pefile
import sys

import re
import math
import numpy as np
# import pandas as pd
import ember

def experiment_with_removing_appended_data(app, pe, bytez):
    # Determine the actual size of the file
    actual_size = pe.OPTIONAL_HEADER.SizeOfHeaders
    for section in pe.sections:
        actual_size += section.SizeOfRawData

    file_size = len(bytez)
    #print('computed size', actual_size)
    # print('bytez recieved size', file_size)

    result, result_prob = None, None
    try:
        if actual_size != file_size:
            #print('*************POTENITAL Manipulation')
            #print('RUNNING WITH REAL SIZE')
            custom_ext = CustomExtractor(bytez[:actual_size])

            model = app.config['model']
            result = 0
            result_prob = custom_ext.custom_predict_with_threshold(model)
            if result_prob[0][0]<0.61: result = 1

            print('LABEL = ', result)
            print('LABEL PROB = ', result_prob)
        else:
            custom_ext = CustomExtractor(bytez)
            # attributes = custom_ext.custom_attribute_extractor()
            # print(attributes['header'])


            model = app.config['model']
            # result = custom_ext.custom_predict_sample(model)
            result_prob = custom_ext.custom_predict_with_threshold(model)
            result = 0
            if result_prob[0][0]<0.61: result = 1
            # else: result = 0
            # result = int(result)

            print('LABEL = ', result)
            print('LABEL PROB = ', result_prob)
    except (lief.bad_format, lief.read_out_of_bound) as e:
        print("Error:", e)
        result = 1

    return result, result_prob

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
            pe = pefile.PE(data=bytez)
        except:
            resp = jsonify({'error': 'Not PE File!'})
            resp.status_code = 400  # Internal Server Error
            return resp

        result, result_prob = experiment_with_removing_appended_data(app, pe, bytez)

        if not isinstance(result, int) or result not in {0, 1}:
            resp = jsonify({'error': 'unexpected model result (not in [0,1])'})
            resp.status_code = 500  # Internal Server Error
            return resp

        resp = jsonify({'result': result, 'result_proba_0': result_prob[0][0], 'result_proba_1': result_prob[0][1]})
        resp.status_code = 200
        return resp

    # # get the model info
    # @app.route('/model', methods=['GET'])
    # def get_model():
    #     # curl -XGET http://127.0.0.1:8080/model
    #     resp = jsonify(app.config['model'].model_info())
    #     resp.status_code = 200
    #     return resp

    return app
