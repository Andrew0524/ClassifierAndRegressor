import sys
if 'C:\\Users\\ASUS\Dropbox\\pycode\\mine\\Dimension-Reduction-Approaches' not in sys.path :
    sys.path.append('C:\\Users\\ASUS\Dropbox\\pycode\\mine\\Dimension-Reduction-Approaches')
import UtilFun as UF
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

import DimensionReductionApproaches as DRA


# This decorator would identify the classifier. This should decorate the Fit function of the 
# Classifier. 
def ClassifierDecorator():
    def decofun():
        
        return None
    
    return decofun
    

class Classifier():
    def __init__(self,classify_function,**kwargs):
        self.parameters = None
        self.transformed_X_train = None
        self.Y_train = None
        self.kwargs = dict()
        self.classify_function = classify_function
        
    
    def Fit(self,X_train,Y_train):
        if self.claasify_function == KNeighborsClassifier :
            self.classifier = self.classify_function(self.kwargs.get('k',5))
        elif self.classify_function == SVC :
            self.classifier = self.classify_function()
        self.classifier.fit(X_train,Y_train)
        
    def Classify(self,X_test,Y_test):
        results = self.classifier.predict(X_test)
        correct_results = np.where(results == Y_test.ravel())[0]
        return len(correct_results) / len(Y_test), correct_results
    
class LinearDiscriminantClassifier(Classifier):
    
    def __init__(self,discriminant_function,classify_function,**kwargs):
        super().__init__()
        self.discriminant_function = discriminant_function
        self.classify_function = classify_function
        self.kwargs = kwargs
    
    
    def Fit(self,X_train,Y_train):
        self.parameters = self.discriminant_function(X_train=X_train,Y_train=Y_train,kwargs=self.kwargs)
        X_train_proj = np.matmul(X_train,self.parameters)
        if self.claasify_function == KNeighborsClassifier :
            self.classifier = self.classify_function(self.kwargs.get('k',5))
        elif self.classify_function == SVC :
            self.classifier = self.classify_function()
        self.classifier.fit(X_train_proj,Y_train.ravel())
        return self.parameters
    
    def Classify(self,X_test,Y_test):
        X_test_proj = np.matmul(X_test,self.parameters)
        # Use K-nearest neighbor to classify the testing data
        results = self.classifier.predict(X_test_proj)
        correct_results = np.where(results == Y_test.ravel())[0]
        return len(correct_results) / len(Y_test), correct_results
        
class TwoStepClassifier(Classifier):
    
    def __init__(self,first_step_function,second_step_function,classify_function,**kwargs):
        super().__init__()
        self.first_step_function = first_step_function
        self.second_step_function = second_step_function
        self.classify_function = classify_function
        self.parameters = dict()
        
    
    def Fit(self,X_train,Y_train,**kwargs):

        self.input_shape = (X_train.shape[1],X_train.shape[2],X_train.shape[3])
        dimension = self._Search_Dimensionality(X_train = X_train,
                                                Y_train = Y_train)
        linear_subspace = self.first_step_function(X_train = X_train,
                                                   Y_train = Y_train,
                                                   p_tilde = dimension,
                                                   q_tilde = dimension)
        
        self.parameters['first_step']['row'] = linear_subspace[0]
        self.parameters['first_step']['column'] = linear_subspace[1]
        
        X_train_proj = DRA.MultilinearReduction.TensorProject(X_train,self.parameters['first_step']['row'],self.parameters['first_step']['column'])
        X_train_proj_vec = UF.imgs2vectors(X_train_proj)
        
        self.parameters['second_step'] = self.second_step_function(X_train=X_train,Y_train=Y_train)
        
        self.transformed_X_train = np.matmul(X_train_proj_vec,self.parameters['second_step'])
        self.Y_train = Y_train
        return self.parameters
    
    def _Search_Dimensionality(self,X_train,Y_train,p_tilde,q_tilde,dimension=50):
        
        
        ratios = []
        for iter in range(dimension):
            linear_subspace = self.first_step_function(X_train = X_train,input_shape = self.input_shape,p_tilde=iter+1,q_tilde=iter+1)
            X_train_proj = np.matmul(np.matmul(linear_subspace[0],X_train),linear_subspace[1])
            X_train_proj_vec = UF.imgs2vectors(X_train_proj)
            linear_subspace = self.second_step_function(X_train_proj,Y_train)
            X_train_proj_vec_proj = np.matmul(X_train_proj_vec,linear_subspace)
            ratio = self.Compute_Ratio(X_train_proj_vec_proj,Y_train)
            ratios.append(ratio)
        
        ratios = np.round(ratios,6)
        index = np.argmax(ratios)
        
        return index + 1
    
    
    def Classify(self,X_test,Y_test,**kwargs):
        k = kwargs.get('k',1)
        # Use K-nearest neighbor to classify the testing data
        neighbor = KNeighborsClassifier(n_neighbors=k)
        neighbor.fit(self.transformed_X_train,self.Y_train.ravel())
        
        X_test_proj = DRA.MultilinearReduction.TensorProject(X_test,self.parameters['first_step']['row'],self.parameters['first_step']['column'])
        X_test_proj_vec = UF.imgs2vectors(X_test_proj)
        X_test_proj_vec_proj = np.matmul(X_test_proj_vec,self.parameters['second_step'])
        results = neighbor.predict(X_test_proj_vec_proj)
        correct_results = np.where(results == Y_test.ravel())[0]
        return len(correct_results) / len(Y_test), correct_results

    def Compute_Ratio(self,X_train,Y_train):
        Total_centered = DRA.TotalCentered(X_train)
        Between_centered = DRA.BetweenGroupMeanCentered(X_train,Y_train)
        _, S, _ = np.linalg.svd(Total_centered,full_matrices=False)
        denominator = np.sum(S)
        _, S, _ = np.linalg.svd(Between_centered,full_matrices=False)
        numerator = np.sum(S)
        return numerator/denominator
    