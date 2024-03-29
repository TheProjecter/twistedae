# -*- coding: utf-8 -*-
#
# Copyright 2009 Tobias Rodäbel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Login/logout handler."""

import Cookie
import google.appengine.ext.webapp
import md5
import os
import re
import wsgiref.handlers


def getCookieName():
    """Returns the cookie name.

    To get the appcfg upload_data command work we have to provide the correct
    cookie name for easy authentication.

    TODO: This is a huge security hole and should be fixed for the productive
          environment.
    """

    if os.environ.get('HTTP_X_APPCFG_API_VERSION') == '1':
        return 'dev_appserver_login'
    else:
        return 'twistedae_login'


def getUserInfo(cookie):
    """Get the user info from the HTTP cookie in the CGI environment."""

    c = Cookie.SimpleCookie(cookie)
    cookie_name = getCookieName()
    value = ''
    if cookie_name in c:
      value = c[cookie_name].value

    email, admin, user_id = (value.split(':') + ['', '', ''])[:3]

    return email, (admin == 'True'), user_id


def createLoginCookie(email, admin):
    """Creates cookie payload data for login information."""

    admin_string = 'False'
    if admin:
        admin_string = 'True'
    if email:
        user_id_digest = md5.new(email.lower()).digest()
        user_id = '1' + ''.join(['%02d' % ord(x) for x in user_id_digest])[:20]
    else:
        user_id = ''

    return '%s:%s:%s' % (email, admin_string, user_id)


class LoginRequestHandler(google.appengine.ext.webapp.RequestHandler):
    """Simple login handler."""

    def get(self):
        """Sets the authentication cookie."""

        cookie_name = getCookieName()
        c = Cookie.SimpleCookie()
        c[cookie_name] = createLoginCookie('admin@localhost', admin=True)
        c[cookie_name]['path'] = '/'
        h = re.compile('^Set-Cookie: ').sub('', c.output(), count=1)
        self.response.headers.add_header('Set-Cookie', str(h))
        self.redirect('/')


class LogoutRequestHandler(google.appengine.ext.webapp.RequestHandler):
    """Simple logout handler."""

    def get(self):
        """Removes the authentication cookie."""

        cookie_name = getCookieName()
        c = Cookie.SimpleCookie()
        c[cookie_name] = ''
        c[cookie_name]['path'] = '/'
        c[cookie_name]['max-age'] = '0'
        h = re.compile('^Set-Cookie: ').sub('', c.output(), count=1)
        self.response.headers.add_header('Set-Cookie', str(h))
        self.redirect('/')


app = google.appengine.ext.webapp.WSGIApplication([
    ('/login', LoginRequestHandler),
    ('/logout', LogoutRequestHandler),
], debug=True)


def main():
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
