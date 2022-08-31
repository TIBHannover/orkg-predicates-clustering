import os

import pandas as pd

from src import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.data import fetch_compared_papers, fetch_uncompared_papers
from src.data.split_dataset import get_paper_contributions
from src.util.io import Writer
from src.util.list import flatten


def main(config=None):
    # TODO: automatically download the orkg_papers dump
    papers_dump = pd.read_csv(os.path.join(RAW_DATA_DIR, 'orkg_papers.csv')).fillna('')

    comparisons = fetch_compared_papers.main(papers_dump)
    uncompared_papers = fetch_uncompared_papers.main(comparisons, papers_dump)

    comparisons.append({
        'id': 'EMPTY',
        'label': 'Empty comparison representing the negative case.',
        'predicates': [],
        'contributions': list(set(flatten([get_paper_contributions(paper['id']) for paper in uncompared_papers]))),
        'papers': uncompared_papers
    })

    comparisons_predicates = {}
    for comparison in comparisons:
        comparisons_predicates[comparison['id']] = comparison['predicates']

    Writer.write_json({'comparisons': comparisons}, os.path.join(PROCESSED_DATA_DIR, 'dataset.json'))
    Writer.write_json(comparisons_predicates, os.path.join(PROCESSED_DATA_DIR, 'mapping.json'))

    return {'comparisons': comparisons}


if __name__ == '__main__':
    main()
