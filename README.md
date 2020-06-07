# jableparser
A HTML parser inspired by jparser which can extract title, content, images, especially form data from html pages

Install:

    pip install jableparser
    (requirement: lxml, Beautifulsoup4)

Usage Example:

    from __future__ import print_function
    import requests
    from jableparser import PageModel
    html = requests.get("https://hollywoodmask.com/entertainment/jason-carroll-cnn-age-gay.html", verify=False).text
    pm = PageModel(html)
    result = pm.extract()
    
    print("==title==")
    print(result['title')
    print("==content==")
    for x in result['content']:
        if x['type'] == 'text':
            print(x['data'])
        if x['type'] == 'image':
            print("[IMAGE]", x['data']['src'])
        if x['type'] == 'html':
            print("Raw table string: )
            print(x['data'])
            print("Processed table data if two columns: )
            print(pm.processtable(x['data']))


