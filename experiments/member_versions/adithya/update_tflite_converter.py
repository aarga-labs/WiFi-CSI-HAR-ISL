import json

filepath = 'd:/WIFI-HAR/csi_fall_detection_3class_temporal_lstm.ipynb'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_converter_code = """    "converter.optimizations = [tf.lite.Optimize.DEFAULT]\\n",
    "\\n",
    "tflite_model = converter.convert()\\n","""

new_converter_code = """    "converter.optimizations = [tf.lite.Optimize.DEFAULT]\\n",
    "converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]\\n",
    "converter._experimental_lower_tensor_list_ops = False\\n",
    "\\n",
    "tflite_model = converter.convert()\\n","""

content = content.replace(old_converter_code, new_converter_code)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("TFLite converter code updated.")
