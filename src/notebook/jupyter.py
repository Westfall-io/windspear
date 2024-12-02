def _base_nb():
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
