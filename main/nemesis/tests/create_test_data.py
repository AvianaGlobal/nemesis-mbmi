import sys
import pandas as pd

def create_test_data(
	entity = ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
	group = ['W', 'X', 'Y', 'Z'],
	categorical = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple', 'Pink'],
	continuous = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
):
	ncombos = len(entity) * len(group) * len(categorical) * len(continuous)
	entity_X = []
	group_X = []
	categorical_X = []
	continuous_X = []

	for e in entity:
		for g in group:
			for cat in categorical:
				for cont in continuous:
					entity_X.append(e)
					group_X.append(g)
					categorical_X.append(cat)
					continuous_X.append(cont)

	df = pd.DataFrame({
		'Entity': entity_X,
		'Group': group_X,
		'Categorical': categorical_X,
		'Continuous': continuous_X,
	})

	assert df.shape[0] == ncombos

	return df


file_path = sys.path[-1] + '/main/nemesis/tests/test_data_X0.csv'
df0 = create_test_data()[['Entity', 'Group', 'Categorical', 'Continuous']]
df0.to_csv(file_path, index_label='Index')

c1 = df0.Group == 'X'
c2 = df0.Continuous == 1.0
df1 = df0.copy()
df1.loc[c1 & c2, 'Continuous'] = 0.0
file_path = sys.path[-1] + '/main/nemesis/tests/test_data_X1.csv'
df1.to_csv(file_path, index_label='Index')

c1 = df0.Group == 'X'
c2 = df0.Continuous > 0.5
df2 = df0.copy()
df2.loc[c1 & c2, 'Continuous'] = 0.0
file_path = sys.path[-1] + '/main/nemesis/tests/test_data_X2.csv'
df2.to_csv(file_path, index_label='Index')

c1 = df0.Group == 'X'
c2 = df0.Continuous > 0.5
df2 = df0.copy()
df2 = df2[~(c1 & c2)]
file_path = sys.path[-1] + '/main/nemesis/tests/test_data_X2.csv'
df2.to_csv(file_path, index_label='Index')
