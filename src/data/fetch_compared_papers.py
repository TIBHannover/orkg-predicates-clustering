import os
import requests
import warnings
import pandas as pd

from src import TRIPLE_STORE_URL, SIMCOMP_HOST, RAW_DATA_DIR, ORKG_PAPERS_DUMP_URL
from src.data.sparql.queries import COMPARISONS_CONTRIBUTINOS_AND_THEIR_PAPERS
from src.data.sparql.service import query
from src.util.io import Writer
from src.util.string import id_to_uri

CONTRIBUTIONS_PER_COMPARISON_THRESHOLD = 10
PAPERS_PER_COMPARISON_THRESHOLD = 2
BLACKLIST = [
    'R142085',
    'R156112'
]


def to_json(df, papers_dump):
    comparisons = []
    uri_columns = ['comparison', 'contribution', 'paper', 'research_field', 'research_problem']
    research_problem_columns = {'research_problem': 'id', 'research_problem_label': 'label'}

    df[uri_columns] = df[uri_columns].applymap(lambda x: os.path.basename(str(x)))
    df.rename(columns=research_problem_columns, inplace=True)

    for comparison_id in df.comparison.unique():
        comparison_df = df[df.comparison == comparison_id]

        comparison_json = {
            'id': comparison_df.comparison.iloc[0],
            'label': comparison_df.comparison_label.iloc[0],
            'contributions': comparison_df.contribution.unique().tolist(),
            'papers': [
                {
                    'id': paper_id,
                    'label': comparison_df[comparison_df.paper == paper_id].paper_title.iloc[0],
                    'doi': comparison_df[comparison_df.paper == paper_id].doi.iloc[0],
                    'research_field': {
                        'id': comparison_df[comparison_df.paper == paper_id].research_field.iloc[0],
                        'label': comparison_df[comparison_df.paper == paper_id].research_field_label.iloc[0]
                    },
                    'research_problems': comparison_df[
                                             comparison_df.paper == paper_id
                                             ].loc[:, research_problem_columns.values()].drop_duplicates()
                    .to_dict(orient='records'),
                    'abstract': papers_dump[papers_dump.uri == id_to_uri(paper_id)].processed_abstract.iloc[0]
                }
                for paper_id in comparison_df.paper.unique()
                if len(papers_dump[papers_dump.uri == id_to_uri(paper_id)].processed_abstract.index) != 0
                   and papers_dump[papers_dump.uri == id_to_uri(paper_id)].processed_abstract.iloc[0]
            ]
        }

        comparisons.append(comparison_json)

    # filtering based on n_papers per comparison and paper labels
    filtered_comparisons = []
    for comparison in comparisons:

        filtered_papers = []
        paper_labels = []
        for paper in comparison['papers']:
            if paper['label'] not in paper_labels:
                filtered_papers.append(paper)
                paper_labels.append(paper['label'])

        comparison['papers'] = filtered_papers

        if len(comparison['papers']) >= PAPERS_PER_COMPARISON_THRESHOLD:
            filtered_comparisons.append(comparison)

    return filtered_comparisons


def extend_to_predicates(comparisons):
    for i, comparison in enumerate(comparisons):
        print('{}/{} fetching predicates for comparison: {}'.format(i + 1, len(comparisons), comparison['id']))

        try:
            comparison['predicates'] = compare(comparison['contributions'])
        except Exception:
            continue

    return comparisons


def compare(contribution_ids):
    response = compare_simcomp(contribution_ids)
    predicates = []
    predicate_ids = []

    for property in response['data'].keys():

        predicate_id = None
        predicate_label = None
        for contribution_data in response['data'][property]:
            if contribution_data[0]:
                predicate_id = ';'.join(contribution_data[0]['path'][1::2])
                predicate_label = ';'.join(contribution_data[0]['pathLabels'][1::2])
                break

        if predicate_id in predicate_ids:
            continue

        # remove 'P32'
        if 'has research problem' in predicate_label:
            continue

        predicate_ids.append(predicate_id)
        predicates.append({
            'id': predicate_id,
            'label': predicate_label
        })

    return predicates


def compare_simcomp(contribution_ids):
    url = '{}/compare/?contributions={}&type=path'.format(SIMCOMP_HOST, ','.join(contribution_ids))

    response = requests.get(url)

    if not response.ok:
        print('Failed to compare contributions')

    return response.json()


def verify(comparison):
    comparison_ids = []
    papers_ids_are_unique_per_comparison = []
    papers_labels_are_unique_per_comparison = []
    overall_paper_ids = []
    number_of_papers_per_comparison = []
    predicates_ids_are_unique_per_comparison = []
    predicates_labels_are_unique_per_comparison = []
    for comparison in comparison:
        comparison_ids.append(comparison['id'])
        number_of_papers_per_comparison.append(len(comparison['papers']))

        paper_ids = []
        paper_labels = []
        for paper in comparison['papers']:
            paper_ids.append(paper['id'])
            paper_labels.append(paper['label'])

        predicate_ids = []
        predicate_labels = []
        for predicate in comparison['predicates']:
            predicate_ids.append(predicate['id'])
            predicate_labels.append(predicate['label'])

        overall_paper_ids.extend(paper_ids)
        papers_ids_are_unique_per_comparison.append(len(paper_ids) == len(list(set(paper_ids))))
        papers_labels_are_unique_per_comparison.append(len(paper_labels) == len(list(set(paper_labels))))
        predicates_ids_are_unique_per_comparison.append(len(predicate_ids) == len(list(set(predicate_ids))))
        predicates_labels_are_unique_per_comparison.append(len(predicate_labels) == len(list(set(predicate_labels))))

    if not len(comparison_ids) == len(set(comparison_ids)):
        warnings.warn('Comparisons are not unique')

    if False in papers_ids_are_unique_per_comparison:
        warnings.warn('Paper IDS per comparisons must be unique')

    if False in papers_labels_are_unique_per_comparison:
        warnings.warn('Paper labels per comparisons must be unique')

    if not all(element >= PAPERS_PER_COMPARISON_THRESHOLD for element in number_of_papers_per_comparison):
        warnings.warn('Each comparison must at least have {} papers'.format(PAPERS_PER_COMPARISON_THRESHOLD))

    if False in predicates_ids_are_unique_per_comparison:
        warnings.warn('Predicate IDs per comparisons must be unique')

    if False in predicates_labels_are_unique_per_comparison:
        # this is ok because IDs are different
        warnings.warn('Predicates labels per comparisons are not unique')

    if not len(overall_paper_ids) == len(set(overall_paper_ids)):
        # this is ok because papers can occur in different comparisons
        warnings.warn('Overall paper IDs are not unique')


def main(papers_dump):
    df = query(
        TRIPLE_STORE_URL,
        COMPARISONS_CONTRIBUTINOS_AND_THEIR_PAPERS(CONTRIBUTIONS_PER_COMPARISON_THRESHOLD, BLACKLIST)
    )

    comparisons = to_json(df, papers_dump)
    comparisons = extend_to_predicates(comparisons)

    verify(comparisons)

    Writer.write_json({'comparisons': comparisons}, os.path.join(RAW_DATA_DIR, 'compared_papers.json'))

    return comparisons


if __name__ == '__main__':
    dump = pd.read_csv(ORKG_PAPERS_DUMP_URL).fillna('')
    main(dump)
