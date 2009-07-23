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
"""Demo application."""

import google.appengine.ext.db
import google.appengine.ext.webapp
import google.appengine.ext.webapp.template
import random
import wsgiref.handlers

NUM_SHARDS = 20


class SimpleCounterShard(google.appengine.ext.db.Model):
    """Shards for the counter"""

    count = google.appengine.ext.db.IntegerProperty(required=True, default=0)   


def get_count():
    """Retrieves the value for a given sharded counter."""

    total = 0
    for counter in SimpleCounterShard.all():
        total += counter.count
    return total


def increment():
    """Increments the value for a given sharded counter."""

    def transaction():
        index = random.randint(0, NUM_SHARDS - 1)
        shard_name = "shard" + str(index)
        counter = SimpleCounterShard.get_by_key_name(shard_name)
        if counter is None:
            counter = SimpleCounterShard(key_name=shard_name)
        counter.count += 1
        counter.put()

    google.appengine.ext.db.run_in_transaction(transaction)


class DemoRequestHandler(google.appengine.ext.webapp.RequestHandler):
    """Simple request handler."""

    def get(self):
        """Handles get."""

        increment()
        count = get_count() 
        vars = dict(count=count, env=self.request)
        output = google.appengine.ext.webapp.template.render('index.html', vars)
        self.response.out.write(output)

 
app = google.appengine.ext.webapp.WSGIApplication([
    ('/', DemoRequestHandler),
], debug=True)


def main():
    """The main function."""

    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
