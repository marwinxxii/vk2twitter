import urllib.request
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor,Request,HTTPRedirectHandler
from http.cookiejar import FileCookieJar
import json

class RedirectLogger(HTTPRedirectHandler):
    '''This bullshit is needed in order to know EXACT urls, e.g. with #anchors
    Needed to get access token'''
    def __init__(self):
        self.urls = []
    
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        self.urls.append(newurl)
        return Request(newurl)

class API(object):

    _api_url = 'https://api.vk.com'
    _request_url = _api_url + '/method/%s?access_token=%s&%s'
    _authorize_url = _api_url + '/oauth/authorize'

    errors = {'auth': 5}
    
    def __init__(self, app, cookie_jar='cookies.dat', user_settings=None):
        '''app is a dict with client_id and scope(vk access rights).
        '''
        setts = {'redirect_uri': 'http://api.vk.com/blank.html',
                 'display': 'wap',
                 'response_type': 'token'}
        setts.update(app)
        self._app_settings = setts
        jar = FileCookieJar(cookie_jar)
        self.logger = RedirectLogger()
        self.opener = urllib.request.build_opener(HTTPCookieProcessor(jar),
                                                  self.logger)
        self._access_token = None
        self._authorized = False
        self.user_settings = user_settings

    def authorize(self, user_settings):
        '''User settings is a dict with email and pass.
        '''
        self._authorized = False
        url = '%s?%s' % (self._authorize_url, urlencode(self._app_settings))
        req = Request(url)
        resp = self.opener.open(req)
        html = resp.read().decode('utf-8')

        form = '<form method="POST" action="'
        i = html.find(form) + len(form)
        k = html.find('"', i)
        url = html[i:k]

        params = ['q','from_host','ip_h','to']
        vals = {}
        for p in params:
            inp = 'name="%s" value="' % p
            i = html.find(inp, k) + len(inp)
            k = html.find('"', i)
            vals[p] = html[i:k]
        vals.update(user_settings)
        resp = self.opener.open(url, data=urlencode(vals).encode('utf-8'))
        url = self.logger.urls[-1]
        if url.startswith(self._authorize_url):
            # granting permissions to our app
            html = resp.read().decode('utf-8')
            i = html.find(form) + len(form)
            k = html.find('"', i)
            url = self._api_url + html[i:k]
            resp = self.opener.open(url, data=urlencode({}).encode('utf-8'))
            #print('granted',resp.geturl(),resp.read().decode('utf-8'))
            url = self.logger.urls[-1]
        anchor = '#access_token='
        i = url.find(anchor) + len(anchor)
        k = url.find('&', i)
        self._access_token = url[i:k]
        self.logger.urls = []
        self._authorized = True

    def _request(self, method, **args):
        '''Returns dict with body of response or error
        description. Error can be detected by checking existance
        of key "error" in result. Tries to authorize if user_settings
        is not None in case of authorization error.
        '''
        url = self._request_url % (method, self._access_token, urlencode(args))
        text = self.opener.open(url).read().decode('utf-8')
        parsed = json.loads(text)
        if 'response' in parsed:
            return parsed['response']
        else:
            error_desc = parsed['error']
            if error_desc['error_code'] == self.errors['auth']:
                if self.user_settings is not None:
                    self.authorize(self.user_settings)
                    url = self._request_url % (method, self._access_token,
                                               urlencode(args))
                    text = self.opener.open(url).read().decode('utf-8')
                    parsed = json.loads(text)
        return parsed
    
    def wall_get(self, owner_id, group=False):
        if group:
            owner_id = -owner_id
        return self._request('wall.get', owner_id=owner_id)

    def get_profiles(self, uids, fields=None):
        params = {'uids': ','.join(uids)}
        if fields is not None:
            params['fields'] = ','.join(fields)
        return self._request('getProfiles', **params)
