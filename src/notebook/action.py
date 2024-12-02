def add_stored_data(a, prev_a, actions, v, verifications):
    # Consider this a sim run
    verifications[v.get_id()]['actions'].append({
        'id' : a.get_id(),
        'declaredName' : a.get_key('declaredName'),
        'qualifiedName' : a.get_key('qualifiedName')
    })

    actions[a.get_id()] = {
        'verification': v.get_id(),
        'shortName': a.get_key('shortName'),
        'declaredName' : a.get_key('declaredName'),
        'qualifiedName' : a.get_key('qualifiedName'),
        'tools': {
            'harbor': None,
            'artifacts': None,
            'variables': {}
        }
    }

    # Add that this action is dependent on the previous
    if prev_a is not None:
        actions[a.get_id()]['dependency'] = prev_a
    prev_a = a.get_id()

    return actions, prev_a, verifications
