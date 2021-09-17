"""
Target Problem:
---------------
* Predict the evolution of brain connectivity over time.

Proposed Solution (Machine Learning Pipeline):
----------------------------------------------
* Eliminate Correlated Features -> Backward Elimination -> Decision Tree Regressor

Input to Proposed Solution:
---------------------------
* Directories of training data and labels(measurements at two different timepoints), and testing data in csv file format.
* These data should be stored in n x m pattern in csv file format.

  Typical Example:
  ----------------
  n x m samples in train_t0 csv file (n number of samples, m number of features)
  n x m samples in train_t1 csv file (n number of samples, m number of features)
  k x m samples in test_t0 csv file (k number of samples, m number of features)

* These data set files are ready by load_data() function.

Output of Proposed Solution:
----------------------------
* Predictions generated by learning model for testing set
* They are stored in "submission.csv" file.

Code Owner:
-----------
* Copyright © Team 17. All rights reserved.
* Copyright © Istanbul Technical University, Learning From Data Fall 2021. All rights reserved.
"""


import csv
import numpy as np
import pandas as pd
import random as r
import statsmodels.api as SMM
from sklearn import svm
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import mean_absolute_error as mae
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings("ignore")

np.random.seed(1)
r.seed(1)

def load_data(train_file, test_file):

    """
    The method reads train and test data from their dataset files.
    Then, it splits train data into features and labels.
    Parameters
    ----------
    train_file: directory of the file in which train data set is located
    test_file: directory of the file in which test data set is located
    """

    x_tra = pd.read_csv(train_file[0]).drop(columns=["ID"])
    y_tra = pd.read_csv(train_file[1]).drop(columns=["ID"])
    x_tst = pd.read_csv(test_file).drop(columns=["ID"])
    return x_tra, y_tra, x_tst

def error_func(actual, predicted):
    actual = actual.to_numpy().flatten() #melt t1 dataset (ground truth)
    predicted = predicted.flatten() #melt your prediction
    return mse(predicted,actual) #returns mse result for two melted matrices


def preprocessing(x_tra, y_tra, x_tst):

    """
    * First, this method calculates correlation values and eliminates highly correlated
    features.
    * Next, it performs backwards elimination to eliminate unnecessary features using
    a linear regressor.
    * Finally, it determines and removes outliers by testing each training sample
    using a leave-one-out method and checking their error rates.
    ----------
    x_tra: features of training data
    y_tra: labels of training data
    x_tst: features of test data
    """
    
    t1_temp = y_tra #to keep all t1 values
    corr = x_tra.corr() 

    # pairwise correlation 
    columns = np.full((corr.shape[0],), True, dtype=bool)
    for i in range(corr.shape[0]):
        for j in range(i+1, corr.shape[0]):
            # remove one of the (corr >= 0.9) pairs
            if corr.iloc[i,j] >= 0.9: 
                if columns[j]:
                    columns[j] = False
                    
    # new columns                
    selected_columns = x_tra.columns[columns]
    t0 = x_tra[selected_columns]
    t1_temp = t1_temp[selected_columns]
    columns = selected_columns[0:].values

    x = t0.iloc[:, 0:].values
    y = t1_temp.iloc[:, 0:].values

    numVars = len(x[0])
    for i in range(0, numVars):
        Y_temp = y[:,i]
        x_temp = x[:,i]
        regressor = SMM.OLS(Y_temp, x_temp).fit()
        maxVar = max(regressor.pvalues).astype(float)
        if maxVar > 0.05:
            for j in range(0, numVars - i):
                if (regressor.pvalues[j].astype(float) == maxVar):
                    x_temp = np.delete(x_temp, j, 1)
                    x = np.delete(x_temp, j, 1)
                    columns = np.delete(columns, j)                
    x_tra = pd.DataFrame(data = x, columns = selected_columns)
    x_tst = pd.DataFrame(data = x_tst, columns = selected_columns)
    
    error_samples = []
    cv_index = 0

    kf = KFold(n_splits=x_tra.shape[0], random_state=r.seed(1), shuffle=False)
    split_indices = kf.split(range(x_tra.shape[0]))

    for train_indices, test_indices in split_indices:
        x_train, y_train = x_tra.iloc[train_indices], y_tra.iloc[train_indices]
        x_test, y_test = x_tra.iloc[test_indices], y_tra.iloc[test_indices]
        model = train_model(x_train, y_train)
        y_pred = predict(x_test, model)
        error = error_func(y_test, y_pred)
        if error>0.006:
            print("CV Fold {}: MSE => {:.5f}%".format(cv_index, error))
            error_samples.append(cv_index)
        cv_index += 1
    
    order = error_samples
    x_tra = x_tra.reset_index().drop("index", axis=1)
    y_tra = y_tra.reset_index().drop("index", axis=1)
    x_tra = pd.DataFrame(x_tra)
    x_tra = pd.DataFrame(x_tra.drop(order).values)
    y_tra = pd.DataFrame(y_tra)
    y_tra = pd.DataFrame(y_tra.drop(order).values)
    return x_tra, y_tra, x_tst

