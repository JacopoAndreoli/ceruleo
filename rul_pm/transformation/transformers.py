import logging

import numpy as np
from rul_pm.transformation.feature_selection import (ByNameFeatureSelector,
                                                    DiscardByNameFeatureSelector,
                                                      NullProportionSelector)
from rul_pm.transformation.imputers import NaNRemovalImputer
from rul_pm.transformation.outliers import IQROutlierRemover
from rul_pm.transformation.utils import PandasToNumpy, TargetIdentity
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from sklearn.utils.validation import check_is_fitted
import copy 


logger = logging.getLogger(__name__)

RESAMPLER_STEP_NAME = 'resampler'


def simple_pipeline(features=[]):
    return Pipeline(steps=[
        ('initial_selection', ByNameFeatureSelector(features)),
        ('to_numpy', PandasToNumpy())
    ])


def transformation_pipeline(outlier=IQROutlierRemover(),
                            imputer=NaNRemovalImputer(),
                            scaler=RobustScaler(),
                            resampler=None,
                            features=None,
                            discard=None,
                            locater=None,
                            pandas_transformation=None):
    if features is not None and discard is not None:
        raise ValueError('Features and discard cannot be setted at the same time')
    selector = 'passthrough'
    if features is not None:
        selector = ByNameFeatureSelector(features)
    if discard is not None:
        selector = DiscardByNameFeatureSelector(discard)
    return Pipeline(steps=[
        ('initial_selection', selector),
        (RESAMPLER_STEP_NAME,
         resampler if resampler is not None else 'passthrough'),
        ('locater',  locater if locater is not None else 'passthrough'),
        ('pandas_transformation', pandas_transformation if pandas_transformation is not None else 'passthrough'),
        ('to_numpy', PandasToNumpy()),
        ('outlier_removal', outlier if outlier is not None else 'passthrough'),
        ('NullProportionSelector', NullProportionSelector()),
        ('selector', VarianceThreshold(0)),
        ('scaler', scaler if scaler is not None else 'passthrough'),
        ('imputer', imputer if imputer is not None else 'passthrough'),
    ])


def step_set_enable(transformer, step_name, enabled):
    if not (isinstance(transformer, Pipeline)):
        return
    for (name, step) in transformer.steps:
        if name == step_name and not isinstance(step, str) and step is not None:
            step.enabled = enabled


def transformer_info(transformer):
    if isinstance(transformer, Pipeline):
        return [(name, transformer_info(step))
                for name, step in transformer.steps]
    elif isinstance(transformer, TransformerMixin):
        return transformer.__dict__


class Transformer:
    """
    Transform each life

    Parameters
    ----------
    target_column : str
                    Column name with the target. Usually where the RUL resides         
    time_feature: str
                  Column name of the timestamp feature
    transformerX: TransformerMixin,
                  Transformer that will be applied to the life data
    transformerY: TransformerMixin default: TargetIdentity()
                  Transformer that will be applied to the target.
    disable_resampling_when_fitting: bool = True
                                     Wether to disable the resampling when the model is being fit.
                                     This can reduce the memory requirements when fitting
    """
    def __init__(self,
                 target_column: str,
                 transformerX: TransformerMixin,
                 time_feature: str = None,
                 transformerY: TransformerMixin = TargetIdentity(),
                 disable_resampling_when_fitting: bool = True):
        self.transformerX = transformerX
        self.transformerY = transformerY
        self.target_column = target_column
        self.features = None
        self.time_feature = time_feature
        self.disable_resampling_when_fitting = disable_resampling_when_fitting

    def _process_selected_features(self):
        if self.transformerX['selector'] is not None:
            selected_columns = (self.transformerX['selector'].get_support(
                indices=True))
            self.features = [self.features[i] for i in selected_columns]

    def clone(self):
        return copy.deepcopy(self)

    def fit(self, dataset, proportion=1.0):
        logger.info('Fitting Transformer')
        df = dataset.toPandas(proportion)
        self.fitX(df)
        self.fitY(df)

        X = self.transformerX.transform(df.head(n=2))
        self.number_of_features_ = X.shape[1]
        self.fitted_ = True
        return self

    def fitX(self, df):
        if self.disable_resampling_when_fitting:
            step_set_enable(self.transformerX, RESAMPLER_STEP_NAME, False)
        self.transformerX.fit(df)
        step_set_enable(self.transformerX, RESAMPLER_STEP_NAME, True)

    def _target(self, df):
        if self.time_feature is not None:
            if isinstance(self.target_column, list):
                select_features = [self.time_feature]  + self.target_column
            else:
                select_features = [self.time_feature,  self.target_column]
            return df[select_features]
        else:
            return df[self.target_column]


    def fitY(self, df):
        if self.disable_resampling_when_fitting:
            step_set_enable(self.transformerY, RESAMPLER_STEP_NAME, False)   
        self.transformerY.fit(self._target(df))
        step_set_enable(self.transformerY, RESAMPLER_STEP_NAME, True)

    def transform(self, df):
        check_is_fitted(self, 'fitted_')
        return (self.transformX(df), self.transformY(df))

    def transformY(self, df):
        return np.squeeze(
            self.transformerY.transform(self._target(df)))

    def transformX(self, df):
        return self.transformerX.transform(df)

    @property
    def n_features(self):
        return self.number_of_features_

    def description(self):
        return {
            'target_column': self.target_column,
            'features': self.features,
            'transformerX': transformer_info(self.transformerX),
            'transformerY': transformer_info(self.transformerY),
        }


class SimpleTransformer(Transformer):
    def __init__(self, target_column: str, time_feature: str=None):
        super().__init__(target_column, simple_pipeline(), transformerY=TargetIdentity(), time_feature=time_feature, disable_resampling_when_fitting=True)
                 