"""
Target Problem:
---------------
* To train a model to predict the brain connectivity for the next time point given the brain connectivity at current time point.
Proposed Solution (Machine Learning Pipeline):
----------------------------------------------
* Preprocessing Method (if any) -> Dimensionality Reduction method (if any) -> Learner
Input to Proposed Solution:
---------------------------
* Directories of training and testing data in csv file format
* These two types of data should be stored in n x m pattern in csv file format.
  Typical Example:
  ----------------
  n x m samples in training csv file (Explain n and m) 
  k x s samples in testing csv file (Explain k and s

Output of Proposed Solution:
----------------------------
* Predictions generated by learning model for testing set
* They are stored in "results_team11.csv" file. (Change the name file if needed)
Code Owner:
-----------
* Copyright © Team 15. All rights reserved.
* Copyright © Istanbul Technical University, Learning From Data Spring/Fall 2020. All rights reserved. 
"""

import numpy as np
import pandas as pd
import random as r
from sklearn.metrics import mean_squared_error as mse
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy.stats.stats import pearsonr
from sklearn.ensemble import VotingRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.multioutput import MultiOutputRegressor
from sklearn.linear_model import BayesianRidge
from sklearn.ensemble import AdaBoostRegressor
import random as r
r.seed(1)
np.random.seed(1)
import warnings
warnings.filterwarnings('ignore')


def load_data(csv):

    """
    The method reads train and test data from their dataset files.
    Then, it splits train data into features and labels.
    Parameters
    ----------
    train_file: directory of the file in which train data set is located
    test_file: directory of the file in which test data set is located
    """
    df = pd.read_csv(csv).iloc[:, 1:]
    return df


def preprocessing(train_t0, test_t0):

    """
    Drops duplicates from given datasets
    Parameters
    ----------
    train_t0: X data -> train
    test_t0: X data -> test
    """
    train_t0_T = train_t0.T
    train_t0 = train_t0_T.drop_duplicates(keep='first').T

    test_t0_T = test_t0.T
    test_t0 = test_t0_T.drop_duplicates(keep='first').T


def cv5(X, y):

    """
    Applies 5 fold cross validation
    Parameters
    ----------
    X: X data -> train
    y: Y data -> train
    """
    predictions = []
    mse = []
    mae = []
    pear = []
    kf = KFold(n_splits=5, shuffle = True ,random_state=1)
    for train_index, test_index in kf.split(X):

        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        
        X_train = X_train.T
        X_train = X_train.drop_duplicates(keep='first').T
        
        X_test = X_test.T
        X_test = X_test.drop_duplicates(keep='first').T
        
        model = MultiOutputRegressor(VotingRegressor(estimators=[("knn", KNeighborsRegressor(n_neighbors=25, weights='distance', p=1)), ("adab",AdaBoostRegressor(random_state=0, loss='exponential', learning_rate= 0.1)), ("bayesianridge", BayesianRidge())], n_jobs=-1))
        model.fit(X_train, y_train)
        
        prediction = model.predict(X_test)
        
        mse.append(mean_squared_error(prediction, y_test))
        mae.append(mean_absolute_error(prediction, y_test))
        pear.append(pearsonr(prediction.flatten(), y_test.values.flatten())[0])
                        
        for i in range(prediction.shape[0]):
            print(mean_absolute_error(prediction[i,:], y_test.values[i,:] ))
        print("----")
        for i in range(prediction.shape[0]):
            print(pearsonr(prediction[i,:], y_test.values[i,:])[0])
        print("----")
        
    print("mses: ", mse)
    print("maes: ", mae)
    print("pears", pear)
    
    print("mse", np.mean(mse))
    print("mae", np.mean(mae))
    print("pear", np.mean(pear))

    print("std mse", np.std(mse))
    print("std mae", np.std(mae))
    print("std pear", np.std(pear))    

def train_model(train_t0, train_t1):
    
    """
    The method creates a learning model and trains it by using training data.
    Parameters
    ----------
    train_t0: x
    train_t1: y
    """
    model = MultiOutputRegressor(VotingRegressor(estimators=[("knn", KNeighborsRegressor(n_neighbors=25, weights='distance', p=1)), ("adab",AdaBoostRegressor(random_state=0, loss='exponential', learning_rate= 0.1)), ("bayesianridge", BayesianRidge())], n_jobs=-1))
    model.fit(train_t0, train_t1)
    return model

def predict(X, model):


    """
    The method predicts for testing data samples by using trained learning model.
    Parameters
    ----------
    x_tst: features of testing data
    model: trained learning model
    """
    return model.predict(X)

def write_output(filename, predictions):

    """
    Writes predictions as desired in the submission process
    Parameters
    ----------
    filename: file path for saving file
    predictions: model outputs
    """
    predictions = predictions.flatten()
    np.savetxt(filename+".csv", np.dstack((np.arange(1, predictions.size+1) - 1, predictions))[0], "%d,%f", header="ID, predicted")

train_t0 = load_data("train_t0.csv")
train_t1 = load_data("train_t1.csv")
test_t0 = load_data("test_t0.csv")

model = train_model(train_t0, train_t1)
predictions = predict(test_t0, model)
write_output("results_team15", predictions)

###### CALCULATE 5-F CV ######
train_t0 = load_data("train_t0.csv")
train_t1 = load_data("train_t1.csv")
test_t0 = load_data("test_t0.csv")
cv5(train_t0, train_t1)
