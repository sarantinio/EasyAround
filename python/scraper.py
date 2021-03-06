
''' ==========================================================================
   Scraper. It visits tripadvisor in order to get all the necessary content
   ========================================================================== '''
from bs4 import BeautifulSoup
from urllib2 import urlopen
import urllib
import json
import os
from PIL import Image
from time import sleep # be nice
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from app import models
from app import db


BASE_URL = "http://www.tripadvisor.com"

def make_soup(url):
    html = urlopen(url).read()
    return BeautifulSoup(html, "lxml")

def get_places_links(section_url):
    soup = make_soup(section_url)
    category_links = [BASE_URL + block.find("a", {'class':"property_title"})['href'] for block in soup.findAll("div", {'class':"listing"})]
    return category_links

def getHeroPhoto(list):
    for dict in list:
        if dict['id'] == 'HERO_PHOTO':
            return dict['data']

    return list[0]['data']
    
if __name__ == '__main__':
    places = []
    pages = {
        'museum' : ("http://www.tripadvisor.com/Attractions-g187791-Activities-c49-Rome_Lazio.html", "http://www.tripadvisor.com/Attractions-g187791-Activities-c49-oa30-Rome_Lazio.html"),
        'historical': ("http://www.tripadvisor.com/Attractions-g187791-Activities-c50-Rome_Lazio.html", "http://www.tripadvisor.com/Attractions-g187791-Activities-c50-oa30-Rome_Lazio.html", "http://www.tripadvisor.com/Attractions-g187791-Activities-c50-oa60-Rome_Lazio.html", "http://www.tripadvisor.com/Attractions-g187791-Activities-c47-oa30-Rome_Lazio.html", "http://www.tripadvisor.com/Attractions-g187791-Activities-c47-Rome_Lazio.html"),
        'shopping' : ("http://www.tripadvisor.com/Attractions-g187791-Activities-c26-Rome_Lazio.html", "http://www.tripadvisor.com/Attractions-g187791-Activities-c26-oa30-Rome_Lazio.html"),
        'gastronomy': ("http://www.tripadvisor.com/Attractions-g187791-Activities-c36-Rome_Lazio.html", "http://www.tripadvisor.com/Attractions-g187791-Activities-c36-oa30-Rome_Lazio.html"),
        'entertainment': ("http://www.tripadvisor.com/Attractions-g187791-Activities-c43-Rome_Lazio.html",),
        'performance': ("http://www.tripadvisor.com/Attractions-g187791-Activities-c43-Rome_Lazio.html",),
        'outdoors': ("http://www.tripadvisor.com/Attractions-g187791-Activities-c45-Rome_Lazio.html",),
        'kids': ("http://www.tripadvisor.com/Attractions-g187791-Activities-c48-Rome_Lazio.html",),
        'hard': ("http://www.tripadvisor.com/Attractions-g187791-Activities-c38-Rome_Lazio.html",),
        'amusement': ("http://www.tripadvisor.com/Attractions-g187791-Activities-c31-Rome_Lazio.html",)
    }

    pool = ThreadPool(4)
    for key in pages:
        for category in pages[key]:
            places = get_places_links(category)
            
            placesContent = pool.map(urlopen, places)
            for place in placesContent:
                html = place.read()
                soup = BeautifulSoup(html, "lxml")

                title = soup.find("h1", {'id':"HEADING"}).get_text().strip()
                print title;
                description = ""
                if soup.find("span", {"class":"onShow"}) != None:
                    description = soup.find("span", {"class":"onShow"}).get_text().replace("less", "").replace("Owner description:", "").strip()
                intensive = False
                rating = int(float(soup.find("img", {"class": "sprite-ratings"})["content"]))
                type = key
                excludedCategory = None
                forKids = None

                
                scripts = soup.findAll('script')
                script = scripts[len(scripts)-5].get_text()
                script = script.replace("ta.queueForLoad( function() {", "")
                script = script.replace("window.setupLazyLoad();", "").replace("}, 'lazy load images');", "")
                script = script.replace("var lazyHtml = [", "").replace("var lazyImgs = ", "").replace("];", "").strip() + "]"
                value = json.loads(script)
                imgUrl = getHeroPhoto(value)
                imgName = os.path.basename(imgUrl)
                urllib.urlretrieve(imgUrl, 'images/'+imgName)

                im = Image.open('images/'+imgName)
                width, height = im.size   # Get dimensions
                new_width = 160
                new_height = 160

                left = (width - new_width)/2
                top = (height - new_height)/2
                right = (width + new_width)/2
                bottom = (height + new_height)/2

                im = im.crop((left, top, right, bottom))

                im.save('images/'+imgName)


                if type == "kids":
                    type = "entertainment"
                    forKids = True

                if type == "hard" or type == "amusement":
                    type = "amusement"
                    intensive = True
                    excludedCategory='elderly'


                if models.Location.query.filter_by(name = title).first() is None:
                    l = models.Location(title, description, 0,0, imgName, intensive, rating, type, excludedCategory, forKids)
                    db.session.add(l)
                    db.session.commit()
    
    


   



