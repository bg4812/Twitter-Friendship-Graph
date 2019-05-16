#Brandon Gardner

import twitter
import functools
import json
import sys
from sys import maxsize
import time
from functools import partial
import networkx as nx
import matplotlib.pyplot as plt
import urllib
import time


def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw): #Got this from the cookbook https://www.oreilly.com/library/view/mining-the-social/9781449368180/ch09.html#Get_all_friends_or_followers_for_a_particular_user
    # A nested helper function that handles common HTTPErrors. Return an updated
    # value for wait_period if the problem is a 500 level error. Block until the
    # rate limit is reset if it's a rate limiting issue (429 error). Returns None
    # for 401 and 404 errors, which requires special handling by the caller.
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):

        if wait_period > 3600:  # Seconds
            print("fatal error", file=sys.stderr) #'Too many retries. Quitting.'
            raise e

        # See https://dev.twitter.com/docs/error-codes-responses for common codes

        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)', file=sys.stderr),
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)', file=sys.stderr),
            return None
        elif e.e.code == 429:
            print('Encountered 429 Error (Rate Limit Exceeded)', file=sys.stderr),
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...ZzZ...", file=sys.stderr),
                sys.stderr.flush()
                time.sleep(60 * 15+5)
                print('...ZzZ...Awake now and trying again.', file=sys.stderr),
                return 2
            else:
                raise e  # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered Error. Retrying in _ seconds', file=sys.stderr)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function

    wait_period = 2
    error_count = 0

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError as e:
            error_count = 0
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return

        except urllib.request.URLError as e:
            error_count += 1
            print("URLError encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
        except BadStatusLine as e:
            error_count += 1
            print("BadStatusLine encountered. Continuing.",file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.",file=sys.stderr)
                raise


def get_user_profile(twitter_api, screen_names=None, user_ids=None): #Got this from the cookbook https://www.oreilly.com/library/view/mining-the-social/9781449368180/ch09.html#Get_all_friends_or_followers_for_a_particular_user
    # Must have either screen_name or user_id (logical xor)
    assert (screen_names != None) != (user_ids != None), \
        "Must have screen_names or user_ids, but not both"

    items_to_info = {}

    items = screen_names or user_ids

    while len(items) > 0:

        # Process 100 items at a time per the API specifications for /users/lookup.
        # See https://dev.twitter.com/docs/api/1.1/get/users/lookup for details.

        items_str = ','.join([str(item) for item in items[:100]])
        items = items[100:]

        if screen_names:
            response = make_twitter_request(twitter_api.users.lookup,
                                            screen_name=items_str)
        else:  # user_ids
            response = make_twitter_request(twitter_api.users.lookup,
                                            user_id=items_str)
    if response is not None: #trying to handle Nonetype error
        for user_info in response:
            if screen_names:
                items_to_info[user_info['screen_name']] = user_info
            else:  # user_ids
                items_to_info[user_info['id']] = user_info

    return items_to_info



#returns friends arguement must be screen name
def getFriendsn(screen_name,twitter_api):
    R1=twitter_api.friends.ids(screen_name=screen_name, count=1000)
    friends = R1["ids"]
  #  print('got {0} friends for {1}'.format(len(friends), screen_name))
    return friends
#returns friends arguement must be a id
def getFriendsi(id,twitter_api):
    R1=twitter_api.friends.ids(user_id=id, count=1000)
    friends = R1["ids"]
   # print('got {0} friends for {1}'.format(len(friends), id))
    return friends

#returns followers arguement must be screen name
def getFollowersn(screen_name,twitter_api):
    R=twitter_api.followers.ids(screen_name=screen_name, count=1000)
    followers = R["ids"]
  #  print('got {0} followers for {1}'.format(len(followers), screen_name))
    return followers
#returns followers arguement must be id
def getFollowersi(id,twitter_api):
    R=twitter_api.followers.ids(user_id=id, count=1000)
    followers = R["ids"]
   # print('got {0} followers for {1}'.format(len(followers), id))
    return followers

#returns reciprocal friends arguement must be screen name
def getReciprocalFriendsn(screen_name,twitter_api):
    friends=getFriendsn(screen_name,twitter_api)
    followers=getFollowersn(screen_name,twitter_api)
    reciprocal_friends = set(friends) & set(followers)
   # print('got {0} reciprocal friends for {1}'.format(len(reciprocal_friends), screen_name))
    return reciprocal_friends
#returns reciprocal friends arguement must be id
def getReciprocalFriendsi(id,twitter_api):
    friends=getFriendsi(id,twitter_api)
    followers=getFollowersi(id,twitter_api)
    reciprocal_friends = set(friends) & set(followers)
   # print('got {0} reciprocal friends for {1}'.format(len(reciprocal_friends), id))
    return reciprocal_friends
#returns The five most popular friends based on folower count arguement must be screen name
def getMostPopFriendsn(screen_name,twitter_api):
    RF=getReciprocalFriendsn(screen_name,twitter_api)
    l = list(RF) # list of reciprocal friends ids
    followerCounts = []  # follower counts of all reciprocal friends
    mostPopularFriends = []  # most popular friends ids
    mostFollowerCount = []  # the highest followers count values
    # get all the follower counts of reciprocal friends
    for item in l:
        data = get_user_profile(twitter_api, user_ids=[item])
        fc = (data[item]['followers_count'])
        print(fc)
        followerCounts.append(fc)
    #print(followerCounts)
    # create a dictionary with the key as screen name and value as follower count
    dictionary = dict(zip(followerCounts, RF))
    # sort the list of reciprocal friends follower counts
    followerCounts.sort(reverse=True)
    #print(followerCounts)

    mostFollowerCount.append(followerCounts[0:5])
    #print(mostFollowerCount)
    #print(dictionary)

    # print the 5 people with the maximum follow count
    try:
        for i in range(5):
            mostPopularFriends.append(dictionary[mostFollowerCount[0][i]])
    except IndexError:
        print('Not enough reciprocal friends')
    print(mostPopularFriends)
    return mostPopularFriends
#returns The five most popular friends based on folower count arguement must be id
def getMostPopFriendsi(id,twitter_api):
    RF=getReciprocalFriendsi(id,twitter_api)
    l = list(RF) # list of reciprocal friends ids
    followerCounts = []  # follower counts of all reciprocal friends
    mostPopularFriends = []  # most popular friends ids
    mostFollowerCount = []  # the highest followers count values
    # get all the follower counts of reciprocal friends
    for item in l:
        data = get_user_profile(twitter_api, user_ids=[item])
        try:
            fc = (data[item]['followers_count'])
        except KeyError:
            print("Key not found")
       # print(fc)
        followerCounts.append(fc)
    #print(followerCounts)
    # create a dictionary with the key as screen name and value as follower count
    dictionary = dict(zip(followerCounts, RF))
    # sort the list of reciprocal friends follower counts
    followerCounts.sort(reverse=True)
    #print(followerCounts)

    mostFollowerCount.append(followerCounts[0:5])
    #print(mostFollowerCount)
    #print(dictionary)

    # print the 5 people with the maximum follow count

    try:
        for i in range(5):
            mostPopularFriends.append(dictionary[mostFollowerCount[0][i]])
            #not enough friennds to go through
    except IndexError:
        print('Not enough reciprocal friends')
    print(mostPopularFriends)
    return mostPopularFriends
# Go to http://dev.twitter.com/apps/new to create an app and get values
# for these credentials, which you'll need to provide in place of these
# empty string values that are defined as placeholders.
# See https://developer.twitter.com/en/docs/basics/authentication/overview/oauth
# for more information on Twitter's OAuth implementation.

CONSUMER_KEY = 'u9CeAFvjEXTuncWZlF0sPPz7K'
CONSUMER_SECRET = 'MLa1J9F3RZmaYXVTHClPbnSN25JOw6K1AReJePMS4eW1mSvXz9'
OAUTH_TOKEN = '3070550111-VSWLUhZHeAuIEjOwhvj6mt4ZB3FyL7CGMeOYedL'
OAUTH_TOKEN_SECRET = 'XSso1xhOOeaXxfitEGAMm5BJsQhEhZC47hZnQaFKZxHoZ'

auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,CONSUMER_KEY, CONSUMER_SECRET)

twitter_api = twitter.Twitter(auth=auth)


#print(twitter_api)


#starting point using twitter name bg4812
screen_name='Bg_4812'
response=twitter_api.users.show(screen_name=screen_name)
#print(json.dumps(response, sort_keys=True, indent=1))
queue=[]

friendship= nx.Graph()

queue.append(screen_name)

F1=getMostPopFriendsn(screen_name,twitter_api)
starting_point=queue.pop(0)
#make starting Node
friendship.add_node(starting_point)


for i in range(len(F1)):
    queue.append(F1[i])
    friendship.add_node(F1[i])
    friendship.add_edge(F1[i],starting_point)

    count = 0

    # while on level 1 =1
    # while on level 2 =6 iterations
    # while on level 3 =31interations
while queue: #while queue not empty
    count += 1
    print('Count :')
    print(count)
    time.sleep(60)  #delay to prevent reaching api limit
    popVal=queue.pop(0)
    MPF=getMostPopFriendsi(popVal,twitter_api)
    if isinstance(MPF, list):        #if the most popular friends are in a list
        for i in range(len(MPF)):    #take every element in the list and put it into the queue
            queue.append(MPF[i])
            friendship.add_node(MPF[i])
            friendship.add_edge(MPF[i],popVal)
             #time.sleep(3)
    else:
        queue.append(MPF)
    if count == 3:
        break




#print(queue)
#friendship.add_edge(starting_point,2)
print('The Diameter of the network is:')
print(nx.diameter(friendship))
nodeVal=len(friendship.nodes)
edgesVal=len(friendship.edges)
WI=nx.wiener_index(friendship)
numerator=nodeVal*(nodeVal-1)
average_distance=numerator/WI
print('The amount of nodes is :')
print(nodeVal)
print('The amount of edges is :')
print(edgesVal)
print('The average distance of the network is :')
print(average_distance)
nx.draw(friendship,with_labels=True)
plt.show(friendship)













