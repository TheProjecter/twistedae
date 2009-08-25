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
"""Console script to perform common tasks on configuring an application."""

import optparse
import os
import re
import sys
import twistedae 

DESCRIPTION = ("Console script to perform common tasks on configuring an "
               "application.")

USAGE = "usage: %prog [options] <application root>"

NGINX_STATIC_LOCATION = """
location ~ ^/(%(path)s)/ {
    root %(root)s;
    expires 30d;
}
"""

FCGI_PARAMS = """
    fastcgi_param CONTENT_LENGTH $content_length;
    fastcgi_param CONTENT_TYPE $content_type;
    fastcgi_param PATH_INFO $fastcgi_script_name;
    fastcgi_param QUERY_STRING $query_string;
    fastcgi_param REMOTE_ADDR $remote_addr;
    fastcgi_param REQUEST_METHOD $request_method;
    fastcgi_param REQUEST_URI $request_uri;
    fastcgi_param SERVER_NAME $server_name;
    fastcgi_param SERVER_PORT $server_port;
    fastcgi_param SERVER_PROTOCOL $server_protocol;
    fastcgi_pass_header Authorization;
    fastcgi_intercept_errors off;
"""

NGINX_SECURE_LOCATION = """
location ~ ^/(%(path)s) {
    auth_basic "%(app_id)s";
    auth_basic_user_file %(passwd_file)s;
    fastcgi_pass %(addr)s:%(port)s;
    %(fcgi_params)s
}
"""

NGINX_FCGI_CONFIG = """
location / {
    fastcgi_pass %(addr)s:%(port)s;
    %(fcgi_params)s
}
"""


def write_nginx_conf(outf, conf, app_root, addr='127.0.0.1', port='8081'):
    """Writes a nginx proxy configuration file."""

    proxy_conf = open(outf, 'w')

    static_dirs = {}
    secure_urls = []

    for handler in conf.handlers:
        ltrunc_url = re.sub('^/', '', handler.url)
        if handler.GetHandlerType() == 'static_dir':
            if handler.static_dir in static_dirs:
                static_dirs[handler.static_dir].append(ltrunc_url)
            else:
                static_dirs[handler.static_dir] = [ltrunc_url]
        if handler.secure == 'always':
            if ltrunc_url not in secure_urls:
                secure_urls.append(ltrunc_url)

    for s in static_dirs:
        if len(s.split('/')) > 1:
            root = app_root + '/' + '/'.join(s.split('/')[1:])
        else:
            root = app_root
        proxy_conf.write(NGINX_STATIC_LOCATION % dict(
            root=root,
            path='|'.join(static_dirs[s]),
            )
        )

    if secure_urls:
        proxy_conf.write(NGINX_SECURE_LOCATION % dict(
            addr=addr,
            app_id=conf.application,
            fcgi_params=FCGI_PARAMS,
            passwd_file=os.path.join(
                os.getcwd(), os.path.dirname(outf), 'htpasswd'),
            path='|'.join(secure_urls),
            port=port
            )
        )

    vars = locals()
    vars.update(dict(fcgi_params=FCGI_PARAMS))
    proxy_conf.write(NGINX_FCGI_CONFIG % vars)
    proxy_conf.close()


def main():
    """Runs the apptool console script."""

    op = optparse.OptionParser(description=DESCRIPTION, usage=USAGE)

    op.add_option("-n", "--nginx", dest="nginx", metavar="FILE",
                  help="write nginx configuration to this file",
                  default=os.path.join('etc', 'proxy.conf'))

    (options, args) = op.parse_args()

    if not sys.argv[1:]:
        op.print_usage()
        sys.exit(1)

    app_root = sys.argv[1]
    if not os.path.isabs(app_root):
        app_root = os.path.normpath(os.path.join(os.getcwd(), app_root))

    conf = twistedae.getAppConfig(app_root)

    write_nginx_conf(options.nginx, conf, app_root)
