

import numpy as np
import pandas as pd
from infineonPM.transformation.generation import AlarmsAccumulated, SourceTime
from infineonPM.transformation.target import TargetToHours
from rul_pm.dataset.lives_dataset import AbstractLivesDataset
from rul_pm.models.sklearn import SKLearnModel
from rul_pm.transformation.features.generation import RollingStatistics
from rul_pm.transformation.features.scalers import PandasMinMaxScaler
from rul_pm.transformation.features.selection import (
    ByNameFeatureSelector, PandasNullProportionSelector,
    PandasVarianceThreshold)
from rul_pm.transformation.imputers import ForwardFillImputer
from rul_pm.transformation.target import PicewiseRULThreshold
from rul_pm.transformation.transformers import (LivesPipeline, Transformer,
                                                transformation_pipeline)
from rul_pm.transformation.utils import (PandasFeatureUnion,
                                         PandasTransformerWrapper)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet
from sklearn.preprocessing import MinMaxScaler


class MockDataset(AbstractLivesDataset):
    def __init__(self, nlives: int):

        self.lives = [
            pd.DataFrame({
                'feature1': np.linspace(0, 100, 50),
                'feature2': np.linspace(-25, 500, 50),
                'RUL': np.linspace(100, 0, 50)
            })
            for i in range(nlives-1)]

        self.lives.append(
            pd.DataFrame({
                'feature1': np.linspace(0, 100, 50),
                'feature2': np.linspace(-25, 500, 50),
                'feature3': np.linspace(-25, 500, 50),
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


class TestSKLearn():
    def test_sklearn(self):
        faetures = ['feature1', 'feature2']
        transformer = Transformer(
            'RUL',
            transformation_pipeline(
                numericals_pipeline=LivesPipeline(
                    steps=[
                        ('ss', ByNameFeatureSelector(faetures)),
                        ('scaler', PandasMinMaxScaler((-1, 1)))
                    ]),
                output_df=False)
        )

        ds = MockDataset(5)
        model = SKLearnModel(
            model=ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=100000),
            window=1,
            step=2,
            transformer=transformer,
            shuffle='all'
        )

        model.fit(ds)

        y_pred = model.predict(ds)
        y_true = model.true_values(ds)

        assert np.sum(y_pred - y_true) < 0.001