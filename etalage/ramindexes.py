# -*- coding: utf-8 -*-


# Etalage -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
#
# Copyright (C) 2011, 2012 Easter-eggs
# http://gitorious.org/infos-pratiques/etalage
#
# This file is part of Etalage.
#
# Etalage is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Etalage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Generic toolbox for RAM-based indexes"""


def delete_remaining(indexes, remaining):
    for index_type, remaining_for_type in remaining.iteritems():
        if index_type == 'dict_of_sets':
            for index_name, remaining_for_index in remaining_for_type.iteritems():
                index = getattr(indexes, index_name)
                for value, keys in remaining_for_index.iteritems():
                    for key in keys:
                        key_values = index[key]
                        key_values.discard(value)
                        if key_values is None:
                            del index[key]
        elif index_type == 'dict_of_values':
            for index_name, remaining_for_index in remaining_for_type.iteritems():
                index = getattr(indexes, index_name)
                for value, keys in remaining_for_index.iteritems():
                    for key in keys:
                        del index[key]
        else:
            raise KeyError(index_type)


def find_existing(indexes, index_name, index_type, value, existing):
    found_keys = find_value_functions[index_type](getattr(indexes, index_name), value)
    if found_keys is not None:
        existing.setdefault(index_type, {}).setdefault(index_name, {})[value] = found_keys
    return found_keys


def find_value_in_dict_of_sets(index, value):
    found_keys = []
    for key, key_values in index.iteritems():
        if value in key_values:
            found_keys.append(key)
    return found_keys or None


def find_value_in_dict_of_values(index, value):
    found_keys = []
    for key, key_value in index.iteritems():
        if value == key_value:
            found_keys.append(key)
    return found_keys or None


def intersection_set(iterables):
    result = None
    for iterable in iterables:
        if iterable is None:
            continue
        if result is None:
            result = set(iterable)
        else:
            result.intersection_update(iterable)
    return result


def union_set(iterables):
    result = None
    for iterable in iterables:
        if iterable is None:
            continue
        if result is None:
            result = set(iterable)
        else:
            result.update(iterable)
    return result


find_value_functions = {
    'dict_of_sets': find_value_in_dict_of_sets,
    'dict_of_values': find_value_in_dict_of_values,
    }
