from matplotlib import pyplot as plt
import numpy as np
import scienceplots
from functools import partial

def homology_fitness(V, D, T):
    def f(h, V, D, T):
        return -V - np.exp(np.log(V) * (1-h)/(1-T) - D) + np.exp(np.log(V) - D)

    return partial(f, V=V, D=D, T=T)

if __name__ == '__main__':
    import matplotlib
    plt.style.use(['science', 'no-latex'])
    V = 2000
    T = 0.8
    t = np.linspace(T-0.05, T+0.05, 1000)[:-1]
    matplotlib.rcParams.update({'font.size': 18})


    fig, ax = plt.subplots(figsize=(10,7))
    for D in [0, 0.5, 1, 2]:
        fh = homology_fitness(V=V, D=D, T=T)
        ax.plot(t, fh(t), label=f'$D={D}$')

    ax.set_xticks(ticks=[T -0.05, T, T + 0.05], labels=['$T -5\%$', '$T$', '$ T + 5\%$'])
    ax.set_ylim(-4*V, 0)
    ax.set_yticks(ticks=[0, -V, -2*V, -3*V], labels=[0, '$-V$', '$-2V$', '$-3V$'])
    ax.axhline(y=-V, xmin=0, xmax=0.5, c='#202020', linewidth=0.5)
    ax.axvline(x=T, ymin=0, ymax=0.75, c='#202020', linewidth=0.5)
    ax.set_xlabel('$h$')
    ax.set_ylabel('$f_h$')

    fig.legend(loc=(0.75, 0.2))
    fig.tight_layout()
    fig.savefig('./figures/homology_fitness.png', dpi=300)

