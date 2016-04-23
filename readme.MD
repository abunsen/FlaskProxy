# UP Preview Proxy

### usage

Params:
`id` renders widget_id for file directory & used in the `data-attr` below
`host` is where the widget lives

### set up

`pip install -r requirements.txt`

also needs node, npm & the following packages::

`npm install phantomjs phantom-url`

### production

run behind nginx 

##### nginx.conf


```
location / { try_files $uri @yourapplication; }

location @yourapplication {
    proxy_pass
}
```

##### gunicorn

`pip install uwsgi`

run from same directory as `proxy.py`: `gunicorn -w 4 -b 127.0.0.1:8080 proxy:app &`

##### deploy


`cd ~/apps/ && rm -rf FlaskProxy && git clone git@github.com:abunsen/FlaskProxy.git && cd FlaskProxy && source ~/apps/bin/activate && kill `cat ~/up.proxy.pid` && gunicorn -w 4 -D -b 127.0.0.1:8080 proxy:app -p ~/up.proxy.pid`