import json

filepath = 'd:/WIFI-HAR/csi_fall_detection_3class_temporal_full.ipynb'

with open(filepath, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the index of the cell that prints X.shape
insert_idx = -1
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'print("X shape:", X.shape)' in source:
            insert_idx = i + 1
            break

# Define the new markdown and code cells for EDA
eda_markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## Exploratory Data Analysis (EDA)\n",
        "Visualizing class distributions and the temporal CSI amplitude signatures (Heatmaps) for each class."
    ]
}

eda_code = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "plt.figure(figsize=(8, 5))\n",
        "sns.countplot(x=y, palette='viridis')\n",
        "plt.title('Class Distribution (0: Falling, 1: Empty, 2: Small Activity)')\n",
        "plt.xlabel('Class Label')\n",
        "plt.ylabel('Count')\n",
        "plt.show()\n",
        "\n",
        "# Plot temporal heatmap of a sample window from each class\n",
        "class_names = {0: \"Falling\", 1: \"Empty\", 2: \"Small Activity\"}\n",
        "\n",
        "fig, axes = plt.subplots(1, 3, figsize=(18, 5))\n",
        "\n",
        "for i, class_label in enumerate([0, 1, 2]):\n",
        "    # Find first sample of this class\n",
        "    idx = np.where(y == class_label)[0]\n",
        "    if len(idx) > 0:\n",
        "        sample_idx = idx[0]\n",
        "        sample_window = X[sample_idx] # Shape (15, 128)\n",
        "        \n",
        "        sns.heatmap(sample_window, ax=axes[i], cmap='viridis', cbar=True)\n",
        "        axes[i].set_title(f'Temporal CSI Heatmap: {class_names[class_label]}')\n",
        "        axes[i].set_xlabel('Subcarrier Index')\n",
        "        axes[i].set_ylabel('Time Step (packet)')\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n"
    ]
}

if insert_idx != -1:
    nb['cells'].insert(insert_idx, eda_markdown)
    nb['cells'].insert(insert_idx + 1, eda_code)

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("EDA cells inserted.")
