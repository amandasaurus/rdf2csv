# -*- coding: utf-8 -*-

__author__ = 'Rory McCann'
__email__ = 'rory@technomancy.org'
__version__ = '0.1.0'

import rdflib
from rdflib.plugins.sparql import prepareQuery
import csv
import argparse
import sys
import zipfile
import StringIO
import json
import yaml

def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rdf", help="Input RDF file to read", required=True)
    parser.add_argument("-c", "--converter", help="JSON/YAML file to use to convert", required=True)
    parser.add_argument("-z", "--zip", help="Output ZIP file to write to", required=True)
    args = parser.parse_args(argv)

    with open(args.converter) as converter_fp:
        converter_dict = read_json_or_yaml(args.converter, converter_fp.read())

    with open(args.zip, 'w') as zip_fp:
        graph = rdflib.Graph()
        with open(args.rdf) as rdf_fp:
            graph.parse(args.rdf, format=rdflib.util.guess_format(args.rdf))

        convert_from_dict(graph, converter_dict, zip_fp)


def read_json_or_yaml(filename, contents):
    if filename.lower().endswith(".json"):
        results = json.loads(contents)
        return results
    elif filename.lower().endswith(".yaml") or filename.lower().endswith(".yml"):
        results = yaml.safe_load(contents)
        return results
    else:
        # Try both
        try:
            results = json.loads(contents)
            return results
        except ValueError:
            try:
                results = yaml.safe_load(contents)
                return results
            except yaml.parser.ParserError:
                raise Exception("Invalid converter file")


def resultrowkey_to_csvvalue(resultrow, key):
    if resultrow[key] is None:
        return ''
    elif isinstance(resultrow[key], rdflib.term.URIRef):
        return unicode(resultrow[key])
    elif isinstance(resultrow[key], rdflib.term.Literal):
        return unicode(resultrow[key].value).encode("utf-8")
    else:
        raise NotImplementedError()

def apply_filters(key, value, filters):
    if key not in filters:
        return value
    else:
        filter_code = filters[key]
        new_value = eval(filter_code, {'x': value})
        return new_value


def convert(rdf_filename, csv_filename, sparql_query):
    graph = rdflib.Graph()
    graph.parse(rdf_filename, format=rdflib.util.guess_format(rdf_filename))

    with open(csv_filename, 'w') as fp:
        extract_csv_from_graph(graph=graph, sparql_query=sparql_query, csv_fp=fp)


def extract_csv_from_graph(graph, sparql_query, csv_fp, filters=None):
    filters = filters or {}

    query = prepareQuery(sparql_query, initNs=dict(graph.namespaces()))
    column_names = [str(k) for k in query.algebra['PV']]

    writer = csv.DictWriter(csv_fp, column_names, lineterminator="\n")
    writer.writeheader()

    for resultrow in graph.query(query):
        row_dict = {}
        for column_name in column_names:
            raw_value = resultrowkey_to_csvvalue(resultrow, column_name)
            value = apply_filters(column_name, raw_value, filters)
            row_dict[column_name] = value

        writer.writerow(row_dict)

def convert_from_dict(graph, converter_dict, output_zipfile_fp):
    with zipfile.ZipFile(output_zipfile_fp, 'w') as zipf:
        for filename, sparql_query in converter_dict['files'].items():
            output = StringIO.StringIO()
            extract_csv_from_graph(graph, sparql_query, output, filters=converter_dict.get('filters'))
            zipf.writestr(filename, output.getvalue())



if __name__ == '__main__':
    main(sys.argv[1:])
