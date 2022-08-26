import os
import requests
import pandas as pd

from src import RAW_DATA_DIR, TRIPLE_STORE_URL, SIMCOMP_HOST
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
                                         ].loc[:, research_problem_columns.values()]
                    .to_dict(orient='records'),
                    'abstract': papers_dump[papers_dump.uri == id_to_uri(paper_id)].processed_abstract.iloc[0]
                }
                for paper_id in comparison_df.paper.unique()
                if len(papers_dump[papers_dump.uri == id_to_uri(paper_id)].processed_abstract.index) != 0
                   and papers_dump[papers_dump.uri == id_to_uri(paper_id)].processed_abstract.iloc[0]
            ]
        }

        comparisons.append(comparison_json)

    # filtering based on n_papers per comparison #
    filtered_comparisons = []
    for comparison in comparisons:
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


def main():
    # TODO: automatically download the orkg_papers dump
    papers_dump = pd.read_csv(os.path.join(RAW_DATA_DIR, 'orkg_papers.csv')).fillna('')

    df = query(
        TRIPLE_STORE_URL,
        COMPARISONS_CONTRIBUTINOS_AND_THEIR_PAPERS(CONTRIBUTIONS_PER_COMPARISON_THRESHOLD, BLACKLIST)
    )

    comparisons = to_json(df, papers_dump)
    comparisons = extend_to_predicates(comparisons)

    print('Verify:')

    comparisons_predicates = {}
    for comparison in comparisons:
        comparisons_predicates[comparison['id']] = comparison['predicates']

    Writer.write_json({'comparisons': comparisons}, os.path.join(RAW_DATA_DIR, 'data.json'))
    Writer.write_json(comparisons_predicates, os.path.join(RAW_DATA_DIR, 'comparison_predicates.json'))

    return {'comparisons': comparisons}


if __name__ == '__main__':
    main()
