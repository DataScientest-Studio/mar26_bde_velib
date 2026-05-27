import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor

from joblib import dump


ts = (pd.Timestamp(1779453961, unit='s')).date()
print(ts)  # Returns a datetime.date object