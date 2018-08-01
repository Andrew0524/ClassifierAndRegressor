import numpy as np
import pandas as pd
import sys
import warnings
import ModelEvaluation as ME
from itertools import combinations

if 'C:\\Users\\ASUS\\Dropbox\\pycode\\mine\\Dimension-Reduction-Approaches' not in sys.path:
    sys.path.append('C:\\Users\\ASUS\Dropbox\\pycode\\mine\\Dimension-Reduction-Approaches')
if 'C:\\Users\\randysuen\\pycodes\\Dimension-Reduction-Approaches' not in sys.path:
        sys.path.append('C:\\Users\\randysuen\\pycodes\\Dimension-Reduction-Approaches')
from DimensionReductionApproaches import CenteringDecorator, NormalizingDecorator


class VariableSelection:
    # Till now, Y_train should be a N*1 matrix.
    @CenteringDecorator('X_train', 'Y_train')
    def CorrSelection(X_train, Y_train, both_sides, num_each_side, abs=False, **kwargs):
        if Y_train.shape[1] > 1:
            warnings.warn('The dimension of the Y variable should be 1 now.')
        covariance = np.matmul(X_train.T, Y_train)/X_train.shape[0]
        X_std = np.expand_dims(np.std(X_train, axis=0), axis=1)
        Y_std = np.std(Y_train)
        corr = covariance/(X_std*Y_std)
        
        if abs is True:
            if num_each_side == 'full':
                num_each_side = X_train.shape[1]
            corr = np.abs(corr)
            sorted_index_all = np.argsort(corr.ravel())
            sorted_index_all = sorted_index_all[::-1]
            sorted_left = sorted_index_all[0:num_each_side]
            sorted_index = sorted_left
            if both_sides is True:
                warnings.warn('You should not have picked the both sides of the variable list.')
            return sorted_index, np.reshape(corr[sorted_index], newshape=(1, len(corr[sorted_index])))
        
        sorted_index_all = np.argsort(corr.ravel())
        sorted_index_all = sorted_index_all[::-1]
        
        if both_sides is True:
            # if fill, it will discard the weakest one
            if num_each_side == 'full':
                num_each_side = np.floor(X_train.shape[1]/2)
                
            index_left = sorted_index_all[0:num_each_side]
            index_right = sorted_index_all[-1:-1-num_each_side:-1]
            sorted_index = np.concatenate([index_left, index_right], axis=0)
        else:
            if num_each_side == 'full':
                num_each_side = X_train.shape[1]
                
            index_left = sorted_index_all[0:num_each_side]
            sorted_index = index_left
            
        return sorted_index, np.reshape(corr[sorted_index], newshape=(1, len(corr[sorted_index])))


