import nbformat

notebook_path = 'c:/ADHIKKESH/FYP/ImagePi/ImagePi_Model_Kaggle_Notebook.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

new_cell_1 = nbformat.v4.new_code_cell(source="!pip install pyts")
new_cell_2 = nbformat.v4.new_code_cell(source='''from pyts.image import MarkovTransitionField
import matplotlib.pyplot as plt
import numpy as np

def generate_mtf_heatmap(time_series_data, image_size=50):
    """
    Converts 1D CSI amplitude sequence into a 2D Markov Transition Field (MTF) heat map.
    """
    # MTF expects 2D array of shape (n_samples, n_timestamps)
    # If time_series_data is 1D, we reshape to (1, -1)
    ts = np.array(time_series_data).reshape(1, -1)
    
    # Initialize MTF
    mtf = MarkovTransitionField(image_size=image_size)
    
    # Transform
    X_mtf = mtf.fit_transform(ts)
    
    return X_mtf[0]

# --- Example usage (assuming amplitude_csi is available from previous cells) ---
# csi_mtf_image = generate_mtf_heatmap(amplitude_csi)
# 
# plt.figure(figsize=(8, 8))
# plt.imshow(csi_mtf_image, cmap='jet', origin='lower')
# plt.title('CSI Markov Transition Field (MTF) Heat Map')
# plt.colorbar(label='Transition Probability')
# plt.tight_layout()
# plt.show()
''')

nb.cells.extend([new_cell_1, new_cell_2])

with open(notebook_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("MTF cells successfully appended to the notebook.")
