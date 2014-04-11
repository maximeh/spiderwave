#! /usr/bin/python
# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
import subprocess
import re
import sys
import urllib2

import db_wrapper

def get_page( url ):
    opener = urllib2.build_opener()
    data = opener.open(url).read()
    soup = BeautifulSoup(data)
    return soup

db_wrapper.connect()
non_decimal = re.compile(r'[^\d.]+')
cnt_id = db_wrapper.insert_country("Canada")

soup = get_page("http://www.canadianwebradio.com/")
countries = soup.find("table", {"id" : "thetable"})

countries_url = []
# Get every countries's page
for row in countries.findAll('tr'):
    link = row.findAll('td')[0].findAll('a')[0]
    countries_url.append("http://www.canadianwebradio.com/"+link['href'])

# Ok let's parse per country now
for country in countries_url:
    soup = get_page(country)
    radios = soup.find("table", {"id" : "thetable3"})
    for row in radios.findAll('tr'):
        if len(row.findAll('th')) > 0:
            continue
        name_link = row.findAll('td')[0].findAll('a')
        location = row.findAll('td')[2].text
        if len(name_link) > 0:
            name = name_link[0].text
            url = name_link[0]['href']

        stream_href_list = row.findAll('td')[4].findAll('a')
        streams = []
        for stream_href in stream_href_list:
            stream = stream_href["href"]
            quality = stream_href.text
            try:
                quality = int(non_decimal.sub('', quality))
            except ValueError:
                quality = 0
            if "javascript:" in stream:
                open_js = stream[stream.find("(")+1:stream.find(")")]
                open_arg = open_js[open_js.find("(")+1:open_js.find(")")]
                args = open_arg.split(',')
                stream = args[0].strip('\'')
            streams.append([stream, quality])

        categ = []
        if len(row.findAll('td')) > 5:
            categ = row.findAll('td')[5].text
            categ = re.split(', |/', categ)

        # Insert a City of a country
        city_id = db_wrapper.insert_city(location.strip(), cnt_id)
        # Insert the genre
        genres_id = []
        for cat in categ:
            genres_id.append(db_wrapper.insert_genre(cat.strip()))

        st_ids = []
        for st in streams:
            st_ids.append(db_wrapper.insert_streamurl(st[0].strip(), st[1]))

        # Finally, the whole radio
        db_wrapper.insert_radio(name.strip(), stream_url_ids=st_ids, genre_ids=genres_id, country_id=cnt_id, city_id=city_id, homepage=url.strip())

        print '-'*80
        print name
        print url
        print location
        print streams
        print categ

db_wrapper.disconnect()
