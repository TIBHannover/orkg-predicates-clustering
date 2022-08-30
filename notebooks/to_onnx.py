import pickle
import os

from onnxconverter_common import StringTensorType
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from skl2onnx.helpers.onnx_helper import add_output_initializer

# TODO: extend to download and upload from/to huggingface. Consider a full pipeline integration with the training script

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, 'output', 'orkgnlp-predicates-kmeans-1850.pkl')
VECTORIZER_PATH = os.path.join(CURRENT_DIR, 'output', 'orkgnlp-predicates-tfidf.pkl')


def read_pickle(input_path):
    with open(input_path, 'rb') as f:
        loaded_object = pickle.load(f)
    return loaded_object


def write_onnx(model, input_path):
    with open(input_path, 'wb') as f:
        f.write(model.SerializeToString())


def convert_model(model, model_path, input_tensor_type, additional_output=None):
    print("converting {}".format(model_path))

    onnx_model = convert_sklearn(model,
                                 initial_types=[('X', input_tensor_type)]
                                 )
    if additional_output:
        onnx_model = add_output_initializer(onnx_model, additional_output[0], additional_output[1])

    onnx_model_path = '{}.onnx'.format(os.path.splitext(model_path)[0])
    write_onnx(onnx_model, onnx_model_path)

    print('converted {}'.format(onnx_model_path))


def main():
    # ----------- Sklearn-KMeans -----------
    model = read_pickle(MODEL_PATH)
    convert_model(model=model,
                  model_path=MODEL_PATH,
                  input_tensor_type=FloatTensorType([None, model.cluster_centers_.shape[1]]),
                  additional_output=('labels_', model.labels_)
                  )

    # ----------- Sklearn-TfidfVectorizer -----------
    model = read_pickle(VECTORIZER_PATH)
    convert_model(model=model,
                  model_path=VECTORIZER_PATH,
                  input_tensor_type=StringTensorType([None, 1])
                  )


if __name__ == '__main__':
    main()
