from bs4 import NavigableString, Tag

def element_to_formatted_text(element):
    if isinstance(element, NavigableString):
        text = element.strip()
        return text if text else ''
    
    if not isinstance(element, Tag):
        return ''
    
    if element.name in ('ul', 'ol'):
        items = []
        for li in element.find_all('li', recursive=False):
            li_text = ' '.join(
                element_to_formatted_text(child) for child in li.children
            ).strip()
            if li_text:
                items.append(li_text)
        return ', '.join(items)
    
    parts = []
    for child in element.children:
        child_text = element_to_formatted_text(child)
        if child_text:
            parts.append(child_text)
    
    return ' '.join(parts)