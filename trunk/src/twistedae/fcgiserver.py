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


def log_traceback():
    s = StringIO.StringIO()
    traceback.print_exc(file=s)
    logging.error(s.getvalue())


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
    sys.path.append(app_root)

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

            sys.stdin = inp
            sys.stdout = out
            sys.stderr = err

            # Initialize application environment
            orig_env = dict(os.environ)
            os.environ.clear()
            os.environ.update(env)
            os.environ['APPLICATION_ID'] = conf.application
            os.environ['SERVER_SOFTWARE'] = 'TwistedAE/0.1.0'
            os.environ['TZ'] = 'UTC'

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
            finally:
                del sys.modules
                sys.modules = dict(modules)

            # Restore original environment
            os.environ.clear()
            os.environ.update(orig_env)

            try:
                fcgiapp.Finish()
            except:
                log_traceback()
    except:
        log_traceback()


if __name__ == "__main__":
    main()
