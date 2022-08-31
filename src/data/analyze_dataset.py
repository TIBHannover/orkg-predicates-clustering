import os
import pandas as pd
import numpy as np

from src import PROCESSED_DATA_DIR
from src.util.io import Reader, Writer
from src.util.list import sort_list_by_occurrences, list_unique_elements
from src.util.visualization import scatter_plot, scatters_plot


def statistics_per_entity(dataset, entity_name, dir_path):
    assert entity_name in ['comparison', 'predicate'], 'entity can be either "comparison" or "predicate"'

    other_entity_name = {
        'predicate': 'comparison',
        'comparison': 'predicate'
    }[entity_name]

    statistics = {entity_name + 's': []}

    contributions_per_entity = []
    overall_contribution_ids = []
    papers_per_entity = []
    overall_paper_ids = []
    fields_per_entity = []
    overall_field_ids = []
    problems_per_entity = []
    overall_problem_ids = []
    other_entities_per_entity = []
    overall_other_entity_ids = []
    for entity in dataset[entity_name + 's']:
        contribution_ids = entity['contributions']
        paper_ids = [paper['id'] for paper in entity['papers']]
        research_field_ids = [paper['research_field']['id'] for paper in entity['papers']]
        research_field_labels = [paper['research_field']['label'] for paper in entity['papers']]
        research_problem_labels = [problem['label'] for paper in entity['papers'] for problem in
                                   paper['research_problems'] if problem['label']]
        other_entity_ids = [other_entity['id'] for other_entity in entity[other_entity_name + 's']]

        overall_contribution_ids.extend(contribution_ids)
        contributions_per_entity.append(len(contribution_ids))

        overall_paper_ids.extend(paper_ids)
        papers_per_entity.append(len(paper_ids))

        overall_field_ids.extend(list(set(research_field_ids)))
        fields_per_entity.append(len(list(set(research_field_ids))))

        # there are many redundant problems that have same label but different ID.
        overall_problem_ids.extend(list(set(research_problem_labels)))
        problems_per_entity.append(len(list(set(research_problem_labels))))

        overall_other_entity_ids.extend(other_entity_ids)
        other_entities_per_entity.append(len(other_entity_ids))

        statistics[entity_name + 's'].append({
            'id': entity['id'],
            'contributions': len(contribution_ids),
            'papers': len(entity['papers']),
            other_entity_name + 's': len(entity[other_entity_name + 's']),
            'research_fields': len(list(set(research_field_ids))),
            'research_problems': len(list(set(research_problem_labels))),
            'frequent_field_ids': ';'.join(sort_list_by_occurrences(research_field_ids)[:5]),
            'frequent_field_labels': ';'.join(sort_list_by_occurrences(research_field_labels)[:5]),
            'problem_labels': ';'.join(list_unique_elements(research_problem_labels))
        })

    statistics[entity_name + 's'] = sorted(statistics[entity_name + 's'], key=lambda e: e['papers'], reverse=True)
    df = pd.json_normalize(statistics[entity_name + 's'])

    statistics['number_of_' + entity_name + 's'] = len(statistics[entity_name + 's'])
    statistics['number_of_contributions'] = len(list(set(overall_contribution_ids)))
    statistics['avg_contributions_per_' + entity_name] = np.average(contributions_per_entity)
    statistics['min_contributions_per_' + entity_name] = min(contributions_per_entity)
    statistics['max_contributions_per_' + entity_name] = max(contributions_per_entity)

    statistics['number_of_papers'] = len(list(set(overall_paper_ids)))
    statistics['avg_papers_per_' + entity_name] = np.average(papers_per_entity)
    statistics['min_papers_per_' + entity_name] = min(papers_per_entity)
    statistics['max_papers_per_' + entity_name] = max(papers_per_entity)

    statistics['number_of_' + other_entity_name + 's'] = len(list(set(overall_other_entity_ids)))
    statistics['avg_' + other_entity_name + 's_per_' + entity_name] = np.average(
        other_entities_per_entity)
    statistics['min_' + other_entity_name + 's_per_' + entity_name] = min(other_entities_per_entity)
    statistics['max_' + other_entity_name + 's_per_' + entity_name] = max(other_entities_per_entity)

    statistics['number_of_research_fields'] = len(list(set(overall_field_ids)))
    statistics['avg_research_fields_per_' + entity_name] = np.average(fields_per_entity)
    statistics['min_research_fields_per_' + entity_name] = min(fields_per_entity)
    statistics['max_research_fields_per_' + entity_name] = max(fields_per_entity)

    statistics['number_of_research_problems'] = len(list(set(overall_problem_ids)))
    statistics['avg_research_problems_per_' + entity_name] = np.average(problems_per_entity)
    statistics['min_research_problems_per_' + entity_name] = min(problems_per_entity)
    statistics['max_research_problems_per_' + entity_name] = max(problems_per_entity)

    statistics['correlation_papers_fields'] = df['papers'].corr(df['research_fields'])
    statistics['correlation_papers_' + other_entity_name + 's'] = df['papers'].corr(df[other_entity_name + 's'])
    statistics['correlation_papers_problems'] = df['papers'].corr(df['research_problems'])
    statistics['correlation_fields_problems'] = df['research_fields'].corr(df['research_problems'])

    text = ''
    for key, value in statistics.items():
        if key == entity_name + 's':
            continue
        text += '{}: {}\n'.format(key, value)

    os.makedirs(dir_path, exist_ok=True)
    df.to_csv(os.path.join(dir_path, 'statistics.csv'), index=False)
    Writer.write_txt(text, os.path.join(dir_path, 'statistics.txt'))

    # ----------------- Plots -----------------
    plot_entities = [other_entity_name + 's', 'contributions', 'papers', 'research_fields', 'research_problems']

    for i, plot_entity in enumerate(plot_entities):
        plot = scatter_plot(df['id'], df[plot_entity].sort_values(ascending=False),
                            '{} (total={})'.format(entity_name + 's',
                                                   statistics['number_of_' + entity_name + 's']),
                            '# {}'.format(plot_entity),
                            [statistics['number_of_{}'.format(plot_entity)],
                             statistics['avg_' + plot_entity + '_per_' + entity_name],
                             statistics['min_' + plot_entity + '_per_' + entity_name],
                             statistics['max_' + plot_entity + '_per_' + entity_name]],
                            entity_name)

        Writer.write_png(plot, os.path.join(dir_path, '{:02d}_{}_distribution.png'.format(i, plot_entity)))

    distributions = scatters_plot(
        x_data=df['id'],
        y_data=[df['contributions'], df['papers'], df['research_fields'], df['research_problems']],
        x_label='{} (total={})'.format(entity_name + 's', statistics['number_of_' + entity_name + 's']),
        y_label='Value',
        legend_labels=['Contributions (total={})'.format(statistics['number_of_contributions']),
                       'Papers (total={})'.format(statistics['number_of_papers']),
                       'Research Fields (total={})'.format(statistics['number_of_research_fields']),
                       'Research Problems (total={})'.format(statistics['number_of_research_problems'])
                       ])

    Writer.write_png(distributions, os.path.join(dir_path, '99_distributions.png'))


