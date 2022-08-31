import os
import warnings

import pandas as pd

from src import RAW_DATA_DIR, TRIPLE_STORE_URL
from src.data.sparql.queries import PAPERS_BY_RESEARCH_FIELD_QUERY, PAPERS_QUERY, RESEARCH_PROBLEMS_BY_PAPER
from src.data.sparql.service import query
from src.util.io import Reader, Writer
from src.util.string import uri_to_id, id_to_uri

UNCOMPARED_PAPERS_THRESHOLD = 2  # n_uncompared * threshold == n_compared


def fetch_uncompared_papers_with_same_distribution(paper_ids, paper_labels, papers_dump, research_fields):
    uncompared_papers = []
    uncompared_paper_ids = []
    uncompared_paper_labels = []
    for research_field_id in research_fields:
        orkg_papers = query(TRIPLE_STORE_URL,
                            PAPERS_BY_RESEARCH_FIELD_QUERY('<{}>'.format(id_to_uri(research_field_id)))
                            )
        orkg_papers.paper = orkg_papers.paper.apply(uri_to_id)

        temp_uncompared_papers = []
        temp_uncompared_paper_ids = []
        temp_uncompared_paper_labels = []

        for index, orkg_paper in orkg_papers.iterrows():

            # stop if we got what we need
            if len(temp_uncompared_papers) * UNCOMPARED_PAPERS_THRESHOLD >=\
                    len(research_fields[research_field_id]['papers']):
                break

            # papers have not been seen before by ID
            if orkg_paper.loc['paper'] in paper_ids + uncompared_paper_ids + temp_uncompared_paper_ids:
                continue

            # papers have not been seen before by label
            if orkg_paper.loc['paper_title'] in paper_labels + uncompared_paper_labels + temp_uncompared_paper_labels:
                continue

            if len(papers_dump[papers_dump.uri == id_to_uri(orkg_paper.loc['paper'])].processed_abstract) != 0 \
                    and papers_dump[papers_dump.uri == id_to_uri(orkg_paper.loc['paper'])].processed_abstract.iloc[0]:

                problems_df = query(TRIPLE_STORE_URL, RESEARCH_PROBLEMS_BY_PAPER(uri_to_id(orkg_paper.loc['paper'])))
                problems_df.id = problems_df.id.apply(uri_to_id)
                temp_uncompared_paper = {
                    'id': orkg_paper.loc['paper'],
                    'label': orkg_paper.loc['paper_title'],
                    'doi': orkg_paper.loc['doi'],
                    'research_field': {
                        'id': research_field_id,
                        'label': research_fields[research_field_id]['label']
                    },
                    'research_problems': problems_df.drop_duplicates().to_dict(orient='records'),
                    'abstract': papers_dump[
                        papers_dump.uri == id_to_uri(orkg_paper.loc['paper'])
                    ].processed_abstract.iloc[0]
                }

                temp_uncompared_papers.append(temp_uncompared_paper)
                temp_uncompared_paper_ids.append(orkg_paper.loc['paper'])
                temp_uncompared_paper_labels.append(orkg_paper.loc['paper_title'])

        uncompared_papers.extend(temp_uncompared_papers)
        uncompared_paper_ids.extend(temp_uncompared_paper_ids)
        uncompared_paper_labels.extend(temp_uncompared_paper_labels)

    return uncompared_papers, uncompared_paper_ids, uncompared_paper_labels


