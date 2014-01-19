import sqlite3
import urlparse
import urllib
import httplib2
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.notestore.NoteStore as NoteStore
from evernote.api.client import EvernoteClient
from evernote.edam.type.ttypes import Publishing

import oauth2 as oauth
from flask import Flask, session, redirect, url_for, request,render_template, flash


app = Flask(__name__)
APP_SECRET_KEY = 'MHACKS'
CONSUMER_KEY='dineshdommaraju'
CONSUMER_SECRET='07dae2d2c309c6a6'

EN_REQUEST_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
EN_ACCESS_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
EN_AUTHORIZE_URL = 'https://sandbox.evernote.com/OAuth.action'
status=" "


def get_oauth_client(token=None):
    consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
    if token:
       
       client = oauth.Client(consumer, token)
    else:
        
    	client = oauth.Client(consumer)
    return client

@app.route('/auth')
def auth_start():
    print "test_auth"
    client = get_oauth_client()
    callback_url = 'http://%s%s' % ('127.0.0.1:5000', url_for('auth_finish'))
    request_url = '%s?oauth_callback=%s' % (EN_REQUEST_TOKEN_URL,
        urllib.quote(callback_url))
    
    
    resp, content = client.request(request_url, 'GET')
    
    if resp['status'] != '200':
    	raise Exception('Invalid response %s.' % resp['status'])
    request_token = dict(urlparse.parse_qsl(content))
    session['oauth_token'] = request_token['oauth_token']
    session['oauth_token_secret'] = request_token['oauth_token_secret']

    return redirect('%s?oauth_token=%s' % (EN_AUTHORIZE_URL,
        urllib.quote(session['oauth_token'])))

@app.route('/notebook')
def default_notbook():
    authToken = session['identifier']
    client=EvernoteClient(token=authToken)
    noteStore = client.get_note_store()
    notebooks = noteStore.listNotebooks(authToken)
    print notebooks
    for notebook in notebooks:
        defaultNotebook = notebook
        break
    
    return defaultNotebook.name

@app.route('/authComplete')
def auth_finish():
    
    oauth_verifier = request.args.get('oauth_verifier', '')
    token = oauth.Token(session['oauth_token'], session['oauth_token_secret'])
    token.set_verifier(oauth_verifier)

    client = get_oauth_client()
    client = get_oauth_client(token)
    resp, content = client.request(EN_ACCESS_TOKEN_URL, 'POST')

    if resp['status'] != '200':
        raise Exception('Invalid response %s.' % resp['status'])

    access_token = dict(urlparse.parse_qsl(content))
    authToken = access_token['oauth_token']
    client=EvernoteClient(token=authToken)

    userStore=client.get_user_store()
    user=userStore.getUser()
    
    session['shardId'] = user.shardId
    session['identifier'] = authToken
    return redirect('/')

@app.route('/login')
def disp_login():
    return redirect('/auth')

@app.route('/select')
def get_select():
    authToken = session['identifier']
    
    client=EvernoteClient(token=authToken)
    userStore=client.get_user_store()
    noteStore = client.get_note_store()
    notebook = noteStore.getNotebook(authToken,'f8df2681-403f-4019-b249-84a2e60ce609')
    print notebook
    #make the notes public
    notebook.published = True

    notebook.publishing = Publishing()
    notebook.publishing.uri = "algorithms"
    notebook.publishing.publicDescription = "My default notebook is public!"
    noteStore.updateNotebook(notebook)
    notebookUrl = "https://%s/pub/%s/%s/" % \
                (client.service_host, 
                 userStore.getUser().username,
                 notebook.publishing.uri)

    
                 
    print "View this notebook:",
    print notebookUrl
    print "----------------------------" 
    
    #generate the tags for the notebook.

    notebook_tags=[]
    notebook_tags=noteStore.listTagsByNotebook(authToken,'f8df2681-403f-4019-b249-84a2e60ce609')
    #connect to the database
    conn = sqlite3.connect('Evernote.db')
    c = conn.cursor()

    #check if the tag already exists
    
    for tag in notebook_tags:
        
        row=c.execute(' select * from UNIQUETAG where TAGNAME=(?)', (tag.name,))
        
        print row
        if row:
            #new tag, thus insert into the table.
            c.execute("insert into  UNIQUETAG values (?)",(tag.name,))
            

    print notebook_tags
    notei=0
    #create unique noteID
    for noteid in c.execute('select max(NODEID) from NODE '):
        print noteid[0]
        if noteid[0] == "None":
            print "test"
            notei=1
            print notei
        else:
            notei=notei+1

    
    #create new entries in the table NODE and TAG table
    thumbsup=0
    thumbsdown=0

    c.execute("insert into NODE values (?,?,?,?,?)",(notebookUrl,notei,notebook.name,thumbsup,thumbsdown))
    for tag in notebook_tags:
        c.execute('insert into TAG values (?,?,?)',(0,notei,tag.name))
        #insert into the TAG table
    
    conn.commit()    
    conn.close()
    return redirect('/')

@app.route('/share', methods=['GET', 'POST'])
def perform_share():

    notebook_list=[]
    notebook_guid=[]
    authToken = session['identifier']
    client=EvernoteClient(token=authToken)
    noteStore = client.get_note_store()
    notebooks = noteStore.listNotebooks(authToken)
    for notebook in notebooks:
        
        notebook_list.append(notebook.name)
        notebook_guid.append(notebook.guid)

    return render_template('landing_share.htm',notebook_list=notebook_list,notebook_guid=notebook_guid)


#changes to be added to here
def search_notebooks():
    conn = sqlite3.connect('Evernote.db')
    c = conn.cursor()
    #tagname : name retrieved from the search tab
    for row in c.execute('select * from NODE inner join TAG on NODE.NODEID = TAG.NODEID where TAGNAME=(?) orderby thumbsup',(tagname)):


@app.route('/', methods=['GET', 'POST'])
def home():
    
    if len(session['identifier'])>0:
        
        return render_template('welcome.htm')
    else:
        return render_template('index.htm')
        return redirect('/auth')

if __name__ == '__main__':
    app.secret_key = APP_SECRET_KEY
    app.run(debug=True)

