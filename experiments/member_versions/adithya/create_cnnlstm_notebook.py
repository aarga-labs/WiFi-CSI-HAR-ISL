import json

src_file = 'd:/WIFI-HAR/csi_fall_detection_3class_temporal_lstm.ipynb'
dst_file = 'd:/WIFI-HAR/csi_fall_detection_3class_temporal_cnnlstm.ipynb'

with open(src_file, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        # Change title
        for i, line in enumerate(cell['source']):
            if '# CSI Fall Detection - 3 Class Temporal LSTM Model' in line:
                cell['source'][i] = line.replace('LSTM Model', 'CNN-LSTM Model')

    elif cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # Change imports
        if 'from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization' in source:
            new_source = source.replace(
                'from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization',
                'from tensorflow.keras.layers import Conv1D, MaxPooling1D, LSTM, Dense, Dropout, BatchNormalization'
            )
            cell['source'] = [line + '\n' for line in new_source.split('\n')][:-1]
            
        # Change model architecture
        elif 'model = Sequential([' in source and 'LSTM' in source:
            new_source = """model = Sequential([

    Conv1D(32, 3, activation='relu', input_shape=(WINDOW_SIZE,128)),
    BatchNormalization(),
    MaxPooling1D(2),

    Conv1D(64, 3, activation='relu'),
    BatchNormalization(),
    MaxPooling1D(2),

    LSTM(64, return_sequences=True),
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
        elif 'model.save("fall_detection_3class_lstm.h5")' in source:
            new_source = source.replace('fall_detection_3class_lstm.h5', 'fall_detection_3class_cnnlstm.h5')
            new_source = new_source.replace('fall_detection_3class_lstm.tflite', 'fall_detection_3class_cnnlstm.tflite')
            new_source = new_source.replace('Saved LSTM H5', 'Saved CNN-LSTM H5')
            cell['source'] = [line + '\n' for line in new_source.split('\n')][:-1]

with open(dst_file, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("CNN-LSTM notebook successfully generated.")
