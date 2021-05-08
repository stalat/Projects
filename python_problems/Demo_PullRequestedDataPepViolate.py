from bottle import run, route, template, get, post, request
import subprocess as sub, json, string

'''A function that will call the URL to recieve the files'''

@route('/', method=['GET', 'POST'])
@route('/home_page', method=['GET', 'POST'])
def home():
    #import pdb; pdb.set_trace()
    return "<form action='get_url' method='POST'>" \
           "<b>Enter the URL you want to check the file: </b>" \
           "<input type='text' name = 'url' ></form>"


@route('/get_url', method='post')
def get_url():
    url1 = request.forms.get('url')
    import pdb; pdb.set_trace()
    t = url1.replace('github.com', 'api.github.com/repos')
    url2 = url1.split('/')
    url3 = url2[6]
    url4 = t.split('/', 6)
    g = url4[0]+'//'+url4[2]+'/'+url4[3]+'/'+url4[4]+'/'+url4[5]
    c1 = """{0}'{1}'""".format('curl -s ', g)
    out = sub.Popen(c1, stderr=sub.PIPE, stdout=sub.PIPE, shell=True)

    k = json.loads(out.communicate()[0])
    k1 = k['source']['owner']['login']
    k2 = k['source']['html_url']
    c2 = 'wget '+url1.replace('blob', 'raw')
    out1 = sub.Popen(c2, stderr=sub.PIPE, stdout=sub.PIPE, shell=True)
    return template("This is the difference:{{p}} ", p=pep(url1))
    h = out1.communicate()
    return template("<h5>Requesting file to be merged is <h5><h3>{{url}}</h3>"
                    "<h5> and the branch name is</h5> <h3>{{url3}}</h3>"
                    "<h5>The Parent you forked this repo is:<h5> <h3>{{k1}}<h3>"
                    "<h5>and the url for parent repo is:<h5> <h3>{{k2}}</h3> ", url=url1, url3=url3, k1=k1, k2=k2)


def pep(url1):
    file_name = url1.split('/')[-1]
    import pdb; pdb.set_trace()
    cmd = 'pep8 '+file_name
    out2 = sub.Popen(cmd, stderr=sub.PIPE, stdout=sub.PIPE, shell=True)
    return out2.communicate()

@route('/b')
def b():
    out1 = sub.Popen('wget  https://raw.githubusercontent.com/SivaCn/test_for_webhooks/master/README.md' , stderr=sub.PIPE, stdout=sub.PIPE, shell=True)
    l=out1.communicate()
    return template("The file is there: {{l}}", l=l)

run(host='0.0.0.0', port=1026, debug=True)

