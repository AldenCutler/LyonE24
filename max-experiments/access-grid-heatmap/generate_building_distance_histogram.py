import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the CSV file
file_path = 'out/building_distances_greater_lyon_region_all_buildings.csv'
data = pd.read_csv(file_path)

# Extract the 'distance' column
distances = data['distance']

# Create a histogram of the distances with a logarithmic scale on the y-axis
plt.figure(figsize=(10, 6))
plt.hist(distances, bins=50, edgecolor='black')
plt.yscale('log')
plt.title('Building Distances from the Closest Transit Station (Lyon Metropolis)')
plt.xlabel('Distance (meters)')
plt.ylabel('Number of Buildings (Log Scale)')
#plt.grid(True, which="both", ls="--")
plt.show()
