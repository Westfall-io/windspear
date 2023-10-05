import os
import json

import networkx as nx

G = nx.DiGraph()

elements = {}
dir_path = 'tmp/sysml_workflow/FireSat.ipynb'
for (dir_path, dir_names, file_names) in os.walk(dir_path):
    for name in file_names:
        path = os.path.join(dir_path, name)

        with open(path, 'r') as f:
            data = json.load(f)
            G.add_node(data['identity']['@id'])
            elements[data['identity']['@id']] = data
            for key in data['payload'].keys():
                if '@id' in json.dumps(data['payload'][key]):
                    if isinstance(data['payload'][key], list):
                        if len(data['payload'][key]) < 5:
                            for item in data['payload'][key]:
                                G.add_edge(data['identity']['@id'], item['@id'], weight=len(data['payload'][key])*100000)
                    elif isinstance(data['payload'][key], dict):
                        G.add_edge(data['identity']['@id'], data['payload'][key]['@id'],weight=1)
                    else:
                        raise TypeError("Can't handle this type.")
                else:
                    continue

while True:
    path = []
    source = input('Source ID name: ')
    target = input('Target ID name: ')
    sps = list(nx.all_shortest_paths(G, source=source, target=target, weight="weight"))
    #sp.reverse()
    for sp in sps:
        print('Path 1')
        for i in range(len(sp)-1):
            #print('Finding path between {} and {}.'.format(sp[i],sp[i+1]))
            # Each point in the path (minus one)
            base = elements[sp[i]]['payload']
            for key in base:
                if '@id' in json.dumps(base[key]):
                    if isinstance(base[key], list):
                        breakflag = False
                        for item in base[key]:
                            if sp[i+1] == item['@id']:
                                print('path found')
                                path.append(key)
                                breakflag = True
                                break
                            else:
                                #print(item['@id'])
                                pass
                        if breakflag:
                            break
                    elif isinstance(base[key], dict):
                        if sp[i+1] == base[key]['@id']:
                            print('path found')
                            path.append(key)
                            # Stop checking keys
                            break
                        else:
                            pass
                            #print(base[key]['@id'])
                    else:
                        raise TypeError("Can't handle this type.")
                else:
                    continue

            if len(path) != i+1:
                raise ValueError

        print('{} -- {}'.format(elements[sp[0]]['payload']['@type'], sp[0]))
        for k,v in enumerate(path):
            e = elements[sp[k]]['payload']
            print('   key:{} -- values:{}'.format(v, e[v]))
            for key in e.keys():
                if 'name' in key.lower() and isinstance(e[key], str):
                    print('name:{},type:{} -- id:{}'.format(e[key],elements[sp[k+1]]['payload']['@type'], sp[k+1]))
                    break
            else:
                print('type:{} -- id:{}'.format(elements[sp[k+1]]['payload']['@type'], sp[k+1]))
