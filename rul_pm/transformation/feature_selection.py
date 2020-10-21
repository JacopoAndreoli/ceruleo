import numpy as np
from sklearn.base import TransformerMixin, BaseEstimator
import pandas as pd



class NullProportionSelector(BaseEstimator, TransformerMixin):
    def __init__(self, min_null_proportion=0.5):
        self.min_null_proportion = min_null_proportion

    def fit(self, X, y=None):        
        self.not_null_proportion = np.mean(np.isfinite(X), axis=0)
        self.mask = self.not_null_proportion > self.min_null_proportion
        return self

    def transform(self, X):
        return X[:, self.mask]

class ByNameFeatureSelector(BaseEstimator, TransformerMixin):
    def __init__(self, features=[]):
        self.features = features
        self.features_indices = None

    def fit(self, df, y=None):
        if len(self.features) > 0:
            features = list(set(df.columns).intersection(set(self.features)))
        else:
            features= list(set(df.columns))
        self.features_indices = [i for i, c in enumerate(df.columns) if c in features]
        return self

    def transform(self, X):
        return X.iloc[:, self.features_indices]

    @property
    def n_features(self):
        return len(self.features)


class DiscardByNameFeatureSelector(BaseEstimator, TransformerMixin):
    def __init__(self, features=[]):
        self.features = features
        self.features_indices = None

    def fit(self, df, y=None):
        features = list(set(df.columns).difference(set(self.features)))
        self.features_indices = [i for i, c in enumerate(df.columns) if c in features]
        return self

    def transform(self, X):
        return X.iloc[:, self.features_indices]

    @property
    def n_features(self):
        return len(self.features)