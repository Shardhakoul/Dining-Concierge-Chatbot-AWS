import math
import dateutil.parser
import datetime
import time
import os
import logging
import re
import boto3
import json
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# connect to the dynamoDB table
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('restaurantSuggestionStore')

# this code is modified from the lex orderFlowers getting started guide on AWS

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

# read the lex event and get the slots


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

# function to invoke the slot


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

# function to say intent is fulfilled and give response


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

# function to delegate the slots


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """

# convert int to float


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

# check if date is valid


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

# check if email is valid


def isvalid_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

# check if the messages are valid(not empty)


def build_validation_result(is_valid, violated_slot, message_content):
    # if no message should be shown
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    # return violated slot and the message to be displayed
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

# function to validate the dining suggestion request


def validate_dining_suggestion(cuisine, number_of_people, date, time, location, email):

    # list of cuisines
    cuisines = ['indian', 'italian', 'chinese', 'vietnamese', 'mexican',
                'french', 'thai', 'burmese', 'japanese', 'persian', 'turkish']

    # if cuisine is not in the list, then return message
    if cuisine is not None and cuisine.lower() not in cuisines:
        return build_validation_result(False,
                                       'CuisineType',
                                       'We do not have that cuisine, can you please try another?')

    # make sure number of people is not less than 0 or greater than 20
    if number_of_people is not None:
        number_of_people = int(number_of_people)
        if number_of_people > 20:
            return build_validation_result(False,
                                           'NumberOfPeople',
                                           'Only a maximum 20 people are allowed to dine, please try again.')
        elif number_of_people < 0:
            return build_validation_result(False,
                                           'NumberOfPeople',
                                           'There cannot be less than zero people dining, please try again.')

    # check if date is valid
    if date is not None:
        if (isvalid_date(date) == False):
            return build_validation_result(False,
                                           'Date',
                                           'I did not understand that, what date would you like to go dining?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(True, 'Date', 'Great, you can go dining on {}.'.format(date))

    # check if the time is valid
    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', 'Not a valid time, please try again.')

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', 'Not a valid time, please try again.')

        if hour < 10 or hour > 16:
            # Outside of business hours
            return build_validation_result(False, 'Time', 'Our working hours are from 10am to 5pm, please specify a time in this interval.')

    # check if the location is valid
    if location is not None:
        if len(location) < 1:
            return build_validation_result(False, 'Location', 'Not a valid location, please try again.')

    # check if the email is valid
    if email is not None:
        if (isvalid_email(email) == False):
            return build_validation_result(False,
                                           'Email',
                                           'This was not a valid email, please try again.')

    return build_validation_result(True, None, None)


# functions to handle the different intents

# handle the greeting intent
def handle_greeting_intent(event):
    response = table.query(KeyConditionExpression=Key('identity').eq('1'))
    data = response['Items'][0]
    suggestions = data['suggestions']
    status = data['isFirstTime']

    if not status:
        # compose message to return
        return {
            'dialogAction': {
                "type": "ElicitIntent",
                'message': {
                    'contentType': 'PlainText',
                    'content': 'Hi there, how can I help?'}
            }
        }
    else:
        return {
            'dialogAction': {
                "type": "ElicitIntent",
                'message': {
                    'contentType': 'PlainText',
                    'content': 'Welcome back! Here are your previous suggestions! ' + suggestions}
            }
        }


# handle the thank you intent
def handle_thankyou_intent(event):
    # compose message to return
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText',
                'content': 'You are welcome!'}
        }
    }

# handle the dining suggestion intent


def handle_dining_suggestion_intent(event):
    invocation_source = event['invocationSource']

    slots = get_slots(event)
    location = slots["Location"]
    cuisine = slots["Cuisine"]
    number_of_people = slots["NumberOfPeople"]
    date = slots["Date"]
    time = slots["Time"]
    email = slots["Email"]
    # phone = slots["Phone"]

    if invocation_source == 'DialogCodeHook':
        # slots = get_slots(event)
        validation_result = validate_dining_suggestion(
            cuisine, number_of_people, date, time, location, email)

        if validation_result['isValid'] == False:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(event['sessionAttributes'],
                               event['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        if event['sessionAttributes'] is not None:
            output_session_attributes = event['sessionAttributes']
        else:
            output_session_attributes = {}

        return delegate(output_session_attributes, get_slots(event))

    queue_message = {"cuisine": cuisine, "email": email, "location": location,
                     "cuisine": cuisine, "numberOfPeople": number_of_people, "date": date, "time": time}
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='restaurantRequests')
    response = queue.send_message(MessageBody=json.dumps(queue_message))

    return close(event['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Great! You will receive your suggestion shortly.'})

# lambda handler and dispatching intent funtions

# function to handle the different intents


def dispatch(event):

    logger.debug(
        'dispatch userId={}, intentName={}'.format(event['userId'], event['currentIntent']['name']))

    # get the intent type from event
    intent_type = event['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if (intent_type == 'GreetingIntent'):
        return handle_greeting_intent(event)
    elif(intent_type == 'ThankYouIntent'):
        return handle_thankyou_intent(event)
    elif(intent_type == 'DiningSuggestionsIntent'):
        return handle_dining_suggestion_intent(event)

    raise Exception('Intent with name ' + intent_type + ' not supported')

# function to handle the lex event


def lambda_handler(event, context):
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
