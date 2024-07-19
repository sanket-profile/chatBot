import sys


def getErrorMessage(message):
    _,_,exc_tb = sys.exc_info()
    if exc_tb:
        fileName = exc_tb.tb_frame.f_code.co_filename
        lineNumber = exc_tb.tb_lineno
        error_message = f"The error has occured in file - {fileName} on line number - {lineNumber}. ERROR IS - {message}"
        return error_message
    else:
        error_message = message
        return error_message

class CustomException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.error_message = getErrorMessage(message)

    def __str__(self):
        return self.error_message