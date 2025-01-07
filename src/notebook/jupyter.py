# Copyright (c) 2023-2025 Westfall Inc.
#
# This file is part of Windspear.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, and can be found in the file NOTICE inside this
# git repository.
#
# This program is distributed in the hope that it will be useful
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
