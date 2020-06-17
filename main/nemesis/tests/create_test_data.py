import itertools
import random
import string
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

random.seed(12345)
df = pd.DataFrame({
    'A': [random.randint(45, 55) for i in range(1000)],
    'B': [random.randint(30, 70) for i in range(1000)],
    'C': [random.randint(10, 90) for i in range(1000)],
    'D': [random.randint(05, 95) for i in range(1000)],
    'W': [random.randint(91, 97) for i in range(1000)],
    'X': [random.randint(17, 32) for i in range(1000)],
    'Y': [random.randint(26, 67) for i in range(1000)],
    'Z': [random.randint(05, 95) for i in range(1000)],
}).melt()
df.columns = ['Letter', 'Number']
df_path = sys.path[-1] + '/main/nemesis/tests/test_letters_numbers_1.csv'
df.to_csv(df_path, index_label='Id')

dfs = df.sample(250, replace=True)
dfs_path = sys.path[-1] + '/main/nemesis/tests/test_letters_numbers_2.csv'
dfs.to_csv(dfs_path, index_label='Id')

for val in dfs['Letter'].value_counts().index.values:
    dfs.loc[dfs['Letter'] == val, 'Number'].plot.kde()
plt.show()


def create_test_data(
        letters=list(string.ascii_uppercase)[:4],
        colors=['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple', 'Pink'],
        numbers=[1.0 * number / 10 for number in range(10)]
):
    ncombos = len(letters) * len(colors) * len(numbers)
    group_X = []
    categorical_X = []
    continuous_X = []

    for letter in letters:
        for color in colors:
            for number in numbers:
                group_X.append(letter)
                categorical_X.append(color)
                continuous_X.append(number)

    df = pd.DataFrame({
        'Letter': group_X,
        'Color': categorical_X,
        'Number': continuous_X,
    })

    assert df.shape[0] == ncombos
    return df


df0 = create_test_data()[['Letter', 'Color', 'Number']]

c1 = df0['Letter'] == 'B'
c2 = df0['Number'] > 0.5
c3 = df0['Letter'] == 'C'
c4 = df0['Number'] > 0.8
c5 = df0['Letter'] == 'D'
c6 = df0['Number'] > 0.2

df1 = df0.copy()
df1.loc[c1 & c2, 'Number'] = 0.0
df1.loc[c3 & c4, 'Number'] = 0.0
df1.loc[c5 & c6, 'Number'] = 0.0
df1 = df1.sample(100, replace=True)
df1_path = sys.path[-1] + '/main/nemesis/tests/test_letters_numbers_with_zeros.csv'
df1.to_csv(df1_path, index_label='Id')

df2 = df0.copy()
df2 = df2[~(c1 & c2)]
df2 = df2[~(c3 & c4)]
df2 = df2[~(c5 & c6)]
df2 = df2.sample(100, replace=True)
df2_path = sys.path[-1] + '/main/nemesis/tests/test_letters_numbers_with_missing.csv'
df2.to_csv(df2_path, index_label='Id')

df3 = df0.copy()
df3.loc[c1 & c2, 'Number'] = None
df3.loc[c3 & c4, 'Number'] = None
df3.loc[c5 & c6, 'Number'] = None
df3_path = sys.path[-1] + '/main/nemesis/tests/test_letters_numbers_with_blanks.csv'
df3 = df3.sample(100, replace=True)
df3.to_csv(df3_path, index_label='Id')

# fig, axs = plt.subplots(nrows=4, ncols=1)
for val in df1['Letter'].value_counts().index.values:
    df1.loc[df1['Letter'] == val, 'Number'].plot.kde()
plt.show()

for val in df2['Letter'].value_counts().index.values:
    df2.loc[df2['Letter'] == val, 'Number'].plot.kde()
plt.show()

def choose(n, k):
    """
    A fast way to calculate binomial coefficients by Andrew Dalke (contrib).
    """
    if 0 <= k <= n:
        ntok = 1
        ktok = 1
        for t in xrange(1, min(k, n - k) + 1):
            ntok *= n
            ktok *= t
            n -= 1
        return ntok // ktok
    else:
        return 0

for grp in df2['Letter'].unique():
    print(choose(df1.groupby('Letter').size()[grp], 2) / choose(len(df1.groupby('Letter')['Number'].unique()[grp]), 2))

x = [
    choose(df1.groupby('Letter').size()[grp], 2) / \
    choose(len(df1.groupby('Letter')['Number'].unique()[grp]), 2)
    for grp in df2['Letter'].unique()
]

(x - np.mean(x))/np.std(x)