def train_model(x_tra, y_tra):

    """
    The method creates a learning model and trains it by using training data.
    Parameters
    ----------
    x_tra: features of training data
    y_tra: labels of training data
    """

    alphas = 10**np.linspace(10,-2,100)*0.5
    dt = RidgeCV(alphas = alphas, scoring = 'neg_mean_squared_error', normalize = True)
    dt.fit(x_tra, y_tra)
    return dt

def predict(x_tst, model):

    """
    The method predicts labels for testing data samples by using trained learning model.
    Parameters
    ----------
    x_tst: features of testing data
    model: trained learning model
    """
    return model.predict(x_tst)

def cross_validation(x_tra, y_tra):

    """
    The method performs 5-fold cross-validation on training data and returns the error rates.
    Parameters
    ----------
    x_tra: features of training data
    y_tra: labels of training data
    """

    errors = []
    maes = []
    pcc = []
    X = x_tra
    Y = y_tra
    cv_index = 1

    kf = KFold(n_splits=5, random_state=1, shuffle=True)
    split_indices = kf.split(range(X.shape[0]))

    for train_indices, test_indices in split_indices:
        x_train, y_train = X.iloc[train_indices], Y.iloc[train_indices]
        x_test, y_test = X.iloc[test_indices], Y.iloc[test_indices]
        x_train, y_train, x_test = preprocessing(x_train, y_train, x_test)
        model = train_model(x_train, y_train)
        y_pred = predict(x_test, model)
        error = error_func(y_test, y_pred)
        errors.append(error)
        maes.append(mae(y_pred, y_test.to_numpy()))
        pcc.append(pearsonr(y_pred.flatten(), y_test.to_numpy().flatten())[0])
        cv_index += 1
    print(errors)
    print(sum(errors)/5)
    print(maes)
    print(sum(maes)/5)
    print(pcc)
    print(sum(pcc)/5)
    return errors

def write_output(filename, predictions):
    
    """
    Writes the outputted predictions to a file.
    Parameters
    ----------
    filename: file path for saving file
    predictions: pandas.dataframe object containing predictions
    """

    meltedDF = predictions.flatten()
    kaglexd = pd.DataFrame(meltedDF)
    kaglexd_melted = kaglexd.melt()
    kaglexd_melted.drop('variable', inplace=True, axis=1)

    kaglexd_melted = kaglexd_melted.rename(columns={'value': 'predicted'})
    kaglexd_melted.index.name = 'ID'

    kaglexd_melted.to_csv(filename)

# ********** MAIN PROGRAM ********** #


train_file, test_file = ["train_t0.csv", "train_t1.csv"], "test_t0.csv"
x_tra, y_tra, x_tst = load_data(train_file, test_file)

cross_validation(x_tra, y_tra)

x_tra, y_tra, x_tst = preprocessing(x_tra, y_tra, x_tst)
model = train_model(x_tra, y_tra)
predictions = predict(x_tst, model)
write_output("submission.csv", predictions)