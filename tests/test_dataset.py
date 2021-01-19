

import numpy as np
import pandas as pd
from rul_pm.dataset.lives_dataset import AbstractLivesDataset, FoldedDataset


class MockDataset(AbstractLivesDataset):
    def __init__(self, nlives: int):

        self.lives = [
            pd.DataFrame({
                'feature1': np.linspace(0, (i+1)*100, 50),
                'feature2': np.linspace(-25, (i+1)*500, 50),
                'RUL': np.linspace(100, 0, 50)
            })
            for i in range(nlives-1)]

        self.lives.append(
            pd.DataFrame({
                'feature1': np.linspace(0, 5*100, 50),
                'feature2': np.linspace(-25, 5*500, 50),
                'feature3': np.linspace(-25, 5*500, 50),
                'RUL': np.linspace(100, 0, 50)
            })
        )

    def get_life(self, i: int):
        return self.lives[i]

    @property
    def rul_column(self):
        return 'RUL'

    @property
    def nlives(self):
        return len(self.lives)


class TestDataset():
    def test_dataset(self):
        ds = MockDataset(5)
        columns = [set(['feature1', 'feature2', 'RUL', 'life'])
                   for i in range(4)]
        columns.append(
            set(['feature1', 'feature2', 'feature3', 'RUL', 'life']))
        for life, columns in zip(ds, columns):
            assert set(life.columns) == columns
        assert ds.nlives == 5

        p = ds.toPandas()
        assert p.shape[0] == 50*5
        assert set(ds.commonFeatures()) == set(
            ['feature1', 'feature2', 'RUL', 'life'])

        folded = ds[[3, 2, 1]]
        assert isinstance(folded, FoldedDataset)
        assert folded[0][['feature1',
                          'feature2']].equals(ds[3][['feature1', 'feature2']])
        assert not folded[1][['feature1',
                              'feature2']].equals(ds[3][['feature1', 'feature2']])
