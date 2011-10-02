import urllib.request
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor,Request,HTTPRedirectHandler
from http.cookiejar import FileCookieJar
import json

class RedirectLogger(HTTPRedirectHandler):
    '''This bullshit is needed in order to know EXACT urls, e.g. with #anchors
    Needed to get access token'''
    def __init__(self):
        self.urls=[]
    def redirect_request(self,req,fp,code,msg,hdrs,newurl):
        self.urls.append(newurl)
        return Request(newurl)

class API(object):

    _api_url='https://api.vk.com'
    _request_url=_api_url+'/method/%s?access_token=%s&%s'
    _authorize_url=_api_url+'/oauth/authorize'
    
    def __init__(self,app,cookie_jar='cookies.dat'):
        setts={'redirect_uri':'http://api.vk.com/blank.html',
                   'display':'wap',
                   'response_type':'token'}
        setts.update(app)
        self._app_settings=setts
        jar=FileCookieJar(cookie_jar)
        self.logger=RedirectLogger()
        self.opener=urllib.request.build_opener(HTTPCookieProcessor(jar),
                                                self.logger)
        self._access_token=None
        self._authorized=False

    def authorize(self,user_settings):
        self._authorized=False
        url='%s?%s' % (self._authorize_url,urlencode(self._app_settings))
        req=Request(url)
        resp=self.opener.open(req)
        html=resp.read().decode('utf-8')

        form='<form method="POST" action="'
        i=html.find(form)+len(form)
        k=html.find('"',i)
        url=html[i:k]

        params=['q','from_host','ip_h','to']
        vals={}
        for p in params:
            inp='name="%s" value="' % p
            i=html.find(inp,k)+len(inp)
            k=html.find('"',i)
            vals[p]=html[i:k]
        vals.update(user_settings)
        resp=self.opener.open(url,data=urlencode(vals).encode('utf-8'))
        url=self.logger.urls[-1]
        if url.startswith(self._authorize_url):
            # granting permissions to our app
            html=resp.read().decode('utf-8')
            i=html.find(form)+len(form)
            k=html.find('"',i)
            url=self._api_url+html[i:k]
            resp=self.opener.open(url,data=urlencode({}).encode('utf-8'))
            #print('granted',resp.geturl(),resp.read().decode('utf-8'))
            url=self.logger.urls[-1]
        anchor='#access_token='
        i=url.find(anchor)+len(anchor)
        k=url.find('&',i)
        self._access_token=url[i:k]
        self.logger.urls=[]
        self._authorized=True

    def _request(self,method,**args):
        url=self._request_url % (method,self._access_token,urlencode(args))
        return self.opener.open(url).read().decode('utf-8')
    
    def wall_get(self,owner_id,group=False):
        if group:
            owner_id=-owner_id
        text=self._request('wall.get',owner_id=owner_id)
        return json.loads(text)['response']

    def get_profiles(self,uids,fields=None):
        params={'uids':','.join(uids)}
        if fields is not None:
            params['fields']=','.join(fields)
        text=self._request('getProfiles',**params)
        return json.loads(text)['response']
