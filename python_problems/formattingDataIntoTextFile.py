import string
import subprocess as sub
def foo(param):
    import pdb; pdb.set_trace()
    print param
    cmd='echo '+param+" | awk -F' ' '{print $1}'"
    out = sub.Popen(cmd, stderr=sub.PIPE, stdout=sub.PIPE, shell=True)
    file_name=out.communicate()
    cmd='echo '+param+" | awk -F' ' '{print $2}'"
    out = sub.Popen(cmd, stderr=sub.PIPE, stdout=sub.PIPE, shell=True)
    violation_type=out.communicate()
    cmd='echo '+param+" | awk -F' ' '{print $3}'"
    out = sub.Popen(cmd, stderr=sub.PIPE, stdout=sub.PIPE, shell=True)
    no_of_violations=out.communicate()
    cmd='echo '+param+" | awk -F' ' '{print $4}'"
    out = sub.Popen(cmd, stderr=sub.PIPE, stdout=sub.PIPE, shell=True)
    time_of_violation=out.communicate()
    
    
    with open('myapp.log','a') as myfile:
        myfile.write("%s\t|\t%s\t\t|\t\t%s\t\t\t|\t%s"%(file_name[0].rstrip(),violation_type[0].rstrip(),no_of_violations[0].rstrip(),time_of_violation[0]))
        
foo("CHANGES.TXT EXPECTED 12345 2014.08.11")

#out.write("%s \t\t %d\n" % (prevLine.rstrip() , curCount))