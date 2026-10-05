import json

filepath = 'd:/WIFI-HAR/csi_fall_detection_3class_temporal_full.ipynb'

with open(filepath, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the index of the existing EDA cell
insert_idx = -1
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'Temporal CSI Heatmap:' in source:
            insert_idx = i + 1
            break

if insert_idx == -1:
    insert_idx = len(nb['cells'])

new_eda_code_1 = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "import pandas as pd\n",
        "import numpy as np\n",
        "import os, glob\n",
        "import matplotlib.pyplot as plt\n",
        "from sklearn.metrics.pairwise import cosine_similarity\n",
        "\n",
        "# 1. Amplitude and Subcarrier index for all classes\n",
        "plt.figure(figsize=(10, 5))\n",
        "for class_label in [0, 1, 2]:\n",
        "    idx = np.where(y == class_label)[0]\n",
        "    if len(idx) > 0:\n",
        "        # Take the mean amplitude across the window for the first sample\n",
        "        sample_amp = np.mean(X[idx[0]], axis=0)\n",
        "        plt.plot(sample_amp, label=class_names[class_label])\n",
        "plt.title('Amplitude vs Subcarrier Index (Sample)')\n",
        "plt.xlabel('Subcarrier Index')\n",
        "plt.ylabel('Amplitude')\n",
        "plt.legend()\n",
        "plt.show()\n",
        "\n",
        "# 2. Phase and Subcarrier index for all classes\n",
        "def extract_phase(csi_str):\n",
        "    clean_str = csi_str.replace('[','').replace(']','').strip()\n",
        "    clean_str = ' '.join(clean_str.split())\n",
        "    csi_data = np.fromstring(clean_str, sep=' ', dtype=int)\n",
        "    if len(csi_data) < 10: return None\n",
        "    if len(csi_data) % 2 != 0: csi_data = csi_data[:-1]\n",
        "    imag = csi_data[0::2]\n",
        "    real = csi_data[1::2]\n",
        "    phase = np.arctan2(imag, real)\n",
        "    target_len = 128\n",
        "    if len(phase) < target_len:\n",
        "        temp = np.zeros(target_len)\n",
        "        temp[:len(phase)] = phase\n",
        "        phase = temp\n",
        "    elif len(phase) > target_len:\n",
        "        phase = phase[:target_len]\n",
        "    return phase\n",
        "\n",
        "# Re-read one raw CSV per class to get phase\n",
        "plt.figure(figsize=(10, 5))\n",
        "found_classes = set()\n",
        "all_files = glob.glob(os.path.join(DATA_DIR, \"*.csv\"))\n",
        "for file_path in all_files:\n",
        "    filename = os.path.basename(file_path)\n",
        "    label = -1\n",
        "    if \"falling_\" in filename: label = 0\n",
        "    elif \"empty_\" in filename: label = 1\n",
        "    elif \"small_activity_\" in filename: label = 2\n",
        "    \n",
        "    if label != -1 and label not in found_classes:\n",
        "        try:\n",
        "            df = pd.read_csv(file_path, encoding='utf-16', engine='python', on_bad_lines='skip')\n",
        "            if 'CSI_DATA' in df.columns:\n",
        "                for _, row in df.iterrows():\n",
        "                    csi_str = str(row['CSI_DATA'])\n",
        "                    if csi_str != 'nan' and csi_str:\n",
        "                        phase = extract_phase(csi_str)\n",
        "                        if phase is not None:\n",
        "                            plt.plot(phase, label=class_names[label])\n",
        "                            found_classes.add(label)\n",
        "                            break\n",
        "        except: pass\n",
        "    if len(found_classes) == 3: break\n",
        "\n",
        "plt.title('Phase vs Subcarrier Index (Sample)')\n",
        "plt.xlabel('Subcarrier Index')\n",
        "plt.ylabel('Phase (radians)')\n",
        "plt.legend()\n",
        "plt.show()\n"
    ]
}

new_eda_code_2 = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# 3. Average CSI Amplitude overlap graph\n",
        "plt.figure(figsize=(12, 6))\n",
        "avg_amps = []\n",
        "labels_for_sim = []\n",
        "\n",
        "for class_label in [0, 1, 2]:\n",
        "    idx = np.where(y == class_label)[0]\n",
        "    if len(idx) > 0:\n",
        "        # X shape is (samples, 15, 128). Average over all samples and all time steps.\n",
        "        class_avg = np.mean(X[idx], axis=(0, 1))\n",
        "        avg_amps.append(class_avg)\n",
        "        labels_for_sim.append(class_names[class_label])\n",
        "        \n",
        "        plt.plot(class_avg, label=class_names[class_label])\n",
        "\n",
        "plt.title('Average CSI Amplitude Overlap Across All Samples')\n",
        "plt.xlabel('Subcarrier Index')\n",
        "plt.ylabel('Average Amplitude')\n",
        "plt.legend()\n",
        "plt.show()\n",
        "\n",
        "# 4. Interclass cosine similarity heatmap\n",
        "if len(avg_amps) > 1:\n",
        "    sim_matrix = cosine_similarity(avg_amps)\n",
        "    plt.figure(figsize=(6, 5))\n",
        "    import seaborn as sns\n",
        "    sns.heatmap(sim_matrix, annot=True, xticklabels=labels_for_sim, yticklabels=labels_for_sim, cmap='coolwarm', vmin=0, vmax=1)\n",
        "    plt.title('Interclass Cosine Similarity Heatmap')\n",
        "    plt.show()\n"
    ]
}

nb['cells'].insert(insert_idx, new_eda_code_1)
nb['cells'].insert(insert_idx + 1, new_eda_code_2)

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Additional EDA cells inserted.")
