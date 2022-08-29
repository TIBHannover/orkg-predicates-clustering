import os
import random

from src import PROCESSED_DATA_DIR, TRIPLE_STORE_URL
from src.data.sparql.queries import PAPER_CONTRIBUTIONS
from src.data.sparql.service import query
from src.util.io import Reader, Writer
from src.util.list import flatten
from src.util.string import uri_to_id

SPLIT_THRESHOLD = 0.7
random.seed(1500)


def get_paper_contributions(paper_id):
    df = query(TRIPLE_STORE_URL, PAPER_CONTRIBUTIONS(paper_id))
    return df.contribution.map(uri_to_id).tolist()


def build_instance(comparison, paper):
    return {
        'instance_id': '{}x{}'.format(comparison['id'], paper['id']),
        'comparison_id': comparison['id'],
        'paper_id': paper['id'],
        'text': '{} {}'.format(paper['label'], paper['abstract']),
        'contribution_ids': get_paper_contributions(paper['id'])
    }


def build_training_set(data, training_set, training_instance_ids):
    for comparison in data['comparisons']:

        if 'contributions' in comparison and len(comparison['contributions']) < 10:
            continue

        number_of_instances = int(len(comparison['papers']) * SPLIT_THRESHOLD)
        random_indices = random.sample(range(len(comparison['papers'])), number_of_instances)

        for index in random_indices:
            paper = comparison['papers'][index]

            training_instance_ids.append(paper['id'])
            training_set['instances'].append(build_instance(comparison, paper))


def build_test_set(data, test_set, training_instance_ids, test_instance_ids):
    for comparison in data['comparisons']:

        for paper in comparison['papers']:

            if paper['id'] in training_instance_ids + test_instance_ids:
                continue

            test_instance_ids.append(paper['id'])
            test_set['instances'].append(build_instance(comparison, paper))


def split_dataset(data):
    training_set, test_set = {'instances': []}, {'instances': []}
    training_instance_ids, test_instance_ids = [], []

    build_training_set(data, training_set, training_instance_ids)
    build_test_set(data, test_set, training_instance_ids, test_instance_ids)

    return training_set, test_set


def verify(training_set, test_set):
    print('### Data Splitting Verification ###')

    training_paper_ids = [instance['paper_id'] for instance in training_set['instances']]
    test_paper_ids = [instance['paper_id'] for instance in test_set['instances']]

    print('Training and test papers are disjoint: ', not bool(set(training_paper_ids).intersection(test_paper_ids)))
    # This is ok, because one paper can occur in different comparisons
    print('Training papers are unique: ', len(training_paper_ids) == len(list(set(training_paper_ids))))
    # This must be true, because we don't want duplicates
    print('Test papers are unique: ', len(test_paper_ids) == len(list(set(test_paper_ids))))


def statistics(dataset, training_set, test_set):
    dataset_comparison_ids = [comparison['id'] for comparison in dataset['comparisons']]
    dataset_paper_ids = [paper['id'] for comparison in dataset['comparisons'] for paper in comparison['papers']]
    dataset_contributions_ids = flatten([comparison['contributions'] for comparison in dataset['comparisons']])

    training_comparison_ids = [instance['comparison_id'] for instance in training_set['instances']]
    training_paper_ids = [instance['paper_id'] for instance in training_set['instances']]
    training_contribution_ids = flatten(
        [instance['contribution_ids'] for instance in training_set['instances'] if 'contribution_ids' in instance])

    test_comparison_ids = [instance['comparison_id'] for instance in test_set['instances']]
    test_paper_ids = [instance['paper_id'] for instance in test_set['instances']]
    test_contribution_ids = flatten(
        [instance['contribution_ids'] for instance in test_set['instances'] if 'contribution_ids' in instance])

    dataset_statistics = 'Dataset:\n' \
                         '\tPapers: {}\n' \
                         '\tDistinct Papers: {}\n' \
                         '\tContributions: {}\n' \
                         '\tDistinct Contributions: {}\n' \
                         '\tComparisons: {}\n'.format(len(dataset_paper_ids),
                                                      len(list(set(dataset_paper_ids))),
                                                      len(dataset_contributions_ids),
                                                      len(list(set(dataset_contributions_ids))),
                                                      len(set(dataset_comparison_ids)))

    training_set_statistics = 'Training:\n' \
                              '\tPapers: {}\n' \
                              '\tDistinct Papers: {}\n' \
                              '\tContributions: {}\n' \
                              '\tDistinct Contributions: {}\n' \
                              '\tComparisons: {}\n'.format(len(training_paper_ids),
                                                           len(list(set(training_paper_ids))),
                                                           len(training_contribution_ids),
                                                           len(list(set(training_contribution_ids))),
                                                           len(set(training_comparison_ids)))

    test_set_statistics = 'Test:\n' \
                          '\tPapers: {}\n' \
                          '\tDistinct Papers: {}\n' \
                          '\tContributions: {}\n' \
                          '\tDistinct Contributions: {}\n' \
                          '\tComparisons: {}\n'.format(len(test_set['instances']),
                                                       len(list(set(test_paper_ids))),
                                                       len(test_contribution_ids),
                                                       len(list(set(test_contribution_ids))),
                                                       len(set(test_comparison_ids)))

    Writer.write_txt(
        dataset_statistics + training_set_statistics + test_set_statistics,
        os.path.join(PROCESSED_DATA_DIR, 'split_statistics.txt')
    )


def main(dataset):
    training_set, test_set = split_dataset(dataset)

    Writer.write_json(training_set, os.path.join(PROCESSED_DATA_DIR, 'training_set.json'))
    Writer.write_json(test_set, os.path.join(PROCESSED_DATA_DIR, 'test_set.json'))

    verify(training_set, test_set)
    statistics(dataset, training_set, test_set)


if __name__ == '__main__':
    data = Reader.read_json(os.path.join(PROCESSED_DATA_DIR, 'dataset.json'))
    main(data)
