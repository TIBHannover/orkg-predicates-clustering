import os

from src import DATA_DIR
from src.util.io import Reader


def select_model(results):
    k_micros = [(k, results[k]['micro']['f_measure']) for k in results.keys()]

    best_model = max(k_micros, key=lambda item: item[1])

    return {
        'k': best_model[0],
        'micro_f': best_model[1],
        'macro_f': results[best_model[0]]['macro']['f_measure']
    }


def main(config=None):
    approaches = {
        'scibert_agglomerative': '',
        'scibert_kmeans': '',
        'tfidf_agglomerative': '',
        'tfidf_kmeans': ''
    }

    for approach in approaches.keys():
        results_path = os.path.join(DATA_DIR, 'results', approach + '_results.json')
        results = Reader.read_json(results_path)
        approaches[approach] = select_model(results)

    print(approaches)


if __name__ == '__main__':
    main()
