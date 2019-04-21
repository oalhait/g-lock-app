#UTILITY FUNCTIONS FOR THE GLOCK

def get_code():
    code = ""
    try:  
        with open('code.txt') as fp:
            code = fp.readline().strip()
    finally:  
        fp.close()
        return code


def change_code(code):

    try:  
        with open('code.txt', 'w') as fp:
            fp.write(code + '\n')
    finally:  
        fp.close()
        return 
