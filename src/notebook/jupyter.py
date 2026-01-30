def _base_nb():
    # _base_nb: Return a minimal notebook JSON structure configured with
    # SoS/SysML kernels. This helper is used to synthesize in-memory
    # notebooks for execution or model extraction.
    return {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "SoS",
                "language": "sos",
                "name": "sos"
            },
            "language_info": {
                "codemirror_mode": "sos",
                "file_extension": ".sos",
                "mimetype": "text/x-sos",
                "name": "sos",
                "nbconvert_exporter": \
                    "sos_notebook.converter.SoS_Exporter",
                "pygments_lexer": "sos"
            },
            "sos": {
                "kernels": [
                    [
                        "Python3",
                        "python3",
                        "Python3",
                        "#FFD91A",
                        {
                            "name": "ipython",
                            "version": 3
                        }
                    ],
                    [
                        "SoS",
                        "sos",
                        "",
                        "",
                        "sos"
                    ],
                    [
                        "SysML",
                        "sysml",
                        "sysml",
                        "",
                        "sysml"
                    ]
                ],
                "version": "0.24.2",
                }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

def _make_nb_cell(model_id, model_text, tags=[]):
    # _make_nb_cell: Create a single code cell dictionary shaped like a
    # Jupyter notebook cell. The `model_text` is placed into the cell's
    # `source` and `model_id` is used as the cell id.
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": model_id,
        "metadata": {
            "kernel": "SysML",
            "tags": tags
        },
        "outputs": [],
        "source": [model_text]
    }
