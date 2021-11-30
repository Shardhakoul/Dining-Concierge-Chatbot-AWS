# AWS Dining Concierge chatbot

## Description:-
"Dining Concierge Chatbot" is a serverless, microservice driven web-based application. It is an intelligent natural language powered chat-bot that is designed using multiple AWS components such as :-

AWS Lex, S3-Buckets, API-Gateway, Swagger, Lambda Functions, Cognito, DynamoDB, SQS, Cloud Watch and Elastic Search.
This chatbot can help you provide restaurant suggestions based on your requirements such as - City, Time, Number of people, Cuisine Type and Date. The bot uses the yelp API to fetch relevant suggestions and mails the suggestions on the email-id that the user provides.

## Architecture Diagram:-
![image](https://user-images.githubusercontent.com/85691194/136668983-b981a831-4cd8-4fea-a818-bf81a7c2efcf.png)

## AWS Services used:
- S3
- API Gateway
- Lambda
- Lex
- SQS
- SNS
- DynamoDB
- ElasticSearch

## Example Interaction

User: Hello  
Bot: Hi there, how can I help?  
User: I need some restaurant suggestions  
Bot: Great. I can help you with that.What city or city area are you looking to dine in?  
User: Manhattan  
Bot: Got it, Manhattan. What cuisine would you like to try?  
User: Japanese  
Bot: Ok, how many people are in your party?  
User: Two  
Bot: A few more to go. What date?  
User: Today  
Bot: What time?  
User: 7 pm, please  
Bot: Great. Lastly, I need your phone number so I can send you my findings.  
User: 123-456-7890  
Bot: You’re all set. Expect my suggestions shortly! Have a good day.   
User: Thank you!   
Bot: You’re welcome.  
(a few minutes later)  
User gets the following text message:  
“Hello! Here are my Japanese restaurant suggestions for 2 people, for today at 7 pm: 1. Sushi Nakazawa, located at 23 Commerce St, 2. Jin Ramen, located at 3183 Broadway, 3. Nikko, located at 1280 Amsterdam Ave. Enjoy your meal!”
