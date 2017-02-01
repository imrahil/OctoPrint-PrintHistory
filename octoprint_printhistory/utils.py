#!/usr/bin/python
import collections
import json


def prepare_dict(dictionary):
    for key in dictionary.keys():
        if key.count(" ") > 0:
            new_key = key.replace(" ", "_")
            dictionary[new_key] = dictionary.pop(key)
    return dictionary

def rename_duplicates(immutable, mutable, prefix):
    """
    Add prefix to elements of `mutable` if they are in `immutable`.
    :param immutable: list of strings
    :param mutable: list of strings
    :param prefix: string
    :return: list with renamed elements
    """
    for value in mutable:
        if value in immutable:
            mutable[mutable.index(value)] = str(prefix) + value
    return mutable

def namedtuple_with_defaults(typename, field_names, default_values=()):
    """
    http://stackoverflow.com/questions/11351032/named-tuple-and-optional-keyword-arguments
    """
    T = collections.namedtuple(typename, field_names)
    T.__new__.__defaults__ = (None,) * len(T._fields)
    if isinstance(default_values, collections.Mapping):
        prototype = T(**default_values)
    else:
        prototype = T(*default_values)
    T.__new__.__defaults__ = tuple(prototype)
    return T

def load_json(dictionary, key):
    parameters_json = dictionary.get(key)
    try:
        parameters = json.loads(parameters_json)
    except ValueError:
        parameters = {}
    return parameters
