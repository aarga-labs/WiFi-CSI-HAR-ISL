import json

src_file = 'd:/WIFI-HAR/csi_fall_detection_3class_temporal_full.ipynb'
dst_file = 'd:/WIFI-HAR/csi_fall_detection_3class_temporal_lstm.ipynb'

with open(src_file, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        # Change title
        for i, line in enumerate(cell['source']):
            if '# CSI Fall Detection - 3 Class Temporal Model' in line:
                cell['source'][i] = line.replace('Model', 'LSTM Model')

    elif cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # Change imports
        if 'from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization' in source:
            new_source = source.replace(
                'from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization',
                'from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization'
            )
            cell['source'] = [line + '\n' for line in new_source.split('\n')][:-1]
            
        # Change model architecture
        elif 'model = Sequential([' in source and 'Conv1D' in source:
            new_source = """model = Sequential([

    LSTM(64, return_sequences=True, input_shape=(WINDOW_SIZE,128)),
    BatchNormalization(),

    LSTM(64),
    BatchNormalization(),

    Dense(128, activation='relu'),
    Dropout(0.5),

    Dense(3, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()
"""
            cell['source'] = [line + '\n' for line in new_source.split('\n')][:-1]
            
        # Change save names
        elif 'model.save("fall_detection_3class.h5")' in source:
            new_source = source.replace('fall_detection_3class.h5', 'fall_detection_3class_lstm.h5')
            new_source = new_source.replace('fall_detection_3class.tflite', 'fall_detection_3class_lstm.tflite')
            new_source = new_source.replace('Saved H5 and TFLite models', 'Saved LSTM H5 and TFLite models')
            cell['source'] = [line + '\n' for line in new_source.split('\n')][:-1]

with open(dst_file, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("LSTM notebook successfully generated.")
