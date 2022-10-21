import os

from argparse import ArgumentParser

from onnxconverter_common import FloatTensorType
from skl2onnx import convert_sklearn
from skl2onnx.helpers.onnx_helper import add_output_initializer

from src.util.io import Reader, Writer


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('-mp', '--model_path',
                        type=str,
                        required=False,
                        help='Path to the model to be converted to ONNX format. Required when --task==convert. '
                        )

    return parser.parse_args()


def convert_model(model, model_path, input_tensor_type, additional_output=None, metadata=None):
    print("converting {}".format(model_path))

    onnx_model = convert_sklearn(model,
                                 initial_types=[('X', input_tensor_type)]
                                 )
    if additional_output:
        onnx_model = add_output_initializer(onnx_model, additional_output[0], additional_output[1])

    if metadata:
        for key, value in metadata.items():
            meta = onnx_model.metadata_props.add()
            meta.key = key
            meta.value = value

    onnx_model_path = '{}.onnx'.format(os.path.splitext(model_path)[0])
    Writer.write_onnx(onnx_model, onnx_model_path)

    print('converted {}'.format(onnx_model_path))


def main(config=None):
    args = config or parse_args()

    assert args.model_path, 'model_path must be provided.'

    # ----------- Sklearn-KMeans -----------
    model = Reader.read_pickle(args.model_path)
    convert_model(model=model,
                  model_path=args.model_path,
                  input_tensor_type=FloatTensorType([None, model.cluster_centers_.shape[1]]),
                  additional_output=('labels_', model.labels_),
                  metadata={
                      'description': 'sklearn.cluster.KMeans ONNX formatted model that includes 3150 clusters. '
                                     'The model expects one vector as an input with the shape (768, ) and outputs '
                                     'the predicted cluster label as well as the cluster.labels_ (see sklearn docs '
                                     'for more details).',
                      'author': 'Omar Arab Oghli <omar.araboghli@tib.eu>',
                      'organization': 'Open Research Knowledge Graph https://www.orkg.org',
                      'license': 'MIT',
                      'model_version': 'v0.2.0',
                      'model_release': 'https://gitlab.com/TIBHannover/orkg/nlp/experiments/orkg-predicates-clustering/-/releases/v0.2.0'
                    }
                  )


if __name__ == '__main__':
    main()
