import json

filepath = 'd:/WIFI-HAR/csi_fall_detection_3class_temporal_full.ipynb'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"WINDOW_SIZE = 50\\n",', '"WINDOW_SIZE = 15\\n",')
content = content.replace('"    for start in range(0, len(packets) - WINDOW_SIZE + 1, 10):\\n",', '"    for start in range(0, len(packets) - WINDOW_SIZE + 1, 5):\\n",')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modifications complete.")
