from arango import ArangoClient
from arango_datasets import Datasets
import networkx as nx
import matplotlib.pyplot as plt
from config import ARANGO_HOST, ARANGO_USERNAME, ARANGO_PASSWORD

# Connect to database
db = ArangoClient(hosts=ARANGO_HOST).db(
    username=ARANGO_USERNAME, 
    password=ARANGO_PASSWORD, 
    verify=True
)

# Connect to datasets
datasets = Datasets(db)

# Delete existing graph if it exists
if db.has_graph("OPEN_INTELLIGENCE"):
    db.delete_graph("OPEN_INTELLIGENCE")

# List datasets
print(datasets.list_datasets())

# List more information about a particular dataset
print(datasets.dataset_info("OPEN_INTELLIGENCE"))

datasets.load("OPEN_INTELLIGENCE")


# Test Query for violence example
aql_query = """
FOR t IN Event
    FILTER STARTS_WITH(t.date, "2020")
    FILTER 
        t.fatalities > 100
    RETURN t
"""
# Execute the query
cursor = db.aql.execute(aql_query)
civilian_violence_events = list(cursor)

# Print the results
print(civilian_violence_events)