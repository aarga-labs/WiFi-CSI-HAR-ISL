import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv1D, MaxPooling1D, Flatten, Dense, Concatenate, Dropout
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

print("Loading custom pocket datasets...")
X = np.load("X_data.npy")
y = np.load("y_data.npy")

X_acc = X[:, :, 0:3]  
X_gyro = X[:, :, 3:6] 

X_acc_train, X_acc_test, X_gyro_train, X_gyro_test, y_train, y_test = train_test_split(
    X_acc, X_gyro, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training on {len(y_train)} windows, Testing on {len(y_test)} windows.")

input_shape = (128, 3)

# Stream A: Accelerometer
input_acc = Input(shape=input_shape, name="Accel_Input")
x_acc = Conv1D(filters=64, kernel_size=3, activation='relu')(input_acc)
x_acc = MaxPooling1D(pool_size=2)(x_acc)
x_acc = Conv1D(filters=32, kernel_size=3, activation='relu')(x_acc)
x_acc = MaxPooling1D(pool_size=2)(x_acc)
x_acc = Flatten()(x_acc)

# Stream B: Gyroscope
input_gyro = Input(shape=input_shape, name="Gyro_Input")
x_gyro = Conv1D(filters=64, kernel_size=3, activation='relu')(input_gyro)
x_gyro = MaxPooling1D(pool_size=2)(x_gyro)
x_gyro = Conv1D(filters=32, kernel_size=3, activation='relu')(x_gyro)
x_gyro = MaxPooling1D(pool_size=2)(x_gyro)
x_gyro = Flatten()(x_gyro)

# Fusion Layer
merged = Concatenate()([x_acc, x_gyro])

# Decision Layers
z = Dense(64, activation='relu')(merged)
z = Dropout(0.5)(z) # Prevent overfitting
output = Dense(1, activation='sigmoid', name="Fall_Prediction")(z)

# Compile the Model
model = Model(inputs=[input_acc, input_gyro], outputs=output)
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

print("\nStarting Training Phase...")
history = model.fit(
    [X_acc_train, X_gyro_train], y_train,
    epochs=20,
    batch_size=32,
    validation_data=([X_acc_test, X_gyro_test], y_test)
)

model.save("fall_detection_model.keras")
print("\nSuccess! Model saved as 'fall_detection_model.keras'")

# Plot the accuracy
plt.figure(figsize=(10, 4))
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy on Custom Pocket Data')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)
plt.show()