def fetch_rest_uncompared_papers(paper_ids, paper_labels, uncompared_paper_ids, uncompared_paper_labels, papers_dump):
    rest_uncompared_papers = []
    rest_uncompared_paper_ids = []
    rest_uncompared_paper_labels = []

    orkg_papers = query(TRIPLE_STORE_URL, PAPERS_QUERY)
    orkg_papers.paper = orkg_papers.paper.apply(uri_to_id)

    while (len(rest_uncompared_papers) + len(uncompared_paper_ids)) * UNCOMPARED_PAPERS_THRESHOLD < len(paper_ids):
        orkg_paper = orkg_papers.sample(n=1).iloc[0]

        # papers have not been seen before by ID
        if orkg_paper.loc['paper'] in paper_ids + uncompared_paper_ids + rest_uncompared_paper_ids:
            continue

        # papers have not been seen before by label
        if orkg_paper.loc['paper_title'] in paper_labels + uncompared_paper_labels + rest_uncompared_paper_labels:
            continue

        if len(papers_dump[papers_dump.uri == id_to_uri(orkg_paper.loc['paper'])].processed_abstract) != 0 \
                and papers_dump[papers_dump.uri == id_to_uri(orkg_paper.loc['paper'])].processed_abstract.iloc[0]:

            problems_df = query(TRIPLE_STORE_URL, RESEARCH_PROBLEMS_BY_PAPER(uri_to_id(orkg_paper.loc['paper'])))
            problems_df.id = problems_df.id.apply(uri_to_id)
            uncompared_paper = {
                'id': uri_to_id(orkg_paper.loc['paper']),
                'label': orkg_paper.loc['paper_title'],
                'doi': orkg_paper.loc['doi'],
                'research_field': {
                    'id': uri_to_id(orkg_paper.loc['research_field']),
                    'label': orkg_paper.loc['research_field_label']
                },
                'research_problems': problems_df.drop_duplicates().to_dict(orient='records'),
                'abstract': papers_dump[
                    papers_dump.uri == id_to_uri(orkg_paper.loc['paper'])
                ].processed_abstract.iloc[0]
            }

            rest_uncompared_papers.append(uncompared_paper)
            rest_uncompared_paper_ids.append(orkg_paper.loc['paper'])
            rest_uncompared_paper_labels.append(orkg_paper.loc['paper_title'])

    return rest_uncompared_papers, rest_uncompared_paper_ids, rest_uncompared_paper_labels


def extract_papers_research_fields(comparisons):
    research_fields = {}

    for comparison in comparisons:
        for paper in comparison['papers']:

            if paper['research_field']['id'] not in research_fields:
                research_fields[paper['research_field']['id']] = {'label': '', 'papers': []}

            research_fields[paper['research_field']['id']]['label'] = paper['research_field']['label']

            if paper['id'] not in research_fields[paper['research_field']['id']]['papers']:
                research_fields[paper['research_field']['id']]['papers'].append(paper['id'])

    return research_fields


def extract_papers(comparisons):
    paper_ids = []
    paper_labels = []
    for comparison in comparisons:
        for paper in comparison['papers']:
            paper_ids.append(paper['id'])
            paper_labels.append(paper['label'])

    paper_ids = list(map(uri_to_id, paper_ids))
    return list(set(paper_ids)), list(set(paper_labels))


def verify(paper_ids, paper_labels, uncompared_papers):
    uncompared_paper_ids = []
    uncompared_paper_labels = []
    for uncompared_paper in uncompared_papers:
        uncompared_paper_ids.append(uncompared_paper['id'])
        uncompared_paper_labels.append(uncompared_paper['label'])

    if len(uncompared_paper_ids) != len(list(set(uncompared_paper_ids))):
        warnings.warn('uncompared_paper_ids are not distinct!')

    if len(uncompared_paper_labels) != len(list(set(uncompared_paper_labels))):
        warnings.warn('uncompared_paper_labels are not distinct!')

    if not set(paper_ids).isdisjoint(uncompared_paper_ids):
        warnings.warn('paper_ids and uncompared_paper_ids are not disjoint!')

    if not set(paper_labels).isdisjoint(uncompared_paper_labels):
        warnings.warn('paper_labels and uncompared_paper_labels are not disjoint!')


def main(comparisons, papers_dump):
    # preparing what we already have.
    research_fields = extract_papers_research_fields(comparisons)
    paper_ids, paper_labels = extract_papers(comparisons)

    # preparing uncompared_papers with same/similar distribution as the compared papers
    uncompared_papers, uncompared_paper_ids, uncompared_paper_labels = fetch_uncompared_papers_with_same_distribution(
        paper_ids, paper_labels, papers_dump, research_fields
    )

    # if not enough uncompared papers could be found, fetch the rest from different research fields
    rest_uncompared_papers, rest_uncompared_paper_ids, rest_uncompared_paper_labels = fetch_rest_uncompared_papers(
        paper_ids, paper_labels, uncompared_paper_ids, uncompared_paper_labels, papers_dump
    )

    uncompared_papers += rest_uncompared_papers

    verify(paper_ids, paper_labels, uncompared_papers)

    Writer.write_json({'uncompared_papers': uncompared_papers}, os.path.join(RAW_DATA_DIR, 'uncompared_papers.json'))

    return uncompared_papers


if __name__ == '__main__':
    dataset = Reader.read_json(os.path.join(RAW_DATA_DIR, 'compared_papers.json'))
    dump = pd.read_csv(os.path.join(RAW_DATA_DIR, 'orkg_papers.csv')).fillna('')

    main(dataset['comparisons'], dump)
