#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_rdf2csv
----------------------------------

Tests for `rdf2csv` module.
"""

import unittest

import rdf2csv
import rdflib
import StringIO
import zipfile

def simple_graph():
    graph = rdflib.Graph()
    graph.add((rdflib.URIRef('http://example.com/people/1'), rdflib.URIRef("http://example.com/name"), rdflib.Literal('Bob')))
    graph.add((rdflib.URIRef('http://example.com/people/1'), rdflib.URIRef("http://example.com/age"), rdflib.Literal(10)))
    graph.add((rdflib.URIRef('http://example.com/people/2'), rdflib.URIRef("http://example.com/name"), rdflib.Literal('Alice')))
    graph.add((rdflib.URIRef('http://example.com/people/2'), rdflib.URIRef("http://example.com/age"), rdflib.Literal(20)))
    return graph


class TestRdf2csv(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_simple(self):
        csv_output = StringIO.StringIO()
        graph = simple_graph()

        rdf2csv.extract_csv_from_graph(
            graph,
            "SELECT ?name ?age WHERE { ?x <http://example.com/name> ?name ; <http://example.com/age> ?age . } ORDER BY ?x",
            csv_output)
        self.assertEquals(csv_output.getvalue(), "name,age\nBob,10\nAlice,20\n")

    def test_dict_to_zipfile(self):
        convert_dict = {
            'files': {
                'ages.csv': "SELECT ?personid ?age WHERE { ?personid <http://example.com/age> ?age . } ORDER BY ?personid",
                'names.csv': "SELECT ?personid ?name WHERE { ?personid <http://example.com/name> ?name . } ORDER BY ?personid",
            },
            'filters': {
                'personid': 'x.split("/")[-1]',
            }
        }

        zip_output_fp = StringIO.StringIO()

        rdf2csv.convert_from_dict(simple_graph(), convert_dict, zip_output_fp)

        z = zipfile.ZipFile(zip_output_fp)
        self.assertEqual(z.namelist(), ['ages.csv', 'names.csv'])
        self.assertEqual(z.read("ages.csv"), "personid,age\n1,10\n2,20\n")
        self.assertEqual(z.read("names.csv"), "personid,name\n1,Bob\n2,Alice\n")





if __name__ == '__main__':
    unittest.main()
