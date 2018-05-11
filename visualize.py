import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation
from IPython.display import HTML, display
import scipy
import scipy.signal
import scipy.ndimage
import matplotlib.patches
import matplotlib.cm
import adjustText

def triangle_scatter_players(
    players_coords,
    players_to_highlight=[],
    clusters_to_highlight=[],
    points_to_label=[],
    title=None,
    tick_size=[.1,.1],
    bounds=[[0,1],[0,1]],
    color=(None, None),
    alpha=0.5,
    saveas=None,
    label=True,
    points_to_highlight=[]):
    
    # Check if we should plot the points in any particular colors, or with specific sizes
    c_func = color[0] if color is not None else None
    c_label = color[1] if color is not None else None
    s_func = lambda player, counts, coords: 0.1*sum(count for action, count in counts.items())
    
    # Make a figure
    fig = plt.figure(figsize=(15, 15))
    ax = plt.gca()
    ax.set_axis_off()
    if title is not None:
        plt.title(title)
    texts = []
    
    # Draw the triangular grid
    xrange = bounds[0][1]-bounds[0][0]
    yrange = bounds[1][1]-bounds[1][0]
    for p in np.arange(bounds[1][0],bounds[1][1]+.000001,tick_size[1]):
        x1 = 0.5*p
        x2 = 1-0.5*p
        y1 = 0.866*p
        y2 = 0.866*p
        if x1 < bounds[0][0]:
            frac_keep = (x2 - bounds[0][0])/(x2 - x1)
            x1 = x2 + frac_keep * (x1 - x2)
            y1 = y2 + frac_keep * (y1 - y2)
        if x2 > bounds[0][1]:
            frac_keep = (bounds[0][1] - x1)/(x2 - x1)
            x2 = x1 + frac_keep * (x2 - x1)
            y2 = y1 + frac_keep * (y2 - y1)
        if y1 < bounds[1][0]:
            frac_keep = (y2 - bounds[1][0])/(y2 - y1)
            x1 = x2 + frac_keep * (x1 - x2)
            y1 = y2 + frac_keep * (y1 - y2)
        if y2 > bounds[1][1]:
            frac_keep = (bounds[1][1] - y1)/(y2 - y1)
            x2 = x1 + frac_keep * (x2 - x1)
            y2 = y1 + frac_keep * (y2 - y1)
        x2 += 0.05*xrange*1.000
        y2 += 0.05*xrange*0.000
        ax.plot([x1,x2],[y1,y2],color='grey')
        ax.text(
            s="shoot {:.2f} ".format(p),
            fontsize='large',
            x=x2,
            y=y2,
            horizontalalignment='left',
            verticalalignment='center',
            zorder=1)
    for p in np.arange(bounds[0][0],bounds[0][1]+.000001,tick_size[0]):
        x1 = p
        x2 = 0.500*(1 + p)
        y1 = 0
        y2 = 0.866*(1 - p)
        if x1 < bounds[0][0]:
            frac_keep = (x2 - bounds[0][0])/(x2 - x1)
            x1 = x2 + frac_keep * (x1 - x2)
            y1 = y2 + frac_keep * (y1 - y2)
        if x2 > bounds[0][1]:
            frac_keep = (bounds[0][1] - x1)/(x2 - x1)
            x2 = x1 + frac_keep * (x2 - x1)
            y2 = y1 + frac_keep * (y2 - y1)
        if y1 < bounds[1][0]:
            frac_keep = (y2 - bounds[1][0])/(y2 - y1)
            x1 = x2 + frac_keep * (x1 - x2)
            y1 = y2 + frac_keep * (y1 - y2)
        if y2 > bounds[1][1]:
            frac_keep = (bounds[1][1] - y1)/(y2 - y1)
            x2 = x1 + frac_keep * (x2 - x1)
            y2 = y1 + frac_keep * (y2 - y1)
        x1 -= 0.05*yrange*0.500
        y1 -= 0.05*yrange*0.866
        ax.plot([x1,x2],[y1,y2],color='grey')
        ax.text(
            s="pass {:.2f} ".format(p),
            fontsize='large',
            x=x1,
            y=y1,
            horizontalalignment='right',
            verticalalignment='center',
            rotation=60,
            rotation_mode='anchor',
            zorder=1)
    for p in np.arange(bounds[0][0],bounds[0][1]+.000001,tick_size[0]):
        x1 = 0.500*p
        x2 = p
        y1 = 0.866*p
        y2 = 0
        if x1 < bounds[0][0]:
            frac_keep = (x2 - bounds[0][0])/(x2 - x1)
            x1 = x2 + frac_keep * (x1 - x2)
            y1 = y2 + frac_keep * (y1 - y2)
        if x2 > bounds[0][1]:
            frac_keep = (bounds[0][1] - x1)/(x2 - x1)
            x2 = x1 + frac_keep * (x2 - x1)
            y2 = y1 + frac_keep * (y2 - y1)
        if y1 < bounds[1][0]:
            frac_keep = (y2 - bounds[1][0])/(y2 - y1)
            x1 = x2 + frac_keep * (x1 - x2)
            y1 = y2 + frac_keep * (y1 - y2)
        if y2 > bounds[1][1]:
            frac_keep = (bounds[1][1] - y1)/(y2 - y1)
            x2 = x1 + frac_keep * (x2 - x1)
            y2 = y1 + frac_keep * (y2 - y1)
        if y1 > bounds[1][1]:
            frac_keep = (y2 - bounds[1][1])/(y2 - y1)
            x1 = x2 + frac_keep * (x1 - x2)
            y1 = y2 + frac_keep * (y1 - y2)
        if y2 < bounds[1][0]:
            frac_keep = (bounds[1][0] - y1)/(y2 - y1)
            x2 = x1 + frac_keep * (x1 - x2)
            y2 = y1 + frac_keep * (y1 - y2)
        print()
        x1 -= 0.05*yrange*0.500
        y1 += 0.05*yrange*0.866
        ax.plot([x1,x2],[y1,y2],color='grey')
        ax.text(
            s="dribble {:.2f} ".format(1-p),
            fontsize='large',
            x=x1,
            y=y1,
            horizontalalignment='right',
            verticalalignment='center',
            rotation=-60,
            rotation_mode='anchor',
            zorder=1)
    
    # Scatter all the players
    scatterplot = ax.scatter(
        x=[coords[0] for player, counts, coords in players_coords],
        y=[coords[1] for player, counts, coords in players_coords],
        alpha=alpha,
        c=None if c_func is None else [c_func(player, counts, coords)
                                       for player, counts, coords in players_coords],
        s=None if s_func is None else [s_func(player, counts, coords)
                                       for player, counts, coords in players_coords]
    )
    if c_func is not None:
        colorbar = plt.colorbar(scatterplot, label=c_label)
        colorbar.set_alpha(1)
        colorbar.draw_all()
    
    # Label the players requested
    for name in players_to_highlight:
        try:
            player, counts, coords = next((player, counts, coords)
                                          for player, counts, coords in players_coords
                                          if player['name'] == name)
        except StopIteration:
            continue
        if label:
            texts.append(plt.text(
                s=name,
                x=coords[0],
                y=coords[1],
                bbox=dict(boxstyle='round,pad=0.5', fc='orange'),
                zorder=5))
    
    # Draw the points requested
    for point in points_to_highlight:
        ax.scatter(
            x=point[0],
            y=point[1],
            c=0.4,
            s=300,
            cmap=scatterplot.get_cmap()
        ).set_clim(scatterplot.get_clim())
    
    # Label the points requested
    for color, label, point in points_to_label:
        ax.annotate(
            s=label,
            xy=point,
            xytext=point,
            bbox=dict(boxstyle='round,pad=0.5', fc=color),
            arrowprops=dict(arrowstyle="->", color=color, lw=4),
            zorder=5).draggable()
    
    # Scatter the clusters requested
    for color, points_list in clusters_to_highlight:
        ax.scatter(
            x=[point[0] for point in points_list],
            y=[point[1] for point in points_list],
            c=color,
            s=100)
    
    # Finish the plot
    adjustText.adjust_text(texts,
                           arrowprops=dict(arrowstyle="->", color='orange', lw=4),
                           expand_points=(3, 3),
                           expand_text=(2, 2))
    annotation_text = ax.text(
            s='',
            x=bounds[0][0],
            y=bounds[1][0],
            bbox=dict(boxstyle='round,pad=0.5', fc='lime'),
            zorder=6)
    plt.show()
    
    # Save the plot if desired
    if saveas is not None:
        plt.savefig(saveas, format="svg")
    
    # Make the plot interactive if applicable: display the player name while hovering
    def hover_playername(event):
        in_points, indices = scatterplot.contains(event)
        if in_points == True:
            names = '\n'.join(players_coords[n][0]['name'] for n in indices['ind'])
            annotation_text.set_text(names)
        else:
            annotation_text.set_text('')
        fig.canvas.draw_idle()
    fig.canvas.mpl_connect('motion_notify_event', hover_playername)

