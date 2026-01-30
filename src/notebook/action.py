def add_stored_data(a, prev_a, actions, v, verifications):
    # add_stored_data: Collect action metadata into the running
    # in-memory structures used by the pipeline.
    #
    # Parameters:
    # - a: parsed action object
    # - prev_a: id of the previous action (used to set dependencies)
    # - actions: dict accumulating action records
    # - v: verification container this action belongs to
    # - verifications: dict accumulating verification records
    #
    # The function appends action metadata to `verifications` and creates
    # a normalized entry in `actions` with placeholders for tool URIs
    # and variables.
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