def extract_predicates(dataset):
    predicates = {}
    for comparison in dataset['comparisons']:
        for predicate in comparison['predicates']:
            if predicate['id'] not in predicates:
                predicates[predicate['id']] = {
                    'label': predicate['label'],
                    'comparisons': [{'id': comparison['id']}],
                    'papers': comparison['papers'],
                    'contributions': comparison['contributions']
                }
            else:
                predicates[predicate['id']]['comparisons'].append({'id': comparison['id']})
                predicates[predicate['id']]['papers'].extend(comparison['papers'])
                predicates[predicate['id']]['contributions'].extend(comparison['contributions'])

    data_predicates = {'predicates': []}
    for predicate in predicates.keys():
        data_predicates['predicates'].append({
            'id': predicate,
            'label': predicates[predicate]['label'],
            'comparisons': predicates[predicate]['comparisons'],
            'papers': filter_papers(predicates[predicate]['papers']),
            'contributions': list(set(predicates[predicate]['contributions']))
        })

    return data_predicates


def filter_papers(papers):
    filtered_papers = []
    paper_ids = []

    for paper in papers:
        if paper['id'] in paper_ids:
            continue

        filtered_papers.append(paper)
        paper_ids.append(paper['id'])

    return filtered_papers


def main(dataset):
    statistics_per_entity(
        dataset,
        entity_name='comparison',
        dir_path=os.path.join(PROCESSED_DATA_DIR, 'by_comparison')
    )

    by_predicates = extract_predicates(dataset)
    statistics_per_entity(
        by_predicates,
        entity_name='predicate',
        dir_path=os.path.join(PROCESSED_DATA_DIR, 'by_predicate')
    )


if __name__ == '__main__':
    data = Reader.read_json(os.path.join(PROCESSED_DATA_DIR, 'dataset.json'))
    main(data)
