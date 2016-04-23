import os
import re
import struct
import subprocess
from bs4 import BeautifulSoup
from flask import Flask, make_response, request, redirect, url_for
import urlparse

# requests
# beautifulsoup4
# html5lib

app = Flask(__name__)
# app.config['SERVER_NAME'] = 'localhost'
app.debug = True

needs_parsed = [
    'text/html',
    'application/xml+xhtml',
    'application/xhtml+xml',
    'text/css',
    'text/javascript',
    'application/javascript',
    'application/x-javascript',
    'application/json'
]

needs_script = [
    'text/html',
    'application/xml+xhtml',
    'application/xhtml+xml'
]


# uwsgi -s /tmp/uwsgi.sock --module myapp --callable app

def get_image_info(data):
    if is_png(data):
        w, h = struct.unpack('>LL', data[16:24])
        width = int(w)
        height = int(h)
    else:
        raise Exception('not a png image')
    return width, height

def is_png(data):
    return (data[:8] == '\211PNG\r\n\032\n'and (data[12:16] == 'IHDR'))

def add_in_up_script(html_doc, up_options):
    soup = BeautifulSoup(html_doc, "html5lib")
    kwargs = {
        'type':'text/javascript', 
        'data-preview':True,
        'src': "%s/w/get/%s.js" % (up_options.get('up-host'), up_options.get('up-id'))
    }
    new_tag = soup.new_tag("script", **kwargs)
    soup.body.append(new_tag)

    return str(soup)


@app.route('/preview/<path:url>')
def hello(url):
    if url.count('http') == 0:
        url = 'http://'+url
    # print 'URL3: %s' % url
    parsed = urlparse.urlparse(url)
    url = parsed.geturl()
    plain_url_png = re.sub('(\.|\/|\-)', '', parsed.hostname+parsed.path)+'-full.png'
    png_loc = "./static/"+plain_url_png
    if not os.path.isfile(png_loc):
        args = ["webkit2png","-W","1365","-H","768","-D", "./static","-F", url]
        page_png = subprocess.check_output(args)

    with open(png_loc, 'rb') as f:
        data = f.read()
    r = """
    <html>
    <head>
        <title>Preview of %s</title>
    </head>
    <body style="background: url(%s); background-size: cover; height: %spx;">
        Test
    </body>
    </html>
    """ % (url, url_for('static', filename=plain_url_png), get_image_info(data)[1])

    options = {
        'up-id': request.args.get('id'),
        'up-host': request.args.get('host')
    }
    r = add_in_up_script(r, options)

    return r

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(port=5000)
    # app.run(host=app.config['SERVER_NAME'], port=port)