# UP Preview Proxy

### usage

Params:
`up_id` renders widget_id for file directory & used in the `data-attr` below
`widget` is the JS Class name
`data-attr` is the data attribute on the script tag
`attr-x-1` is extra attribute one, paired with `val-x-1` as its value
`attr-x-2` is extra attribute one, paired with `val-x-2` as its value
`widget_loc` is where the widget lives

### set up

`pip install -r requirements.txt`

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