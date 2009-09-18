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
"""FastCGI script to serve a CGI application."""

import StringIO
import fcgiapp
import logging
import os
import re
import runpy
import sys
import time
import traceback
import twistedae
import twistedae.handlers.login


def get_traceback():
    """Writes traceback to log file and returns it for printing."""

    s = StringIO.StringIO()
    traceback.print_exc(file=s)
    logging.error(s.getvalue())
    return s.getvalue()


def main():
    """Initializes the server."""

    # Setting the time zone
    os.environ['TZ'] = 'UTC'
    time.tzset()

    logging.basicConfig(
        format='%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s] '
               '%(message)s',
        level=logging.INFO, filename='var/log/appserver.log')

    app_root = os.environ['APP_ROOT']
    os.chdir(app_root)
    sys.path.insert(0, app_root)

    conf = twistedae.getAppConfig()

    url_mapping = twistedae.initURLMapping(conf)

    twistedae.setupStubs(conf)

    if os.environ.get('RESTRICTED_PYTHON', 'false').lower() == 'true':
        [twistedae.RestrictedImportHook.add(m) for m in
         twistedae.RESTRICTED_MODULES]
        restricted_names = twistedae.RESTRICTED_NAMES
        sys.meta_path = [twistedae.RestrictedImportHook(),
                         twistedae.DisallowExtensionsImportHook()]
    else:
        restricted_names = dict()

    try:
        while True:
            (inp, out, err, env) = fcgiapp.Accept()

            orig_stdin = sys.stdin
            orig_stdout = sys.stdout
            orig_stderr = sys.stderr
            sys.stdin = inp
            sys.stdout = out
            sys.stderr = err

            # Initialize application environment
            orig_env = dict(os.environ)
            os.environ.clear()
            os.environ.update(env)
            os.environ['APPLICATION_ID'] = conf.application
            os.environ['AUTH_DOMAIN'] = 'localhost'
            os.environ['SERVER_SOFTWARE'] = 'TwistedAE/0.1.0'
            os.environ['TZ'] = 'UTC'

            # Get user info and set the user environment variables
            email, admin, user_id = twistedae.handlers.login.getUserInfo(
                os.environ.get('HTTP_COOKIE', None))
            os.environ['USER_EMAIL'] = email
            if admin:
                os.environ['USER_IS_ADMIN'] = '1'
            os.environ['USER_ID'] = user_id

            # Evaluate script path and set PATH_TRANSLATED environment
            # variable
            for pattern, name, script in url_mapping:
                if re.match(pattern, os.environ['PATH_INFO']) is not None:
                    os.environ['PATH_TRANSLATED'] = script
                    break

            modules = dict(sys.modules)

            for m in twistedae.RESTRICTED_MODULES:
                if m in sys.modules:
                    del sys.modules[m]

            if hasattr(sys, 'path_importer_cache'):
                sys.path_importer_cache.clear()

            try:
                # Load and run the application module
                mod = runpy.run_module(
                    name,
                    init_globals=restricted_names,
                    run_name='__main__')
            except:
                print 'Content-Type: text/plain\n'
                print get_traceback()
            finally:
                sys.modules.clear()
                sys.modules.update(modules)

                # Restore original environment
                sys.stdin = orig_stdin
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr
                os.environ.clear()
                os.environ.update(orig_env)

                fcgiapp.Finish()
    except:
        get_traceback()


if __name__ == "__main__":
    main()
