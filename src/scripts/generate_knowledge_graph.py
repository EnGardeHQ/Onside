from rdflib import Graph, URIRef, Literal, Namespace

# Define namespaces
CORP = Namespace("http://example.org/corporation/")
STAKE = Namespace("http://example.org/stakeholder/")

# Initialize RDF graph
g = Graph()

# Define classes and properties (Ontology)
g.add((CORP.Corporation, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://www.w3.org/2000/01/rdf-schema#Class")))
g.add((CORP.hasName, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://www.w3.org/2000/01/rdf-schema#Property")))
g.add((CORP.hasStakeholder, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://www.w3.org/2000/01/rdf-schema#Property")))

# Add instance data for a corporation
corp_id = URIRef(CORP["corp123"])
g.add((corp_id, CORP.hasName, Literal("Tech Innovators Ltd")))
g.add((corp_id, URIRef("http://example.org/corporation/hasIndustry"), Literal("Technology")))

# Add instance data for a stakeholder
stakeholder_id = URIRef(STAKE["stake456"])
g.add((stakeholder_id, URIRef("http://example.org/stakeholder/hasName"), Literal("Jane Doe")))
g.add((stakeholder_id, URIRef("http://example.org/stakeholder/hasRole"), Literal("Investor")))

# Define the relationship between corporation and stakeholder
g.add((corp_id, CORP.hasStakeholder, stakeholder_id))

# Save the RDF graph to a file in Turtle format
g.serialize(destination="vensights_data.ttl", format="turtle")
