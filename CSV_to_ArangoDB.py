from arango import ArangoClient
import pandas as pd
import numpy as np
import os
from datetime import datetime
from config import ARANGO_HOST, ARANGO_USERNAME, ARANGO_PASSWORD

ARANGO_DB = 'Gdelt_DB'

def clean_value(value):
    """Clean and validate values before insertion"""
    if pd.isna(value) or value == '':
        return None
    elif isinstance(value, (np.int64, np.float64)):
        return float(value) if isinstance(value, np.float64) else int(value)
    else:
        return str(value)
    
def delete_collections():
    # Connect to ArangoDB
    db = ArangoClient(hosts=ARANGO_HOST).db(
    username=ARANGO_USERNAME, 
    password=ARANGO_PASSWORD, 
    verify=True
)
    # Get all collections in the database
    all_collections = db.collections()
    
    # Delete each collection if it's not a system collection
    for collection in all_collections:
        # Skip system collections (they start with '_')
        if not collection['name'].startswith('_'):
            db.delete_collection(collection['name'])
            print(f"Deleted collection: {collection['name']}")

def connect_to_arango():
    """Establish connection to ArangoDB and create database if it doesn't exist"""
    sys_db = ArangoClient(hosts=ARANGO_HOST).db(
    username=ARANGO_USERNAME, 
    password=ARANGO_PASSWORD, 
    verify=True
)
    
    if not sys_db.has_database(ARANGO_DB):
        sys_db.create_database(ARANGO_DB)
    
    db = ArangoClient(hosts=ARANGO_HOST).db(
    username=ARANGO_USERNAME, 
    password=ARANGO_PASSWORD, 
    verify=True
)
    return db

def setup_collections(db):
    """Create necessary collections if they don't exist"""
    collections = {}
    
    # Vertex collections
    for name in ['Events', 'Actors', 'Locations']:
        if not db.has_collection(name):
            collections[name.lower()] = db.create_collection(name)
        else:
            collections[name.lower()] = db.collection(name)
    
    # Edge collection
    if not db.has_collection('EventRelations'):
        collections['relations'] = db.create_collection('EventRelations', edge=True)
    else:
        collections['relations'] = db.collection('EventRelations')
    
    return collections

