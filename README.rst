======
vk2rss
======
app for grabbing posts from VK wlls and post to twitter
uses self written VK client library, patched python-twitter, patched python-oauth2(depends on httplib2).
needs myconfig.py with confs of VK app and twitter settings

*myconfig* should contain something like this:

app_settings = {
  'client_id': 0,
  'scope': 0
}

user_settings = {
  'email': '',
  'pass': ''
}

twitter_settings = {
  'consumer_key': '',
  'consumer_secret': '',
  'access_token_key': '',
  'access_token_secret': ''
}

group_id = 0
