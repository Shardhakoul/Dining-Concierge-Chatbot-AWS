from datetime import datetime
import requests
import json
from decimal import *
import boto3
from urllib.parse import quote

API_KEY = "N4a5goKB-N1rpllBVMYv-yg5MkngautOAWU1aOGG7sRFxBanAoYAAe6cpJS92njJ2dB1b0cfy56nMv0TG8rf66O-Is1Vu74uyqJz08BgUXebZYEWP3ewXUaQvT9eYXYx"

# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.

# Defaults for our simple example.
DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'manhattan'
SEARCH_LIMIT = 50

# connect to the dyanmoDB
client = boto3.resource(service_name='dynamodb',
                          aws_access_key_id="YOUR ACESS KEY",
                          aws_secret_access_key="YOUR SECRET KEY",
                          region_name="us-east-1",
                         )
table = client.Table('yelp-restaurants')

# function to make an api request
def request(host, path, api_key, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    print(u'Querying {0} ...'.format(url), url_params)

    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()

# function to use the search API
def search(api_key, term, location, offset):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT,
        'offset': offset,
        'radius':40000
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

# # function to get required fields
def handle_response(businesses, cuisine):
    documents = []
    for item in businesses:
        restaurant = {
            "Business ID": item["id"],
            "Name": item["name"],
            "Address": item["location"]["address1"],
            "Coordinates": {"latitude": item["coordinates"]["latitude"], "longitude": item["coordinates"]["longitude"]},
            "Number of Reviews": item["review_count"],
            "Rating": item["rating"],
            "Zip Code": item["location"]["zip_code"],
            "cuisine": cuisine
        }
        documents.append(restaurant)
    return json.loads(json.dumps(documents), parse_float=Decimal)

# function to push data into dynamoDB
def push_data(businesses):
    with table.batch_writer() as batch:
        for business in businesses:
            now = datetime.now()
            businessTemp = business
            businessTemp["insertedAtTimestamp"] = now.strftime("%d/%m/%Y %H:%M:%S")
            batch.put_item(businessTemp)

cuisines = ['indian', 'italian', 'chinese', 'vietnamese', 'mexican', 'French', 'Thai', 'Burmese', 'Japanese', 'Persian', 'Turkish']

manhattan_neighbourhoods = ['Lower East Side, Manhattan',
                   'Upper East Side, Manhattan',
                   'Upper West Side, Manhattan',
                   'Washington Heights, Manhattan',
                   'Central Harlem, Manhattan',
                   'Chelsea, Manhattan',
                   'Manhattan',
                   'East Harlem, Manhattan',
                   'Gramercy Park, Manhattan',
                   'Greenwich, Manhattan',
                   'Lower Manhattan, Manhattan',
                   'Columbus Circle, Manhattan'
                   'Times Square, Manhattan',
                   'Hells Kitchen, Manhattan',
                   'Midtown, Manhattan',
                   'Union Square, Manhattan']


cusine_counters = []

# for each cuisine
for cuisine in cuisines:
    cuisine_counter = 0
    # do two passes for each neighbourhood with offset 
    for i in range(0, 4):
        for neighbourhood in manhattan_neighbourhoods:
            try:
                response = search(API_KEY, cuisine, neighbourhood, i * 50)
                business_data = response['businesses']
                businesses = handle_response(business_data, cuisine)
                push_data(businesses)  
                cuisine_counter += len(businesses)
            except:
                print(response)
    # print(cuisine, cuisine_counter)
    cusine_counters.append({'cuisine':cuisine, 'count':cuisine_counter})

print(cusine_counters)
