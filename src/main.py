from argparse import ArgumentParser

from src.data import main as data
from src.models import convert, evaluate, predict


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('-t', '--task',
                        choices=['dataset', 'evaluate', 'convert', 'predict'],
                        required=True,
                        help='Indicates the task to be executed. '
                             'dataset: fetches, analyses and splits the dataset. The file paths are fixed. '
                             'select:  selects the best model based on the result files under /data/results.'
                             'convert: converts the selected kmeans model to ONNX format. '
                             'predict: predicts the provided approach using the provided query.'
                        )

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


def main():
    args = parse_args()

    {
        'dataset': data.main,
        'evaluate': evaluate.main,
        'convert': convert.main,
        'predict': predict.main
    }[args.task](args)


if __name__ == '__main__':
    main()

