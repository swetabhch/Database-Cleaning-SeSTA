import numpy as np
import pandas as pd

# declaring constant/threshold values
FREQ_THRESHOLD = 2
REFERENCE_DISTANCE_THRESHOLD = 3
EDIT_DISTANCE_THRESHOLD = 4
WILDCARD = 0

# input path
FILE_PATH = 'Tripura.xlsx'
# output path
FILE_OUT_PATH = r'tripura_unique.xlsx'
# stop_words file path
STOP_WORDS_PATH = 'stop_words.txt'

# get stop_words list
STOP_WORDS = [s[:-1] for s in open(STOP_WORDS_PATH, 'r').readlines()]
print(STOP_WORDS)

# column to autocorrect
COL_AUTO_NAME = 'shgDetails:voName'
# ID columns 1 and 2
COL_ID_1 = 'nameKisan'
COL_ID_2 = 'guardianName'

# - - - - - - - - - -

# helper function: compute levenshtein distance between strings a and b
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

# read in data, replace variants of "no"
# use a levenshtein distance threshold of 2, not case-sensitive
def load_data(filename):
    df = pd.read_excel(filename)
    # replace "no" variants with np.nan
    for i in range(len(df[COL_AUTO_NAME])):
        if (not isinstance(df.loc[i, COL_AUTO_NAME], str)) or (levenshtein(df.loc[i, COL_AUTO_NAME].lower(), "no") <= 2):
            df.loc[i, COL_AUTO_NAME] = np.nan
    return df

# create and reduce references list
def references_list(df):
    global FREQ_THRESHOLD
    global REFERENCE_DISTANCE_THRESHOLD

    shgList = list(df[COL_AUTO_NAME].dropna())
    shgReferences = []
    # TODO: optimze construction of shgReferences
    for shg in shgList:
        if (shgList.count(shg) > FREQ_THRESHOLD) and (shg not in shgReferences):
            shgReferences.append(shg)

    # create matrix of levenshtein distances between reference words
    n = len(shgReferences)
    refMatrix = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            refMatrix[i,j] = levenshtein(shgReferences[i], shgReferences[j])

    # reduce reference list to remove the majority of typos, store in shgReferences
    for j in range(1,n):
        for i in range(j):
            a,b = shgReferences[i], shgReferences[j]
            if a != WILDCARD and b != WILDCARD:
                # check if levenshtein distance less than threshold
                # select more common of the two words if so
                if refMatrix[i,j] <= REFERENCE_DISTANCE_THRESHOLD:
                    shgReferences[i if shgList.count(a) < shgList.count(b) else j] = WILDCARD
                elif " " in a and a.split(' ')[-1].lower() in STOP_WORDS:
                    a = " ".join(a.split(' ')[:-1])
                    shgReferences[i if shgList.count(a) < shgList.count(b) else j] = WILDCARD
                elif " " in b and b.split(' ')[-1].lower() in STOP_WORDS:
                    b = " ".join(b.split(' ')[:-1])
                    shgReferences[i if shgList.count(a) < shgList.count(b) else j] = WILDCARD


    return shgReferences

# autocorrect the values of a shgDetails column using shgReferences
def autocorrect(column, shgReferences):
    global EDIT_DISTANCE_THRESHOLD

    for i in range(len(column)):
        if not isinstance(column[i], str):
            continue
        else:
            for reference in shgReferences:
                if levenshtein(column[i].lower(), reference.lower()) <= EDIT_DISTANCE_THRESHOLD:
                    column[i] = reference
                # read in additional words from 'stopwords' config file
                elif " " in column[i] and column[i].split(' ')[-1].lower() in STOP_WORDS:
                        if levenshtein(" ".join(column[i].lower().split(' ')[:-1]), reference.lower()) <= EDIT_DISTANCE_THRESHOLD:
                            column[i] = reference

# return dataframe with no duplicate records
def remove_duplicates(df):
    itemList = []
    for i in range(df.shape[0]):
        # items to compare for identity
        val = (df.loc[i, COL_ID_1], df.loc[i, COL_ID_2], df.loc[i, COL_AUTO_NAME])
        item = (i, val)
        for other in itemList:
            if (other[1] == val):
                # comparison for number of null records
                if (df.loc[other[0]].isnull().sum() > df.loc[i].isnull().sum()):
                    itemList.remove(other)
                    itemList.append(item)
                break
        else:
            itemList.append(item)

    uniqueRecords = []
    for i in [x[0] for x in itemList]:
        uniqueRecords.append(dict(df.loc[i]))
    uniqueDf = pd.DataFrame(uniqueRecords)

    return uniqueDf

# - - - - - - - - - - -

def main():
    # load data
    df = load_data(FILE_PATH)

    # get references list with wildcards
    shgReferences = references_list(df)
    # remove wildcards
    shgReferences = [x for x in shgReferences if x != WILDCARD]

    # get and autocorrect column
    shgDetails = list(df[COL_AUTO_NAME])
    autocorrect(shgDetails, shgReferences)
    df[COL_AUTO_NAME] = pd.Series(data=shgDetails).fillna("no")

    # get DataFrame without duplicates
    uniqueDf = remove_duplicates(df)

    # export data to excel file
    uniqueDf.to_excel(FILE_OUT_PATH)

main()