def plot_pass_shoot(
    players_records,
    players_to_highlight=[],
    points_to_highlight=[],
    title=None,
    label=False,
    color=(None,None),
    clusters_to_highlight=[],
    points_to_label=[],
    saveas=None,
    bounds=None,
    alpha=0.4):
    
    # Check if we should plot the points in any particular colors, or with specific sizes
    c_func = color[0] if color is not None else None
    c_label = color[1] if color is not None else None
    
    # Collect the data that should be plotted
    data_to_plot = {'x':[],'y':[],'c':[],'s':[]}
    data_names = []
    for player_name, player_record in players_records:
        if len(player_record['passing']) > 5 and len(player_record['shooting']) > 5:
            data_to_plot['x'].append(player_record['average passing'])
            data_to_plot['y'].append(player_record['average shooting'])
            data_to_plot['c'].append(c_func(player_record) if c_func is not None else None)
            data_to_plot['s'].append(player_record['number of entries'])
            data_names.append(player_name)
    
    # Make a figure, and label the axes
    fig = plt.figure(figsize=(15,15))
    ax = fig.add_subplot(1,1,1)
    scatterplot = ax.scatter(
        x=data_to_plot['x'],
        y=data_to_plot['y'],
        c=data_to_plot['c'] if c_func is not None else None,
        s=data_to_plot['s'],
        zorder=1,
        alpha=alpha,
        cmap='viridis')
    if c_func is not None:
        fig.colorbar(scatterplot, label="Shooting Skill")
    ax.set_xlabel('Shot quality taken by next player')
    ax.set_ylabel('Shot quality taken by self')
    if title is not None:
        ax.set_title(title)
    if bounds is not None:
        ax.set_xlim(bounds[0])
        ax.set_ylim(bounds[1])
    texts_to_avoid = []
    objs_to_avoid = []
    points_to_avoid_x = []
    points_to_avoid_y = []
    
    # Label the players requested
    for player_to_highlight in players_to_highlight:
        try:
            player, player_record = next((player, player_record)
                                         for player, player_record in players_records
                                         if player['name'] == player_to_highlight)
        except StopIteration:
            continue
        xy = [player_record['average passing'],
              player_record['average shooting']]
        texts_to_avoid.append(ax.text(
            s="{}".format(player_to_highlight),
            x=xy[0],
            y=xy[1],
            bbox=dict(boxstyle='round,pad=0.5', fc='orange'),
            zorder=5))
        points_to_avoid_x.append(xy[0])
        points_to_avoid_y.append(xy[1])
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
        ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize('xx-large')
    
    # Draw the poitns requested
    for point in points_to_highlight:
        ax.scatter(
            x=point[0],
            y=point[1],
            c=0,
            s=300,
            cmap=scatterplot.get_cmap()
        ).set_clim(scatterplot.get_clim())
        
    # Label the points requested
    for color, label, point in points_to_label:
        ax.annotate(
            s=label,
            xy=point,
            xytext=point,
            size='x-large',
            bbox=dict(boxstyle='round,pad=0.5', fc=color),
            arrowprops=dict(arrowstyle="->", color=color, lw=4),
            zorder=5).draggable()
        
    # Scatter the clusters requested
    for color, points_list in clusters_to_highlight:
        ax.scatter(
            x=[point[0] for point in points_list],
            y=[point[1] for point in points_list],
            c=color,
            s=100)
    
    # Finish the plot
    adjustText.adjust_text(texts_to_avoid,
                           arrowprops=dict(arrowstyle="->", color='orange', lw=4),
                           expand_points=(5, 5),
                           expand_text=(2, 2),
                           x=points_to_avoid_x,
                           y=points_to_avoid_y,
                           ax=ax)
    annotation_text = ax.text(
            s='',
            x=bounds[0][1] if bounds is not None else 47,
            y=bounds[1][0] if bounds is not None else 47,
            bbox=dict(boxstyle='round,pad=0.5', fc='lime'),
            zorder=6)
    
    # Save the plot if desired
    if saveas is not None:
        plt.savefig(saveas, format="svg")
    
    # Make the plot interactive if applicable: display the player name while hovering
    def hover_playername(event):
        in_points, indices = scatterplot.contains(event)
        if in_points == True:
            names = '\n'.join(data_names[n]['name'] for n in indices['ind'])
            annotation_text.set_text(names)
        else:
            annotation_text.set_text('')
        fig.canvas.draw_idle()
    fig.canvas.mpl_connect('motion_notify_event', hover_playername)