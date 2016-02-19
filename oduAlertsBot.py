'''
/u/sadistmushroom\'s ODU Alerts v0.3
by Tristan Pressley tpres008@odu.edu
V0.3 2016-2-17
Much of the code here is taken from the Gmail API reference and Gmail quickstart python program
Uses PRAW 3.3.0
'''
from __future__ import print_function
import httplib2
import os
import base64
import binascii
import time 
import praw 

from apiclient import discovery
from apiclient import errors
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'YourSecretFileHere.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

def ListMessagesMatchingQuery(service, user_id, query=''):
  """List all Messages of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
    Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

  Returns:
    List of Messages that match the criteria of the query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate ID to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               q=query,maxResults=5).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    '''while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query).execute()
      messages.extend(response['messages'])'''

    return messages
  except errors.HttpError, error:
    print ('An error occurred: %s' % error)

def decode_base64(data):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    #missing_padding = 4 - len(data) % 4
    #if missing_padding:
    #   data += b'='* missing_padding
    return base64.decodestring(data)

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    me = "me"
    subredditName = 'libertybot' #name of the subreddit to post to
    print("Please enter subreddit to post to:")
    subredditName = raw_input() 
    postIdFile = open("postedIds.txt", 'r+')
    r = praw.Reddit('/u/sadistmushroom\'s ODU Alerts v0.3')
    r.login(disable_warning='true')  #Login prompt for the reddit bot
    subreddit = r.get_subreddit(subredditName) 
    bodyText = ""  # Stores body text of the email
    submissionTitle = ""  # Stores submission title 
    already_done = []     # Lists id's of emails already posted
    for line in postIdFile:                 ##  Adds ids of previously posted emails into already_done 
        already_done.append(line.rstrip())  ##
        print(line)                         ##


    credentials = get_credentials()                                          ## Prepare gmail API 
    http = credentials.authorize(httplib2.Http())                            ##
    service = discovery.build('gmail', 'v1', http=http)                      ##
    messages = ListMessagesMatchingQuery(service,'me','odualerts@odu.edu')   ##

    while True: # Loop indefinitely
        if not messages:                  # No messages in the email acct
            print('No messages found.')
        else:
            print('Messages:')
            for message in messages:
                if message is not 'nextPageToken': # Probably unnecessary, makes sure that a page token is not mistaken for a message
                    msg = service.users().messages().get(userId=me, id=message['id']).execute() #gets the selected message from the list of all messages
                    if (msg['id'] not in already_done): #ensure that the message has not already been posted
                        already_done.append(msg['id'])  #add the messsage's id to already_done
                        postIdFile.write(msg['id'] + "\n") #add the message's id to the id file
                        try:
                            #print ("==============This msg would now be posted to reddit===================") ##for debugging purposes only
                            for header in (msg['payload']['headers']):  ##
                                if header['name'] == 'Subject':         ##
                                    subject = header['value']           ## Get the email subject
                                    break
                            print (subject)
                            bodyText = decode_base64(msg['payload']['parts'][0]['body']['data'])  ##Decode the message from base64, print to screen and prepare it for posting
                            submissionTitle = subject
                            r.submit(subreddit,submissionTitle, text=bodyText, url=None,captcha=None,send_replies=None,resubmit=None) #submit the post
                            break  ##Break the current message list loop
                        except binascii.Error:
                            print ("no correct base64")  ##Only happens if the data is corrupted or if the selected item is not encoded in base64 (and therefore is not a message)
        time.sleep(600) # Sleep 10 minutes


    

if __name__ == '__main__':
    main()


