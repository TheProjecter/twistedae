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
"""The taskqueue package."""

import datetime
import logging
import os
import time


class _UTCTimeZone(datetime.tzinfo):
  """UTC timezone."""

  ZERO = datetime.timedelta(0)

  def utcoffset(self, dt):
    return self.ZERO

  def dst(self, dt):
    return self.ZERO

  def tzname(self, dt):
    return 'UTC'

UTC = _UTCTimeZone()


def is_deferred_eta(eta):
    """Checks whether the given eta is in the future."""

    if hasattr(time, 'tzset'):
        os.environ['TZ'] = 'UTC'
        time.tzset()

    eta = datetime.datetime.fromtimestamp(eta, UTC)
    now = datetime.datetime.now()

    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    if eta > now:
        return True

    return False


def get_new_eta_usec(try_count):
    """Returns a new astimated execution time depending on try count."""

    eta = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
    return time.mktime(eta.replace(tzinfo=UTC).timetuple())
