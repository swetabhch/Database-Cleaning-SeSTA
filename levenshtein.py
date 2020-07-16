import numpy as np

# compute levenshtein distance between strings a and b
def levenshtein(a, b):
    m, n = len(a)+1, len(b)+1
    matrix = np.zeros((m, n))
    for x in range(m):
        matrix[x, 0] = x
    for y in range(n):
        matrix[0, y] = y

    for x in range(1, m):
        for y in range(1, n):
            if a[x-1] == b[y-1]:
                substitutionCost = 0
            else:
                substitutionCost = 1
            matrix[x, y] = min(matrix[x-1, y]+1, # deletion
                            matrix[x, y-1]+1, # insertion
                            matrix[x-1, y-1] + substitutionCost) # substitution

    #print matrix
    return np.int(matrix[m-1, n-1])
