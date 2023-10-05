import os
import json

dir_path = 'tmp'
for (dir_path, dir_names, file_names) in os.walk(dir_path):
    for name in file_names:
        path = os.path.join(dir_path, name)

        with open(path, 'r') as f:
            data = f.read()

        if '"value": 10,' in data:
            print(name)
            print('\n\n-----')
            print(data)
            break
