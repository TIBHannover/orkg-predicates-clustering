import os
import json
import pickle
import onnx

import pandas as pd


class Writer:

    def validate_path(func):
        """
            Last argument of functions using this decorator must be a path
        """

        def wrapper(self, *args, **kwargs):
            if not os.path.exists(os.path.dirname(args[-1])):
                os.makedirs(os.path.dirname(args[-1]))
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    @validate_path
    def write_json(json_data, output_path):
        with open(output_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

    @staticmethod
    @validate_path
    def write_png(image, output_path):
        image.save(output_path)

    @staticmethod
    @validate_path
    def write_txt(data, output_path):
        with open(output_path, 'w') as file:
            file.write(data)

    @staticmethod
    @validate_path
    def write_onnx(model, input_path):
        with open(input_path, 'wb') as f:
            f.write(model.SerializeToString())


class Reader:

    @staticmethod
    def read_json(input_path):
        with open(input_path, encoding='utf-8') as f:
            json_data = json.load(f)

        return json_data

    @staticmethod
    def read_pickle(input_path):
        with open(input_path, 'rb') as f:
            loaded_object = pickle.load(f)
        return loaded_object

    @staticmethod
    def read_onnx(input_path):
        return onnx.load(input_path)

    @staticmethod
    def read_df_from_json(input_path, key=None):
        json_file = Reader.read_json(input_path)

        if key:
            return pd.json_normalize(json_file[key])

        return pd.json_normalize(json_file)
