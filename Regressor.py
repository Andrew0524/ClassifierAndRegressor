from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.linear_model import Lasso, Ridge, LinearRegression, Lars
from sklearn.ensemble import RandomForestRegressor
from scipy import stats
import statsmodels.api as sm
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sliced import SlicedInverseRegression
import ModelEvaluation as ME
import ModelSelection as MS

import sys
if 'C:\\Users\\randysuen\\pycodes\\Dimension-Reduction-Approaches' not in sys.path:
    sys.path.append('C:\\Users\\randysuen\\pycodes\\Dimension-Reduction-Approaches')

from DimensionReductionApproaches import CenteringDecorator, NormalizingDecorator

"""
Notice: I should add , PIRE(partial inverse regression), decision tree, ...regressions to this file.
"""

from abc import ABC, abstractmethod

# There should be stagewise and stepwise regressor.


class Regressor(ABC):
    def __init__(self):
        self.parameters = None
        self.regressor = None
        self.sse = None
        self.sst = None
        self.adjrsquared = None
        self.rsquared = None
        self.X_train = None
        self.Y_train = None
        self.n = None
        self.p = None

    @abstractmethod
    def _inference(self, X_train, Y_train):
        if type(X_train) == pd.DataFrame:
            X_train = X_train.values

        # Store some info of the model.
        self.sst = np.sum((Y_train-np.mean(Y_train, axis=0))**2, axis=0)
        self.n = X_train.shape[0]
        self.p = X_train.shape[1]
        self.rsquared = ME.ModelEvaluation.Rsquare(self)
        self.adjrsquared = ME.ModelEvaluation.AdjRsquare(self)

        if type(self.regressor) == Lasso:
            predictions = np.expand_dims(self.regressor.predict(X_train), 1)
            self.sse = np.sum((predictions - Y_train) ** 2, axis=0)
        else:
            self.sse = np.sum((self.regressor.predict(X_train) - Y_train) ** 2, axis=0)
        self.sse_scaled = self.sse / float(X_train.shape[0] - X_train.shape[1])

        if type(self.sse_scaled) == np.float64:
            self.sse_scaled = [self.sse_scaled]

        self.se = np.array([np.sqrt(np.diagonal(self.sse_scaled[i] * np.linalg.inv(np.dot(X_train.T, X_train))))
                            for i in range(len(self.sse_scaled))])

        self.t = self.regressor.coef_ / self.se
        self.p = 2 * (1 - stats.t.cdf(np.abs(self.t), X_train.shape[0] - X_train.shape[1]))

    @abstractmethod
    def Fit(self, X_train, Y_train):
        self.X_train = X_train
        self.Y_train = Y_train
        self.regressor.fit(X_train, Y_train)
        self._inference(X_train, Y_train)
        return self.regressor.intercept_, self.regressor.coef_, self.p, self.regressor.score(X_train, Y_train)

    @abstractmethod
    def Predict(self, X_test):
        prediction = self.regressor.predict(X_test)
        return prediction

    @abstractmethod
    def RegressionPlot(self, X, Y):
        scatter = plt.scatter(X, Y, color='b')
        line = plt.plot(X, self.regressor.predict(X), color='r')
        plt.ylabel('response')
        plt.xlabel('explanatory')
        plt.legend(handles=[scatter, line[0], ], labels=['Scatter Plot', 'Intercept:{}, Slope:{},\n R-square:{}'.format(self.regressor.intercept_,self.regressor.coef_,self.regressor.score(X,Y))],loc='best')
        plt.title('Scatter Plot and Regression')


class OrdianryLeastSquareRegressor(Regressor):
    def __init__(self):
        super().__init__()
        self.regressor = LinearRegression()


class PartialLeastSqaureRegressor(Regressor):
    def __init__(self, n_components):
        super().__init__()
        self.regressor = PLSRegression(n_components=n_components)

    def Fit(self, X_train, Y_train):
        self.regressor.fit(X_train, Y_train)
        self._inference(X_train, Y_train)
        
        return None, self.regressor.coef_, self.p, self.regressor.score(X_train, Y_train)


class LassoRegressor(Regressor):
    def __init__(self, alpha):
        super().__init__()
        self.regressor = Lasso(alpha)


