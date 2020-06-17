import itertools
import string
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def create_test_data(
        letters = list(string.ascii_uppercase)[-4:],
        colors=['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple', 'Pink'],
        numbers=[1.0*number/10 for number in range(10)]
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

c1 = df0['Letter'] == 'X'
c2 = df0['Number'] > 0.5
c3 = df0['Letter'] == 'Y'
c4 = df0['Number'] > 0.8
c5 = df0['Letter'] == 'Z'
c6 = df0['Number'] > 0.2

df1 = df0.copy()
df1.loc[c1 & c2, 'Number'] = 0.0
df1.loc[c3 & c4, 'Number'] = 0.0
df1.loc[c5 & c6, 'Number'] = 0.0
df1_path = sys.path[-1] + '/main/nemesis/tests/test_letters_numbers_with_zeros.csv'
df1.to_csv(df1_path, index_label='Id')

df2 = df0.copy()
df2 = df2[~(c1 & c2)]
df2 = df2[~(c3 & c4)]
df2 = df2[~(c5 & c6)]
df2_path = sys.path[-1] + '/main/nemesis/tests/test_letters_numbers_with_missing.csv'
df2.to_csv(df2_path, index_label='Id')


df3 = df0.copy()
df3.loc[c1 & c2, 'Number'] = None
df3.loc[c3 & c4, 'Number'] = None
df3.loc[c5 & c6, 'Number'] = None
df3_path = sys.path[-1] + '/main/nemesis/tests/test_letters_numbers_with_blanks.csv'
df3.to_csv(df3_path, index_label='Id')

# fig, axs = plt.subplots(nrows=4, ncols=1)
for val in df1['Letter'].value_counts().index.values:
    df1.loc[df1['Letter'] == val, 'Number'].plot.kde()
plt.show()

for val in df2['Letter'].value_counts().index.values:
    df2.loc[df2['Letter'] == val, 'Number'].plot.kde()
plt.show()

arr = np.sort(df0['Number'].value_counts().index.values)
[c for c in itertools.combinations(arr, len(arr))]

df1.groupby('Letter')['Number'].unique()

x = [
    np.float(len(df1.groupby('Letter')['Number'].unique()[grp])) / \
    np.float(len(df1['Number'].unique()))
    for grp in df1['Letter'].unique()
]

sns.barplot(df1['Letter'].unique(), x)
plt.show()

x-np.mean(x)/np.std(x)