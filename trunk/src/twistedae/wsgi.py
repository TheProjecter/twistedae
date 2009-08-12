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
"""WSGI Resource implementation."""

import logging

from twisted.web.server import NOT_DONE_YET
from twisted.web.wsgi import _ErrorStream, _InputStream, _WSGIResponse
from twisted.web.wsgi import WSGIResource as BaseWSGIResource


class WSGIResponse(_WSGIResponse):
    """Customized WSGI response implementation."""

    def __init__(self, reactor, threadpool, application_name, request):
        """Initializes the response."""

        _WSGIResponse.__init__(self, reactor, threadpool, None, request)
        self.application_name = application_name

    def run(self):
        """Reloads and calls the WSGI application object.

        This must be called in a non-I/O thread (ie, a WSGI application
        thread).
        """
        mod = __import__(self.application_name)
        reload(mod)
        app = getattr(mod, self.application_name)
        appIterator = app(self.environ, self.startResponse)
        logging.debug("%s" % app)
        for elem in appIterator:
            if elem:
                self.write(elem)
        close = getattr(appIterator, 'close', None)
        if close is not None:
            close()
        if self.started:
            def wsgiFinish():
                self.request.finish()
            self.reactor.callFromThread(wsgiFinish)
        else:
            def wsgiSendResponseHeadersAndFinish():
                self._sendResponseHeaders()
                self.request.finish()
            self.started = True
            self.reactor.callFromThread(wsgiSendResponseHeadersAndFinish)


class WSGIResource(BaseWSGIResource):
    """WSGI Resource implementation."""

    def render(self, request):
        """
        Turn the request into the appropriate C{environ} C{dict} suitable to be
        passed to the WSGI application object and then pass it on.

        The WSGI application object is given almost complete control of the
        rendering process.  C{NOT_DONE_YET} will always be returned in order
        and response completion will be dictated by the application object, as
        will the status, headers, and the response body.
        """
        response = WSGIResponse(
            self._reactor, self._threadpool, self._application, request)
        response.start()
        return NOT_DONE_YET

__all__ = ['WSGIResource']
