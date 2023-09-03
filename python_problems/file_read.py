import os

def log_file_reader():
    """
    function to read a file and output the lines which has word 'error' in it.
    """
    keyword_to_search = 'error'
    file_to_read = os.path.join(os.getcwd(), 'log_file.txt')
    with open(file_to_read) as file_obj:
        file_content = file_obj.read()
        for log_line in file_content.splitlines():
            if keyword_to_search in log_line:
                # write your logic whatever you want to perform over filtered lines of log file
                print(log_line)

        

if __name__ == '__main__':
    log_file_reader()