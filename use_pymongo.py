# pip install pymongo

from pymongo import MongoClient
from pprint import pprint

client = MongoClient('127.0.0.1', 27017)    #Creating client connected to database
db = client['users']     #Using database users
db2 = client['users2']   #We can use 2 or more dbs

user_names = db.users    #using collerction
user_contacts = db.contacts   #using one more collection

Create methods
user_names.insert_one({'name': 'Ivan',
                  'surname': 'Ivanov'})     # insert one document

user_names.insert_many([{'name': 'Ivan',
                         'surname': 'Ivanov',
                         'age' : 30},
                        {'name': 'Ivan',
                         'surname': 'Ptrov',
                         'age' : 20},
                        {'name': 'Michail',
                         'surname': 'Sidorov',
                         'age' : 35}])    # insert list of documents

Read methods

for user in user_names.find({}):
    pprint(user)         #show all results, like select *

for user in user_names.find({'$or' : [{'name' : 'Ivan'}, {'surname': 'Ptrov'}]}):
    pprint(user)        # using filters with operators

for user in user_names.find({'age' : {'$lte' : 30}}):
    pprint(user)

for user in user_names.find({'age' : {'$lte' : 30}}).sort('surname', -1):
    pprint(user)         # sorting values by (surname,  vice versa)

for user in user_names.find({'name': 'Ivan'}, {'surname':1, 'age':1}):
    pprint(user)       # showing only age and surname (if we don't use '_id':0 - it will be shown automatically)

for user in user_names.find({'name': 'Ivan'}).limit(3):
    pprint(user)         # limit the output to 3 results

for user in user_names.find({'salary'.0}):    # if we have [], take an element with 0 index
    pprint(user)

for user in user_names.find({'age'.min_age}):
    pprint(user)


Update methodd

user_names.update_many()
user_names.update_one({'name' : 'Ivan'}, {'$set': {'name' : 'Vanya'}})

doc = {'name' : 'Katya',
       'surname': 'Sokolova',
       'age' : 30}


user_names.update_one({'_id' : "ObjectId('600ad9c0ec8c0dfa98f236f5')"}, {'$set': doc})
user_names.update_one({'_id' : "ObjectId('600ad9c0ec8c0dfa98f236f5')"}, {'$unset': 'age'})

user_names.replace_one({'name' : 'Vanya'}, doc)
for user in user_names.find({'name' : 'Katya'}):
    pprint(user)


Delete methodd

user_names.delete_one({'name' : 'Ivan'})
for user in user_names.find({}):
    pprint(user)

user_names.delete_many({})
for user in user_names.find({}):
    pprint(user)