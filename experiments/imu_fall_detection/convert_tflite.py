import tensorflow as tf

print("Loading the trained Keras model...")
# Load the model you just trained
model = tf.keras.models.load_model("fall_detection_model.keras")

print("Starting conversion to TensorFlow Lite...")
# Initialize the converter
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# OPTIMIZATION (Crucial for Mobile Apps)
# This compresses the model weights to make it faster on mobile CPUs
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# Perform the conversion
tflite_model = converter.convert()

# Save the .tflite file to your folder
with open('fall_detection_model.tflite', 'wb') as f:
    f.write(tflite_model)

print("\nSuccess! Your model is converted and saved as 'fall_detection_model.tflite'.")