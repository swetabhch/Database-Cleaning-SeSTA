import numpy as np
import pandas as pd
from levenshtein import *

# read in data, replace variants of "no"
# use a levenshtein distance threshold of 2, not case-sensitive
def load_data(filename):
    df = pd.read_excel(filename)
    # replace "no" variants with np.nan
    for i in range(len(df['shgDetails:voName'])):
        if (not isinstance(df.loc[i, 'shgDetails:voName'], str)) or (levenshtein(df.loc[i, 'shgDetails:voName'].lower(), "no") <= 2):
            df.loc[i, 'shgDetails:voName'] = np.nan
    return df

# create and reduce references list
def references_list(df):
    global FREQ_THRESHOLD
    global REFERENCE_DISTANCE_THRESHOLD

    shgList = list(df['shgDetails:voName'].dropna())
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
            if refMatrix[i,j] <= REFERENCE_DISTANCE_THRESHOLD:
                a,b = shgReferences[i], shgReferences[j]
                if a != wildcard and b != wildcard:
                    shgReferences[i if shgList.count(a) < shgList.count(b) else j] = wildcard

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

# return dataframe with no duplicate records
def remove_duplicates(df):
    itemList = []
    for i in range(df.shape[0]):
        # items to compare for identity
        val = (df.loc[i, "nameKisan"], df.loc[i, 'guardianName'], df.loc[i, 'shgDetails:voName'])
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

# declaring threshold values
FREQ_THRESHOLD = 2
REFERENCE_DISTANCE_THRESHOLD = 3
EDIT_DISTANCE_THRESHOLD = 4
wildcard = 0

def main():

    # load data
    df = load_data('/Users/swetabhchangkakoti/Downloads/Tripura.xlsx')

    # get references list with wildcards
    shgReferences = references_list(df)
    # remove wildcards
    shgReferences = [x for x in shgReferences if x != wildcard]

    # get and autocorrect column
    shgDetails = list(df['shgDetails:voName'])
    autocorrect(shgDetails, shgReferences)
    df['shgDetails:voName'] = pd.Series(data=shgDetails).fillna("no")

    # get DataFrame without duplicates
    uniqueDf = remove_duplicates(df)

    # export data to excel file
    uniqueDf.to_excel(r'/Users/swetabhchangkakoti/Downloads/tripura_unique.xlsx')

main()
