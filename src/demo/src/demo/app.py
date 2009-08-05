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

import google.appengine.api.labs.taskqueue
import google.appengine.api.memcache
import google.appengine.ext.db
import google.appengine.ext.webapp
import google.appengine.ext.webapp.template
import random
import wsgiref.handlers

NUM_SHARDS = 20


class SimpleCounterShard(google.appengine.ext.db.Model):
    """Shards for the counter"""

    count = google.appengine.ext.db.IntegerProperty(required=True, default=0)   


class Note(google.appengine.ext.db.Model):
    """Very simple note model."""

    body = google.appengine.ext.db.StringProperty()
    date = google.appengine.ext.db.DateTimeProperty(auto_now=True)


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


def get_count():
    """Retrieves the value for a given sharded counter."""

    total = 0
    for counter in SimpleCounterShard.all():
        total += counter.count
    return total


def get_notes():
    notes = google.appengine.api.memcache.get("notes")
    if notes is not None:
        return notes
    else:
        query = google.appengine.ext.db.GqlQuery(
            "SELECT * FROM Note ORDER BY __key__ DESC LIMIT 100")
        notes = ['%s - %s' % (note.date, note.body) for note in query]
        if not google.appengine.api.memcache.add("notes", notes, 10):
            logging.error("Writing to memcache failed")

        return notes


class DemoRequestHandler(google.appengine.ext.webapp.RequestHandler):
    """Simple request handler."""

    def get(self):
        """Handles get."""

        increment()
        count = get_count()
        notes = get_notes()
        google.appengine.api.labs.taskqueue.add(url='/makenote',
                                                payload=str(count))
        vars = dict(count=count, env=self.request, notes=notes)
        output = google.appengine.ext.webapp.template.render('index.html', vars)
        self.response.out.write(output)


class NoteWorker(google.appengine.ext.webapp.RequestHandler):
    """Stores notes."""

    def post(self):
        """Handles post."""

        note = Note()
        note.body = self.request.body
        note.put()

 
app = google.appengine.ext.webapp.WSGIApplication([
    ('/', DemoRequestHandler),
    ('/makenote', NoteWorker),
], debug=True)


def main():
    """The main function."""

    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
