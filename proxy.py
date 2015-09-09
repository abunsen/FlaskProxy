import os
import re
from bs4 import BeautifulSoup
from flask import Flask, make_response, request
import urlparse
# from requests import Request, Session
import requests

# requests
# beautifulsoup4
# html5lib

app = Flask(__name__)
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


# REGEXs
re_rel_proto = r'("|\'|=)(\/\/\w)' # matches //site.com style urls where the protocol is auto-sensed
re_rel_root = r'((href|src|action)=[\'"]{0,1})(\/.)' # matches src="/asdf/asdf"
re_rel = r'((href|src|action)=[\'"]{0,1})(\w+\/)' # matches src="asdf/asdf" or src="../asdf/asdf"
# // no need to match href="asdf/adf" relative links - those will work without modification
# // note: we con't check for urls in quotes here because the previous check will have already handled them
re_css_abs = r'(url\(\s*)(https?:(\/\/|\\\/\\\/))' # matches url( http
re_css_rel_proto = r'(url\(\s*)(\/\/\w)'
re_css_rel_root = r'(url\(\s*[\'"]{0,1})(\/\w+)' # matches url( /asdf/img.jpg
re_css_rel = r'(url\(\s*[\'"]{0,1})(\w+\/)' # matches url( asdf/img.jpg or url( ../asdf/img.jpg
# // partial's dont cause anything to get changed, they just cause last few characters to be buffered and checked with the next batch
re_html_partial = r'((.url\(\s*)?\s[^\s]+\s*)$/' # capture the last two "words" and any space after them  - for `url( h`
# // matches broken xmlns attributes like xmlns="/proxy/http://www.w3.org/1999/xhtml" and xmlns:og="/proxy/http://ogp.me/ns#"
re_proxied_xmlns = r'(xmlns(:[a-z]+)?=")\/preview\/'

def rewrite_urls(string, uri, base):
    re_abs_url = r"(\"|'|=)(http:\/\/%s|https:\/\/%s)" % (uri.netloc.replace('.', '\.'),uri.netloc.replace('.', '\.')) # "http, 'http, or =http
    # print 're_abs_url', re_abs_url
    # // some special rules for CSS
    string = re.sub(re_css_rel_proto, r"\1%s:\2" % uri.scheme, string)
    string = re.sub(re_css_rel_root, r"\1%s://%s\2" % (uri.scheme, uri.netloc), string)
    string = re.sub(re_css_rel, r"\1%s://%s/\2" % (uri.scheme, uri.netloc), string)
    # string = re.sub(re_css_abs, r"\1%s\2" % base, string)

    # // first upgrade // links to regular http/https links because otherwise they look like root-relative (/whatever.html) links
    string = re.sub(re_rel_proto, r"\1%s:\2" % uri.scheme, string)
    # // next sub urls that are relative to the root of the domain (/whatever.html) because this is how proxied urls look
    string = re.sub(re_rel_root, r"\1%s://%s\3" % (uri.scheme, uri.netloc), string)
    string = re.sub(re_rel, r"\1%s://%s/\3" % (uri.scheme, uri.netloc), string)
    # // last sub any complete urls
    string = re.sub(re_abs_url, r"\1%s\2" % base, string)

    # // fix xmlns attributes that were broken because they contained urls.
    # // (JS RegExp doesn't support negative lookbehind, so breaking and then fixing is simpler than trying to not break in the first place)
    string = re.sub(re_proxied_xmlns, r'\1', string)
    return string

def add_in_up_script(html_doc, up_options):
    soup = BeautifulSoup(html_doc, "html5lib")
    tag_placed = soup.find_all('script', attrs={
        "%s" % up_options.get('attr'): "%s" % up_options.get('widget-id')
    })
    # print "num tags placed=", len(tag_placed)
    if len(tag_placed) <= 0:
        kwargs = {k:v for k, v in up_options.items() if k and not k.startswith('widget')}
        kwargs.update({'type':'text/javascript'})
        new_tag = soup.new_tag("script", **kwargs)
        new_tag.string = """var %s = window.%s || {};
        var p = window.location.protocol == 'https:' ? 'https:' : 'http:' ;
        (function() { 
            var script = document.createElement('script');
            script.async = true;
            script.src = p+'//%s';
            var entry = document.getElementsByTagName('script')[0];
            entry.parentNode.insertBefore(script, entry);
        })();""" % (up_options.get('widget'), up_options.get('widget'), up_options.get('widget-loc'))
        soup.body.append(new_tag)
    return str(soup)


@app.route('/preview/<path:url>')
def hello(url):
    url = url.replace('http:/', 'http://')
    url = url.replace('https:/', 'https://')
    # url = request.args['url']
    # print 'URL: %s' % url
    # url = url.replace('www.','')
    # print 'URL2: %s' % url
    if url.count('http') == 0:
        url = 'http://'+url
    # print 'URL3: %s' % url
    parsed = urlparse.urlparse(url)
    url = parsed.geturl()
    # print 'URL4: %s' % url
    # s = Session()
    # req = Request('GET',  url, headers=request.headers)
    # print "CLASSSSS", request.headers.__class__.__name__
    # prepped = s.prepare_request(req)
    # response = s.send(prepped)
    # print "HOST!", parsed.netloc
    headers_as_dict = {
        'User-Agent': request.headers.get('User-Agent'), 
        'Host': parsed.netloc,
        'Accept': request.headers.get('Accept'),
        'Accept-Encoding': request.headers.get('Accept-Encoding'),
        # 'Cookie': request.headers.get('Cookie')
    }
    response = requests.get(url, headers=headers_as_dict)
    # print response.text
    needs_to_be_parsed = response.headers.get('content-type', '').split(';')[0] in needs_parsed
    needs_up_script = response.headers.get('content-type', '').split(';')[0] in needs_script

    if needs_to_be_parsed and response.headers.get('content-length'):
        del response.headers['content-length']

    needs_decoded = (needs_to_be_parsed and response.headers.get('content-encoding') == 'gzip')

    # // we're going to de-gzip it, so nuke that header
    if needs_decoded:
        del response.headers['content-encoding']

    if response.headers.get('set-cookie'):
        del response.headers['set-cookie']

    if response.headers.get('strict-transport-security'):
        del response.headers['strict-transport-security']

    if needs_to_be_parsed:
        # print "RE HEADERS!:", response.request.headers
        # print "HEADERSS!", response.headers
        modded_response = rewrite_urls(response.text, parsed, '/preview/')
        # print "modded_response", modded_response
    else:
        modded_response = response.content

    if needs_up_script:
        options = {
            'widget-id': request.args.get('up_id'),
            'widget': request.args.get('widget'),
            request.args.get('data-attr'): request.args.get('up_id'),
            request.args.get('attr-x-1'): request.args.get('val-x-1'),
            request.args.get('attr-x-2'): request.args.get('val-x-2'),
            'widget-loc': request.args.get('widget_loc')
        }
        modded_response = add_in_up_script(modded_response, options)

    r = make_response(modded_response)
    for k, v in response.headers.items():
        if k.lower() != 'x-frame-options':
            r.headers[k] = v

    return r

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port)