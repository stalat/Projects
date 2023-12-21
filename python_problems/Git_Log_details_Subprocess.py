import os,os.path
import subprocess as sub
def foo(path):
	cmd=[]
	git_dir,log_number="git --git-dir="," log -3"
	with open("Hello.txt","wb") as k:
		cmd.append(git_dir+path+log_number)		
		out = sub.Popen(cmd, stderr=sub.PIPE, stdout=sub.PIPE,shell=True)
		k.write(out.communicate()[0])
		



if __name__=="__main()__":
	foo()


___________________________________________________________________________________________________________________________________________________________________
cmd = ["git --git-dir=/stalat/JIVA551/jiva_buildout/src/jivacore.ui/.git  log -3 --pretty=oneline"]

out = sub.Popen(cmd, stderr=sub.PIPE, stdout=sub.PIPE,shell=True)

print out.communicate()
____________________________________________________________________________________________________________________________________________________________________
"""If you have the git package installed on your system, Then you can directly use the Git command to log all the Changed Files in the repositories:

g = git.Git("C:/path/to/your/repo") 
loginfo = g.log('--since=2013-09-01','--author=KIM BASINGER','--pretty=tformat:','--numstat')
print loginfo
_____________________________________________________________________________________________________________________________________________________________________


t='/stalat/JIVA551/jiva_buildout/src/jivacore.ui'
	#print len([name for name in os.listdir(t)])
	#print os.listdir(t)
	#retvalue = os.system("git log -3 --pretty=oneline")
	#os.chdir("/stalat/JIVA551/jiva_buildout/src/jivacore.ui")
"""