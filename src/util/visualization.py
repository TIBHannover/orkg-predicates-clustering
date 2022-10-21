import io
import matplotlib.pyplot as plt

from PIL import Image

plt.rcParams["figure.figsize"] = (20, 10)


def scatter_plot(x_data, y_data, x_label, y_label, statistics, item='predicate'):
    plt.clf()

    fig = plt.figure()

    fig.text(0.6, 0.8,
             'total: {}\navg.:{}\nmin/{}: {}\nmax/{}: {}'.format(
                 statistics[0],
                 '{:.3f}'.format(statistics[1]),
                 item,
                 statistics[2],
                 item,
                 statistics[3]
             ),
             fontsize=30, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.scatter(x=x_data, y=y_data, s=6)
    plt.xlabel(x_label, fontsize=35)
    plt.ylabel(y_label, fontsize=35)

    plt.tick_params(
        axis='x',  # changes apply to the x-axis
        which='both',  # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelbottom=False)  # labels along the bottom edge are

    plt.tick_params(axis='y', labelsize=30)

    return convert_plot_to_object(plt)


def scatters_plot(x_data, y_data, x_label, y_label, legend_labels):
    plt.clf()
    markers = ['o', 'v', 'x', '*']

    for i, y in enumerate(y_data):
        plt.scatter(x=x_data, y=y, marker=markers[i], s=8, label=legend_labels[i])

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend(loc='best')

    plt.tick_params(
        axis='x',  # changes apply to the x-axis
        which='both',  # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelbottom=False)  # labels along the bottom edge are

    return convert_plot_to_object(plt)


def convert_plot_to_object(plt):
    """ converts matplotlib object into a PIL image object """
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    im = Image.open(buf)

    return im
