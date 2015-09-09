# UP Preview Proxy

### set up

`pip install -r requirements.txt`

### production

run behind nginx 

##### nginx.conf


```
location / { try_files $uri @yourapplication; }

location @yourapplication {
    include uwsgi_params;
    uwsgi_pass unix:/tmp/uwsgi.sock;
}
```

##### uwsgi

`pip install uwsgi`

run from same directory as `proxy.py`: `uwsgi -s /tmp/uwsgi.sock -b 10000 --module proxy --callable app`