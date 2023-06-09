from collections import Counter


def sort_list_by_occurrences(l):
    counts = dict(Counter(l))
    return sorted(list(counts.keys()), key=lambda element: counts[element], reverse=True)


def list_unique_elements(l):
    unique_list = []
    for element in l:

        if element in unique_list:
            continue

        unique_list.append(element)

    return unique_list


def flatten(t, key=None):
    flattened = []

    for sublist in t:
        for item in sublist:
            if key:
                flattened.append(item[key])
            else:
                flattened.append(item)

    return flattened
