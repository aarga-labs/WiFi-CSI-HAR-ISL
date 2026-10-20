import h5py
import json

filename = 'fall_detection_model.h5'

with h5py.File(filename, 'r+') as f:
    # Read the model configuration
    model_config = f.attrs.get('model_config')
    if model_config:
        config_dict = json.loads(model_config.decode('utf-8') if isinstance(model_config, bytes) else model_config)
        
        # Loop through layers and remove 'quantization_config'
        for layer in config_dict['config']['layers']:
            if 'config' in layer and 'quantization_config' in layer['config']:
                del layer['config']['quantization_config']
        
        # Save the modified config back to the file
        f.attrs['model_config'] = json.dumps(config_dict).encode('utf-8')
        print("Model config cleaned successfully.")