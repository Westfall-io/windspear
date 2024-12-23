from notebook.models import Element, Elements

def handle_literals(element):
    # This function handles literals from SysMLv2 standard
    if element.get_type() == "LiteralInteger":
        print("         Value: {}".format(element.get_key("value")))
        v = element.get_key("value")
    elif element.get_type() == "LiteralString":
        print("         Value: {}".format(element.get_key("value")))
        v = element.get_key("value")
    elif element.get_type() == "LiteralRational":
        print("         Value: {}".format(element.get_key("value")))
        v = element.get_key("value")
    elif element.get_type() == "LiteralBoolean":
        print("         Value: {}".format(element.get_key("value")))
        v = element.get_key("value")
    else:
        # This function returns a True/False whether it was parsed as a literal
        return False, None

    return True, v

def handle_operator_expression(elements, feature, tv):
    for arg in feature.get_subelements("argument", elements).get_elements():
        literal, value = handle_literals(arg)
        if literal:
            tv[list(tv.keys())[0]].append(value)

        elif arg.get_type() == "OperatorExpression":
            # This is likely a list of elements
            tv = handle_operator_expression(elements, arg, tv)
        else:
            print(
                "Could not find a valid type for this toolvariable, skipping."
            )
            print(
                "Please consider submitting this issue to github. The type was {}".format(
                    arg.get_type()
                )
            )

    return tv


def handle_feature_element(elements, feature, tv):
    fetype = feature.get_type()
    print("         Target Element: {}".format(fetype))

    # Get the tool variable name again
    tn = list(tv.keys())[0]

    literal, v = handle_literals(feature)
    if literal:
        # Skip the rest of this code if it's been handled.
        tv[tn].append(v)
        return tv

    if fetype == "OperatorExpression":
        return handle_operator_expression(elements, feature, tv)
        ###### END LOOP for each argument
    elif fetype == "Multiplicity":
        # Don't do anything for this right now.
        print("Skipping found multiplicity.")
    elif fetype == "FeatureChainExpression":
        # This is a reference, do this over again and return whatever the end is
        return handle_feature_chain(elements, feature, tn)
    else:
        print("Could not find a valid type for this toolvariable, skipping.")
        print(
            "Please consider submitting this issue to github. The type was {}".format(
                fetype
            )
        )
    ###### END IF @type
    return tv


def handle_feature_chain(elements, e, tn):
    # elements -- All elements
    # e -- FeatureChainExpression Element
    # tn -- The current variable name

    target = e.get_subelement('targetFeature', elements)

    print("         TargetElement: {}".format(target.get_type()))
    if target.get_key("chainingFeature") is None:
        # No chaining feature
        print("No chaining feature found.")
        raise AttributeError

    chain = target.get_subelements("chainingFeature", elements)

    if not isinstance(chain, list):
        chain = chain.get_elements()

        # Go to the end of the feature chain
        chain = chain[-1]
        print("         ChainElement: {}".format(chain.get_type()))
    else:
        if len(chain) == 0:
            # We're at the end of the feature chain
            chain = target
        else:
            print("         ChainElement Error Returned: {}".format(chain))
            raise NotImplementedError

    # Find the child element of the targeted feature
    tv = {tn:[]}
    chain_elements = chain.get_subelements("ownedElement", elements)
    for feature in chain_elements.get_elements():
        tv = handle_feature_element(elements, feature, tv)
        # Extra elements are probably multiplicity.

    # Remove list if unnecessary
    if len(tv[tn]) == 1:
        tv[tn] = tv[tn][0]

    return tv
