from arango import ArangoClient
from arango_datasets import Datasets
import networkx as nx
import matplotlib.pyplot as plt

# Connect to database
db = ArangoClient(hosts="https://5d31644e470d.arangodb.cloud:8529").db(username="root", password="yEYB1v1BTw5Gd9yP2von", verify=True)

# Connect to datasets
datasets = Datasets(db)

# Delete existing graph if it exists
# if db.has_graph("OPEN_INTELLIGENCE"):
#     db.delete_graph("OPEN_INTELLIGENCE")

# List datasets
# print(datasets.list_datasets())

# List more information about a particular dataset
print(datasets.dataset_info("OPEN_INTELLIGENCE"))

# datasets.load("OPEN_INTELLIGENCE")


# Query for violence against civilians events in Algeria
aql_query = """
FOR t IN Event
    FILTER DATE_YEAR(t.date) == 2019
    RETURN t
"""

# Execute the query
cursor = db.aql.execute(aql_query)
civilian_violence_events = list(cursor)

# Print the results
print(civilian_violence_events)