import os
import time
"""#Where my files are saved to be backed-up
source='/home/stalat/Desktop/Talat_Sentinel/PyPractice'
#where my backed-up files will get stored
target_dir='/home/stalat/Desktop/Talat_Sentinel'
#The files are backed up into a zip file
if not os.path.exists(target_dir):
    os.mkdir(target_dir)

target=target_dir+os.sep+time.strftime('%Y%m%d%H%M%S')+'.zip'
zip_command="zip -r {0}{1}".format(target,"".join(source))
print zip_command
if os.system(zip_command) == 0:
    print 'Successful backup to', target
else:
    print 'Backup FAILED'"""
source='/home/stalat/Desktop/Talat_Sentinel/PyPractice'
target_dir='/home/stalat/Desktop/Talat_Sentinel'
import pdb; pdb.set_trace()
target = target_dir + os.sep + \
time.strftime('%Y%m%d%H%M%S') + '.zip'
if not os.path.exists(target_dir):
    os.mkdir(target_dir)
#zip_command = "zip -r {0} {1}".format(target,''.join(source))
print "Zip command is:"
#print zip_command
print "Running:"
if os.system("zip -r '/home/stalat/Desktop/Talat_Sentinel/20140523124523.zip' '/home/stalat/Desktop/Talat_Sentinel/PyPractice'") == 0:
    print 'Successful backup to', target
else:
    print 'Backup FAILED'







