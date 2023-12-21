import os,platform,logging,time
#To check whether we are using linux or windows

if platform.platform().startswith('Windows'):
    logging_file=os.path.join(os.getenv('HOMEDRIVE'),os.getenv('HOMEDRIVE'),'test.log')
else:

    #The logging files are having the value as /home/stalat/test.log
    logging_file=os.path.join(os.getenv('HOME'),'test.log')
time.sleep(5)
print("Logging to ",logging_file)
logging.basicConfig(
level=logging.DEBUG,
format='%(asctime)s,:%(levelname)s,:%(message)s',
filename=logging_file,
filemode='w'
)
logging.debug("Start of the Program")
logging.info("Doing something")
logging.warning("Dying Now")