def process_latest_csv():
    """Process the most recent CSV file from the output directory"""
    output_dir = "/Users/aahilali/Desktop/ArangoDBOutput"
    
    csv_files = [f for f in os.listdir(output_dir) if f.endswith('.CSV')]
    if not csv_files:
        print("No CSV files found in output directory")
        return None
    
    latest_file = max([os.path.join(output_dir, f) for f in csv_files], 
                     key=os.path.getmtime)
    
    print(f"Processing file: {latest_file}")
    df = pd.read_csv(latest_file)
    
    # Convert numeric columns to appropriate types
    numeric_columns = ['GlobalEventID', 'Day', 'MonthYear', 'Year', 'GoldsteinScale', 
                      'NumMentions', 'NumSources', 'NumArticles', 'AvgTone', 
                      'Actor1Geo_Lat', 'Actor1Geo_Long']
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def create_graph_data(df, collections):
    """Convert DataFrame rows into graph components"""
    # Clear existing data
    for collection in collections.values():
        collection.truncate()
    
    for index, row in df.iterrows():
        try:
            # Create Event vertex
            event_doc = {
                '_key': str(int(row['GlobalEventID'])),
                'eventCode': clean_value(row['EventCode']),
                'baseCode': clean_value(row['EventBaseCode']),
                'rootCode': clean_value(row['EventRootCode']),
                'quadClass': clean_value(row['QuadClass']),
                'goldsteinScale': clean_value(row['GoldsteinScale']),
                'numMentions': clean_value(row['NumMentions']),
                'numSources': clean_value(row['NumSources']),
                'numArticles': clean_value(row['NumArticles']),
                'avgTone': clean_value(row['AvgTone']),
                'date': clean_value(row['Day']),
                'year': clean_value(row['Year']),
                'monthYear': clean_value(row['MonthYear']),
                'fractionDate': clean_value(row['FractionDate'])
            }
            
            # Remove None values
            event_doc = {k: v for k, v in event_doc.items() if v is not None}
            
            print(f"Inserting event {index + 1}: {event_doc['_key']}")
            collections['events'].insert(event_doc)
            
            # Create Actor vertex
            actor_key = f"actor_{str(int(row['GlobalEventID']))}"
            actor_doc = {
                '_key': actor_key,
                'type1Code': clean_value(row['Actor1Type1Code']),
                'type2Code': clean_value(row['Actor1Type2Code']),
                'type3Code': clean_value(row['Actor1Type3Code']),
                'countryCode': clean_value(row['Actor1CountryCode'])
            }
            
            # Remove None values
            actor_doc = {k: v for k, v in actor_doc.items() if v is not None}
            collections['actors'].insert(actor_doc)
            
            # Create Location vertex if coordinates exist
            if pd.notna(row['Actor1Geo_Lat']) and pd.notna(row['Actor1Geo_Long']):
                location_key = f"loc_{str(int(row['GlobalEventID']))}"
                location_doc = {
                    '_key': location_key,
                    'type': clean_value(row['Actor1Geo_Type']),
                    'fullname': clean_value(row['Actor1Geo_Fullname']),
                    'countryCode': clean_value(row['Actor1Geo_CountryCode']),
                    'adm1Code': clean_value(row['Actor1Geo_ADM1Code']),
                    'adm2Code': clean_value(row['Actor1Geo_ADM2Code']),
                    'latitude': clean_value(row['Actor1Geo_Lat']),
                    'longitude': clean_value(row['Actor1Geo_Long']),
                    'featureID': clean_value(row['Actor1Geo_FeatureID'])
                }
                
                # Remove None values
                location_doc = {k: v for k, v in location_doc.items() if v is not None}
                collections['locations'].insert(location_doc)
                
                # Create edge between Event and Location
                edge_doc = {
                    '_from': f"Events/{str(int(row['GlobalEventID']))}",
                    '_to': f"Locations/{location_key}",
                    'type': 'OCCURRED_AT'
                }
                collections['relations'].insert(edge_doc)
            
            # Create edge between Event and Actor
            edge_doc = {
                '_from': f"Events/{str(int(row['GlobalEventID']))}",
                '_to': f"Actors/{actor_key}",
                'type': 'HAS_ACTOR'
            }
            collections['relations'].insert(edge_doc)
            
        except Exception as e:
            print(f"Error processing row {index + 1}: {str(e)}")
            print(f"Row data: {row.to_dict()}")
            continue

def main():
    # try:
    #     print("Connecting to ArangoDB...")
    #     db = connect_to_arango()

    #     print("Deleting collections...")
    #     delete_collections()
    #     print("Collections deleted successfully!")
        
    #     print("Setting up collections...")
    #     collections = setup_collections(db)
        
    #     print("Processing CSV file...")
    #     df = process_latest_csv()
    #     if df is None:
    #         return
        
    #     print("Creating graph data...")
    #     create_graph_data(df, collections)
        
    #     print("Graph database successfully created!")
    #     print(f"Total events processed: {len(df)}")
        
    # except Exception as e:
    #     print(f"Error: {str(e)}")
    #     import traceback
    #     print(traceback.format_exc())

    # Connect to database
    db = ArangoClient(hosts=ARANGO_HOST).db(
        username=ARANGO_USERNAME, 
        password=ARANGO_PASSWORD, 
        verify=True
    )
    # Test Query for violence example
    aql_query = """
    WITH Events, Actors, Locations, EventRelations
    FOR event IN Events
    FILTER event.goldsteinScale > 5
    LET actor = (
        FOR v, e IN 1..1 OUTBOUND event EventRelations
        FILTER IS_SAME_COLLECTION("Actors", v)
        RETURN v
    )[0]
    LET location = (
        FOR v, e IN 1..1 OUTBOUND event EventRelations
        FILTER IS_SAME_COLLECTION("Locations", v)
        RETURN v
    )[0]
    RETURN {
        eventID: event._key,
        goldsteinScale: event.goldsteinScale,
        eventCode: event.eventCode,
        eventDate: event.date,
        actor: {
            type1Code: actor.type1Code,
            type2Code: actor.type2Code,
            countryCode: actor.countryCode
        },
        location: location ? {
            fullname: location.fullname,
            countryCode: location.countryCode,
            coordinates: [location.latitude, location.longitude]
        } : null
    }
    """
    # Execute the query
    cursor = db.aql.execute(aql_query)
    intersting_events = list(cursor)

    # Print the results
    print(intersting_events)

if __name__ == "__main__":
    main()