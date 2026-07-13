import re

def matching(regex, search, success_callback = None, failed_callback = None):
    template_date_word = re.compile(regex, re.IGNORECASE)
    match = template_date_word.search(search)

    if match and success_callback != None:
        success_callback(match)
    elif not match and failed_callback != None:
        failed_callback(match)
    
    return match