# Still need to check this class.
class PrincipalComponentRegressor(Regressor):
    def __init__(self, n_components):
        super().__init__()
        self.n_components = n_components
        self.regressor = LinearRegression()
        self.pca = None
        self.X_train_transform = None

    def Fit(self, X_train, Y_train):
        self.pca = PCA(self.n_components)
        self.X_train_transform = self.pca.fit_transform(X_train)
        self.regressor.fit(self.X_train_transform, Y_train)
        self._inference(self.X_train_transform, Y_train)
        return self.regressor.intercept_, self.regressor.coef_, self.p, self.regressor.score(self.X_train_transform,
                                                                                             Y_train)

    def Predict(self, X_test):
        X_test_transform = self.pca.transform(X_test)
        prediction = self.regressor.Predict(X_test_transform)
        return prediction


class RidgeRegressor(Regressor):
    def __init__(self, alpha):
        super().__init__()
        self.regressor = Ridge(alpha)
        
        
class RandForestRegressor(Regressor):
    def __init__(self):
        super().__init__()
        self.regressor = RandomForestRegressor()
        
        
class SlicedInverseRegressor(Regressor):
    def __init__(self):
        super().__init__()
        self.regressor = SlicedInverseRegression()


class LeastAngleRegressor(Regressor):
    def __init__(self):
        super().__init__()
        self.regressor = Lars()


class ForwardStepwiseRegressor(Regressor):
    def __init__(self, criteria=ME.ModelEvaluation.AIC):
        super().__init__()
        self.regressor = LinearRegression()
        self.criteria = criteria
        self.selected_X_train = None

    def Fit(self, X_train, Y_train):
        self.X_train = X_train
        self.Y_train = Y_train
        ids = MS.ModelSelection.FowardSelection(model=self.regressor, X_train=X_train, Y_train=Y_train)
        self.selected_X_train = self.X_train[:, ids]
        self.regressor.fit(X_train, Y_train)
        self._inference(X_train, Y_train)
        return self.regressor.intercept_, self.regressor.coef_, self.p, self.regressor.score(X_train, Y_train)


class BackwardStepwiseRegressor(Regressor):
    def __init__(self, criteria=ME.ModelEvaluation.AIC):
        super().__init__()
        self.regressor = LinearRegression()
        self.criteria = criteria
        self.selected_X_train = None

    def Fit(self, X_train, Y_train):
        self.X_train = X_train
        self.Y_train = Y_train
        ids = MS.ModelSelection.BackwardSelection(model=self.regressor, X_train=X_train, Y_train=Y_train)
        self.selected_X_train = self.X_train[:, ids]
        self.regressor.fit(X_train, Y_train)
        self._inference(X_train, Y_train)
        return self.regressor.intercept_, self.regressor.coef_, self.p, self.regressor.score(X_train, Y_train)


# The response should be univariate.
class ForwardStagewiseRegressor(Regressor):
    def __init__(self):
        super().__init__()
        self.beta = None

    @NormalizingDecorator('X_train', 'Y_train')
    @CenteringDecorator('X_train', 'Y_train')
    def Fit(self, X_train, Y_train, **kwargs):
        eps = kwargs.get('eps', 0.01)
        k = kwargs.get('k', 100)
        lower_bound = kwargs.get('lower_bound', 0)
        self.X_train = X_train
        self.Y_train = Y_train
        self.n = X_train.shape[0]
        self.p = X_train.shape[1]
        assert k <= self.p
        residual = Y_train
        available_predictors = list(range(self.p))
        cors = np.zeros(shape=(self.p, ))
        beta = np.zeros(shape=(self.p, ))
        for i in range(k):
            for predictor in available_predictors:
                cors[predictor] = np.matmul(residual.T, X_train[:, predictor])
            abs_cors = [np.abs(cor) for cor in cors]
            index = np.argmax(abs_cors)
            if abs_cors[index] < lower_bound:
                break
            sign = np.sign(cors[index])
            beta[index] += sign * eps
            residual -= sign * eps * X_train[:, index]

            available_predictors.remove(index)
            cors[index] = 0
            abs_cors[index] = 0

        self.beta = beta