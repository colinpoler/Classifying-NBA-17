import random
import itertools
import numpy as np

# Find the minimum distance between corresponding points in two sets
# Use brute force to just try every possible arrangement
def find_correspondence_distance(a, b):
    # We want to assume that a is the longer list
    # If it isn't, swap them, and then do some work to invert the returned indices
    if len(a) < len(b):
        opposite, score = find_correspondence_distance(b, a)
        result = [None]*len(b)
        for i in range(len(opposite)):
            result[opposite[i]] = i
        return tuple(result), score
    
    # Compute the distance between every pair of points
    dists = [[0 for i in range(len(b))] for i in range(len(a))]
    for ia in range(len(a)):
        for ib in range(len(b)):
            dists[ia][ib] = (sum((a[ia][j] - b[ib][j])**2 for j in range(len(a[0]))))
    
    # Try every possible permutation of assignments, noting the best one
    assignment_indices = range(len(a))
    best_assignment = None
    best_assignment_score = float('inf')
    for assignment in itertools.permutations(assignment_indices, len(b)):
        assignment_score = sum(dists[assignment[i]][i] for i in range(len(assignment)))
        if assignment_score < best_assignment_score:
            best_assignment_score = assignment_score
            best_assignment = assignment
    
    return best_assignment, best_assignment_score

# Compute an average set of points between two other sets of points
# An average should minimize the sum of the correspondence_distances defined above
#     between the average and each of the input lists
def mean_correspondence_distance(lists):
    # If we don't get any lists, just return None
    if len(lists) == 0:
        return None
    
    # Choose the longest list to use as the master ordering
    original = max(lists, key=lambda x: len(x))
    
    # Sum up the lists with the correct ordering
    sums = [[0.0 for x in y] for y in original]
    counts = [0]*len(original)
    for new in lists:
        # Find the ordering that aligns with the master ordering
        assignment, _ = find_correspondence_distance(original, new)
        for i in range(len(new)):
            # Ignore unassigned indices
            if assignment[i] == None:
                continue
            
            # Add the point to the sum variable
            try:
                for j in range(len(new[i])):
                    sums[assignment[i]][j] += new[i][j]
                counts[assignment[i]] += 1
            except IndexError:
                print(original)
                print(new)
                print(assignment)
    
    # Divide by the number of inputs to get the average
    mean = [(sums[i][0]/counts[i],sums[i][1]/counts[i]) for i in range(len(sums))]
    return mean

# Implements k-means to iteratively find useful clusters of the data
def cluster_points(lists, n_groups, points_func=lambda x:x, iterations_after_none=10):
    # Randomly assign the inputs to different groups
    random.shuffle(lists)
    num_per_group = int(len(lists)/n_groups)
    groups = [{'mean': None,
               'nearest': lists[i*num_per_group:(i+1)*num_per_group],
               'score sum': 0
              } for i in range(n_groups)]
    
    # Keep running until some number of iterations have passed without an empty list
    count_since_none = 0
    while count_since_none < iterations_after_none:
        # Compute a new mean for the group
        for group in groups:
            group['mean'] = mean_correspondence_distance([points_func(obj)
                                                          for obj in group['nearest']])
            # If the list was empty, then just assign three inputs and compute a mean
            if group['mean'] is None:
                group['mean'] = mean_correspondence_distance([points_func(obj)
                                                              for obj in [random.choice(lists) for i in range(3)]])
                count_since_none = 0

        # Reset the inputs assigned to each group
        for group in groups:
            group['nearest'] = []
            group['score sum'] = 0
            group['clusters'] = [[] for x in group['mean']]
        
        # Assign each input to the group it is closest to
        for obj in lists:
            points = points_func(obj)
            best_group = None
            best_assignment = None
            best_score = float('inf')
            # Try every group, and just record the best group
            for group in groups:
                assignment, score = find_correspondence_distance(group['mean'], points)
                if score < best_score:
                    best_score = score
                    best_group = group
                    best_assignment = assignment
            best_group['score sum'] += best_score
            best_group['nearest'].append(obj)
            for i in range(len(best_assignment)):
                best_group['clusters'][best_assignment[i]].append((points_func(obj)[i], obj['players'][i]))
        count_since_none += 1
    
    # Compute the average score of the groups
    for group in groups:
        group['score average'] = group['score sum']*1.0/len(group['nearest'])
    return groups