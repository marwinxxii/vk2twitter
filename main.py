import pickle
import os.path
import time

import twitter

import vk
from myconfig import *

class Sender(vk.API):
    
    def __init__(self, app, cookie_jar='cookies.dat'):
        vk.API.__init__(self, app, cookie_jar=cookie_jar)
        self._handlers = []
        self.users_cache = {}

    def add_handler(self, handler):
        if hasattr(handler, 'send'):
            self._handlers.append(handler.send)
        else:
            self._handlers.append(handler)

    def wall_get(self, owner_id, group=True, since=None):
        posts = vk.API.wall_get(self, owner_id, group=True)
        if since is None:
            for post in posts[1:]:
                for h in self._handlers:
                    h(self, post)
        else:
            for post in posts[1:]:
                if post['date'] < since:
                    continue
                for h in self._handlers:
                    h(self, post)
        return posts

    def get_profile(self, uid, fields=None):
        if uid in self.users_cache:
            return self.users_cache[uid]
        else:
            u = vk.API.get_profiles(self, (str(uid),), fields)[0]
            self.users_cache[uid] = u
            return u

def strip_text(text):
    return text.replace('<br>', '\n').replace('#twitter', '')

class TwitterSender(object):
    
    def __init__(self, settings):
        self._api = twitter.Api(**settings)
    
    def send(self, api, post):
        if '#twitter' not in post['text']:
            return None
        u = api.get_profile(post['from_id'], ('first_name','last_name'))
        mes = '%s. %s: %s' % (u['first_name'][0],
                              u['last_name'],
                              strip_text(post['text'])
                              )
        link = ' http://vk.com/wall%s_%s' % (post['to_id'],post['id'])
        if len(mes) + len(link) > 140:
            mes = mes[:140-len(link)]
        mes += link
        status = self._api.PostUpdate(mes)
        #print(status.text)

if __name__ == '__main__':
    api = Sender(app_settings)
    api.authorize(user_settings)
    api.add_handler(TwitterSender(twitter_settings))
    if os.path.exists('state.dat'):
        with open('state.dat', 'rb') as f:
            state = pickle.load(f)
        api.users_cache = state['users_cache']
        api.wall_get(group_id, since=state['last_run'])
    else:
        state = {}
        api.wall_get(group_id)
    with open('state.dat', 'wb') as f:
        state['users_cache'] = api.users_cache
        state['last_run'] = time.mktime(time.localtime())
        pickle.dump(state, f)
#todo: catch KeyBoardInterrupt
