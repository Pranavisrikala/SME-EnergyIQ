import pandas as pd

# Load our factory dataset
data = pd.read_csv("data/factory_data.csv")

print("Dataset loaded successfully!")
print()

print("Shape of dataset:")
print(data.shape)

print()

print("Column names:")
print(data.columns.tolist())

print()

print("First 5 rows:")
print(data.head())

print()

print("Basic statistics:")
print(data.describe())