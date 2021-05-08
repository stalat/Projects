from bottle import run, route, template, get, post, request
import subprocess as sub, json, string
import urllib2
'''A function that will call the URL to recieve the files'''

@route('/', method=['GET', 'POST'])
@route('/home_page', method=['GET', 'POST'])
def home():
    return "<form action='get_url' method='POST'>" \
           "<b>Enter the URL you want to check the file: </b>" \
           "<input type='text' name = 'url' ></form>"


@route('/get_url', method='post')
def get_url():
    url1 = request.forms.get('url')
    import pdb; pdb.set_trace()
    t = url1.replace('github.com', 'api.github.com/repos')
    response = urllib2.urlopen(url1.replace('blob', 'raw'))
    html = response.read()
    file_name = url1.split('/')[-1]
    with open(file_name, 'a') as content_file:
        content_file.write(html)
    return template("This is the difference:{{p}} ", p=pep(file_name))


def pep(file_name):
    import pdb; pdb.set_trace()
    cmd = 'pep8 '+file_name
    out2 = sub.Popen(cmd, stderr=sub.PIPE, stdout=sub.PIPE, shell=True)
    #return out2.communicate()
    pep8_error_file = raw_input("PEP-8 conf.:-")
    with open(pep8_error_file, 'a') as pep8_error_file:
        pep8_error_file.write(str(out2.communicate()[0]))

run(host='0.0.0.0', port=1027, debug=True)
