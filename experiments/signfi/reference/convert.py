from scipy.io import loadmat
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

data = loadmat('dataset_lab_276_dl.mat')

X = data['csid_lab']
y = data['label_lab']

# Select sample
sample_idx = 0
antenna_idx = 0

sample = X[sample_idx, :, antenna_idx, :]   # (30, 5520)

# 🔥 FIX: Convert complex → magnitude
sample = np.abs(sample)

# Plot heatmap
plt.figure(figsize=(12, 5))
sns.heatmap(sample, cmap='viridis')

plt.title("CSI Heatmap (Magnitude)")
plt.xlabel("Time")
plt.ylabel("Subcarriers")

plt.show()
