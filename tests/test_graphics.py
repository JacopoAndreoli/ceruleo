from rul_pm.graphics.plots import boxplot_errors_wrt_RUL, plot_predictions
from rul_pm.results.results import PredictionResult
import numpy as np

def create_predictions(name:str, number_of_lives: int) -> PredictionResult:
    y_trues = []
    y_preds = []
    for i in range(number_of_lives):
        N = np.random.randint(1500) + 200
        y_true = np.linspace(500, 0, N)
        s = np.random.rand() * 500
        y_pred = y_true + np.random.randn(N)*s
        y_trues.append(y_true)
        y_preds.append(y_pred)

    y_true = np.hstack((*y_trues,))
    y_pred = np.hstack((*y_preds,))
    return  PredictionResult(name, y_true, y_pred)

class TestGraphics:
    def test_1(self):
        y_true = np.linspace(500, 0, num=500)
        y_pred = y_true + np.random.rand(500)*15
        r = PredictionResult('Example', y_true, y_pred)
        fig, ax = plot_predictions(r, ncols=1)
        assert ax.shape == (1, 1)

        y_true = np.hstack((y_true, y_true))
        y_pred = np.hstack((y_pred, y_pred))
        r = PredictionResult('Example', y_true, y_pred)
        fig, ax = plot_predictions(r, ncols=2)
        assert ax.shape == (1, 2)
        
        y_true = np.linspace(500, 0, num=500)
        y_pred = y_true + np.random.rand(500)*15
        y_true = np.hstack((y_true, y_true))
        y_pred = np.hstack((y_pred, y_pred))
        r = PredictionResult('Example', y_true, y_pred)
        fig, ax = plot_predictions(r, ncols=1)
        assert ax.shape == (2, 1)

    def test_boxplot(self):
        results = {
            'Model A': [
                create_predictions('Model A', 5),
                create_predictions('Model A', 5)
            ],
            'Model B': [
                create_predictions('Model B', 5),
                create_predictions('Model B', 8)
            ]
        }

        fig, ax = boxplot_errors_wrt_RUL(results, nbins=5)
        assert fig is not None

        results = { 'Model A':[
                create_predictions('Model A', 5),
            ]

        }
        fig, ax = boxplot_errors_wrt_RUL(results, nbins=5)

    