class ModelSelection:

    def BestSubsetSelection(model, X_train, Y_train, criteria=ME.ModelEvaluation.AIC, **kwargs):
        warnings.warn('Please notice that when the number of predictors are too large, the'
                      'best subset selection would be quite time-consuming.')
        p = X_train.shape[1]
        candidates = list()
        predictors_candidates = list()
        predictors_id = list(range(p))
        for i in range(1, p):
            model_candidates = list()
            combs = list(combinations(predictors_id, i))
            for comb in combs:
                model_comb = model()
                model_comb.Fit(X_train=X_train[:, comb], Y_train=Y_train)
                model_candidates.append((model_comb, comb))

            rsquareds = [model.rsquared for model, _ in model_candidates]
            predictors_id = [identity for _, identity in model_candidates]

            index = np.argmax(rsquareds)

            predictor_id = predictors_id[index]
            model = model_candidates[index]

            candidates.append(model)
            predictors_candidates.append(predictor_id)

        if criteria is ME.ModelEvaluation.Rsquared or criteria is ME.ModelEvaluation.AdjRsquared:
            numbers = [criteria(model) for model in candidates]
            index = np.argmax(numbers)
        elif criteria is ME.ModelEvaluation.AIC or criteria is ME.ModelEvaluation.BIC or criteria is ME.ModelEvaluation.MallowCp:
            model_full = model()
            model_full.Fit(X_train=X_train, Y_train=Y_train)
            var = model_full.sse / model_full.n
            numbers = [list(criteria(model, var=var))[0] for model in candidates]
            index = np.argmin(numbers)
        else:
            raise TypeError('Please handle the special criteria.')
        return predictors_candidates[index]

    # This function would return a list of indices indicating which predictors we should select.
    def FowardSelection(model, X_train, Y_train, criteria=ME.ModelEvaluation.AIC, **kwargs):
        p = X_train.shape[1]
        candidates = list()
        predictors_order = list()
        available_predictors = list(range(p))
        for i in range(p):
            model_candidates = list()
            for j in available_predictors:
                add_model = model()
                try:
                    add_predictors = np.concatenate((predictors, X_train[:, j]), axis=1)
                except UnboundLocalError:
                    add_predictors = X_train[:, j]
                add_model.Fit(X_train=add_predictors, Y_train=Y_train)
                model_candidates.append((add_model, j))

            rsquareds = [model.rsquared for model, _ in model_candidates]
            predictors_id = [identity for _, identity in model_candidates]

            index = np.argmax(rsquareds)

            predictor_id = predictors_id[index]
            model = model_candidates[index]

            available_predictors.remove(predictor_id)

            candidates.append(model)
            predictors_order.append(predictor_id)

            predictors = model.X_train

        if criteria is ME.ModelEvaluation.Rsquared or criteria is ME.ModelEvaluation.AdjRsquared:
            numbers = [criteria(model) for model in candidates]
            index = np.argmax(numbers)
        elif criteria is ME.ModelEvaluation.AIC or criteria is ME.ModelEvaluation.BIC or \
                criteria is ME.ModelEvaluation.MallowCp:

            model_full = model()
            model_full.Fit(X_train=X_train, Y_train=Y_train)
            var = model_full.sse / model_full.n
            numbers = [list(criteria(model, var=var))[0] for model in candidates]
            index = np.argmin(numbers)
        else:
            raise TypeError('Please handle the special criteria.')

        return predictors_order[:index+1]

    def BackwardSelection(model, X_train, Y_train, criteria=ME.ModelEvaluation.AIC, **kwargs):
        if X_train.shape[1] > X_train.shape[0]:
            raise ValueError('The number of predictors should not be larger the one of the sample size.')
        p = X_train.shape[1]
        candidates = list()
        predictors_order = list()
        available_predictors = list(range(p))

        model_full = model()
        model_full.Fit(X_train=X_train, Y_train=Y_train)
        candidates.append(model_full)
        for i in range(p):
            model_candidates = list()
            predictors = candidates[-1].X_train
            for j in available_predictors:
                sub_model = model()
                sub_predictors = np.delete(predictors, j, axis=1)
                sub_model.Fit(X_train=sub_predictors, Y_train=Y_train)
                model_candidates.append((sub_model, j))

            rsquareds = [model.rsquared for model, _ in model_candidates]
            predictors_id = [identity for _, identity in model_candidates]

            index = np.argmax(rsquareds)

            predictor_id = predictors_id[index]
            model = model_candidates[index]

            available_predictors.remove(predictor_id)

            candidates.append(model)
            predictors_order.append(predictor_id)

        if criteria is ME.ModelEvaluation.Rsquared or criteria is ME.ModelEvaluation.AdjRsquared:
            numbers = [criteria(model) for model in candidates]
            index = np.argmax(numbers)
        elif criteria is ME.ModelEvaluation.AIC or criteria is ME.ModelEvaluation.BIC or \
                criteria is ME.ModelEvaluation.MallowCp:
            model_full = model()
            model_full.Fit(X_train=X_train, Y_train=Y_train)
            var = model_full.sse / model_full.n
            numbers = [list(criteria(model, var=var))[0] for model in candidates]
            index = np.argmin(numbers)
        else:
            raise TypeError('Please handle the special criteria.')

        predictors = list(range(p))
        to_remove = predictors_order[:index+1]
        for predictor in to_remove:
            predictors.remove(predictor)

        return predictors
