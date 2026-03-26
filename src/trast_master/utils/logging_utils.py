import matplotlib.pyplot as plt


def close_all_figures():
    plt.close("all")


def show_figure(fig=None):
    if fig is not None:
        fig.show()
    else:
        plt.show()