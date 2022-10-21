import onnxruntime as rt
import numpy as np

from argparse import ArgumentParser
from sentence_transformers import SentenceTransformer

from src.util.io import Reader


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('-mp', '--model_path',
                        type=str,
                        required=False,
                        help='Path to the model to be converted to ONNX format. Required when --task==convert. '
                        )

    parser.add_argument('-trainp', '--training_set_path',
                        type=str,
                        required=False,
                        help='Path to training set.'
                        )

    parser.add_argument('-cpp', '--comparisons_predicates_path',
                        type=str,
                        required=False,
                        help='Path to the comparisons predicates mapping.'
                        )

    parser.add_argument('-q', '--query',
                        type=str,
                        required=False,
                        help='Paper textual representation. A concatenation of paper\'s title and DOI. '
                        )

    parser.add_argument('-n', '--n_results',
                        type=int,
                        default=20,
                        required=False,
                        help='Number of results to be retrieved.'
                        )

    return parser.parse_args()


def vectorize(text):
    vectorizer = SentenceTransformer('allenai/scibert_scivocab_uncased')
    return vectorizer.encode([text])


def predict(model, inputs):

    session = rt.InferenceSession(model.SerializeToString())
    input_dict = {session.get_inputs()[i].name: [inputs[i]] for i in range(len(inputs))}
    output = session.run(['label', 'labels_'], input_dict)

    return output[0], output[1]


def main(config=None):
    args = config or parse_args()

    assert args.query, 'query must be provided.'
    assert args.model_path, 'model_path must be provided.'
    assert args.training_set_path, 'training_set_path must be provided.'
    assert args.comparisons_predicates_path, 'comparisons_predicates_path must be provided.'

    train_df = Reader.read_df_from_json(args.training_set_path, key='instances')
    mapping = Reader.read_json(args.comparisons_predicates_path)

    embeddings = vectorize(args.query)
    model = Reader.read_onnx(args.model_path)
    cluster_label, model_labels_ = predict(model, (embeddings[0], ))

    print(model.metadata_props)

    cluster_instances_indices = np.argwhere(cluster_label == model_labels_).squeeze(1)
    cluster_instances = train_df.iloc[cluster_instances_indices]
    comparison_ids = cluster_instances['comparison_id'].unique()

    predicates = []
    for comparison_id in comparison_ids:
        predicates.extend(mapping[comparison_id])

    print(predicates[:args.n_results])
    return predicates[:args.n_results]


if __name__ == '__main__':
    main()
