import pandas as pd
import numpy as np

dataframe = pd.read_csv("./tools/df_filtred.csv")
dataframe = dataframe.explode('text')
    
print(dataframe)