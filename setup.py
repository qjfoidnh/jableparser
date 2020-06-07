# coding=utf-8
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='jableparser',
    author="qjfoidnh",
    version='0.0.1',
    author_email="qjfoidnh@126.com",
    license='MIT',

    packages=["jableparser"],

    description="A enhanced parser which can extract title, content, images and form from html pages, inspired by jparser",
    url="https://github.com/qjfoidnh/jableparser",
    long_description='''
Usage Example:
^^^^^^^^^^^^^^^^^^^^^
::

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
    
''',
    install_requires=[
        "lxml >= 3.7.1",
        "Beautifulsoup4 >= 4.2.0",
        
    ],
    zip_safe=False,
)
