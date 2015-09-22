# Product Roadmap #

The following represents features that are actively under development. Most of these features here are intended to be launched with the **forthcoming first Alpha release** (to be scheduled).

(_Important note_: We consider renaming the twistedae project to avoid confusion with the great [Twisted framework](http://twistedmatrix.com).)

## Features on Deck ##

| **Service** | **Status** | **Unit tests** |
|:------------|:-----------|:---------------|
| Datastore (mongoDB) | working    | yes            |
| Memcache (memcached) | working    | yes            |
| Task Queue (RabbitMQ) | working    | yes            |
| URL Fetch   | working    |                |
| Mail        | working    |                |
| XMPP        | untested   |                |
| Images      | working    |                |
| Remote API  | working    |                |

### Tools ###

  * Installation of the complete development environment via zc.buildout
  * Supervisor to manage the services
  * Support for uploading and downloading data to and from your application's datastore with `appcfg.py`
  * Support for `remote_api_shell.py`
  * The `bin/apptool` console script to perform common tasks on configuring an application (NGINX config etc.)

### Documentation ###

  * Online developer documentation
  * Sample-code and demo applications

## Features planned for the first Beta release ##

  * Alternative datastore backend (BDBDatastore, Cassandra)
  * Authentication (Google Accounts, OpenID, ...)
  * Queue configuration
  * Improved `appcfg.py` support
  * Admin console