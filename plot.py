import io 
import numpy as np
import matplotlib.pyplot as plt

def build_position(student, result):
    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(aspect="equal"))

    recipe = [f'100 0 niveau{i+1}' for i in range(3)]
    sn = student['niveau']
    new_sn = sn + result if sn < 3 else sn 
    if new_sn > sn:
        recipe[sn - 1] = f'100 A niveau{sn}'
        recipe[new_sn - 1] = f'100 1 niveau{new_sn}'
    else:
        recipe[sn - 1] = f'100 1 niveau{sn}'

    data = [float(x.split()[0]) for x in recipe]
    ingredients = [x.split()[-1] for x in recipe]

    wedges, texts, autotexts = ax.pie(
        data, 
        autopct=lambda pct: '', 
        textprops=dict(color="w"), 
        labels=ingredients, 
        wedgeprops=dict(width=0.5)
    )

    ax.legend(wedges, ingredients,
            title="niveaux",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1))


    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),
            bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        status = recipe[i].split()[1]
        if status in '1A':
            ang = (p.theta2 - p.theta1)/2. + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            status = recipe[i].split()[1]
            
            if status == '1':
                msg = student['nom']
            elif status == 'A':
                msg = 'ancienne position'
            ax.annotate(msg, xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y), horizontalalignment=horizontalalignment, **kw)

    plt.setp(autotexts, size=8, weight="bold")
    ax.set_title("positionnement élève")

    io_stream = io.BytesIO()
    plt.savefig(io_stream, format='jpg')
    io_stream.seek(0)
    return io_stream

