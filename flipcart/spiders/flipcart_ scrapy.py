import scrapy
from bs4 import BeautifulSoup as Bs
from pandas import DataFrame as df
import requests
import logging

class ShopcluesSpider(scrapy.Spider):
   #name of spider
   name = 'flipcart'

   #list of allowed domains
   # allowed_domains = ['https://www.flipkart.com/']
   #starting url
   # start_urls = ['https://www.flipkart.com/search?q=mobile']
   #location of csv file
   custom_settings = {
       'FEED_URI' : 'tmp/shopclues.csv'
   }
   PRODUCT_CLASS_DICT = {'name': '_3wU53n',
                          'rating': 'hGSR34 _2beYZw',
                          'rating2': 'hGSR34 _1x2VEC',
                          'rating3': 'hGSR34 _1nLEql',
                          'specs': 'vFw0gD',
                          'price': '_1vC4OE _2rQ-NK',
                          'mrp': '_3auQ3N _2GcJzG', }
   BOX_PRODUCT_CLASS_DICT = {'name': '_2cLu-l',  # <a> class
                              'rating': 'hGSR34 _2beYZw',
                              'rating2': 'hGSR34 _1x2VEC',
                              'rating3': 'hGSR34 _1nLEql',
                              'specs': '_1rcHFq',   # <div> class
                              'price': '_1vC4OE', }
   def start_requests(self):
      url = 'https://www.flipkart.com/search?q='
      print('Enter the word to search')
      search = input()
      url += search
      self.urls = [url]
      for url in self.urls:
         yield scrapy.Request(url=url, callback=self.parse)

   def parse(self, response):
      #Extract product information
      # print response , "response @@@@@@@@@"
      # # print response.text , "text @@@@@@@@@"
      # print response.flags , "flags @@@@@@@@@"
      # print response.request , "request @@@@@@@@@"
      # print response.headers , "headers @@@@@@@@@"

      raw_html = response.text
      soup = Bs(raw_html, 'html.parser')
      df1 = self.get_number_of_products(soup)
      
      for index in range(0,len(df1['RATING'])):
         scraped_info = {
            'NAME' : df1['NAME'][index],
            'SPECS' : df1['SPECS'][index],
            'PRICE' : df1['PRICE'][index], 
            'RATING' : df1['RATING'][index]
         }

         yield scraped_info

   def get_number_of_products(self,soup):
      klass = '_2yAnYN'

      try:
         raw_results = soup.find('span', {'class': klass}).get_text()
         if raw_results is None:
             logging.error("No Results found for <h1> class: " + klass)
             exit()
         else:
             start = raw_results.index('of')
             end = raw_results.index('results')
             no_of_results = int(raw_results[start + 3:end - 1].replace(',', ''))
             if no_of_results > 10000:
                 print('Too many' + '(' + str(no_of_results) + ' )results ' + 'Please extend your search term.')
                 print('Do you still want to continue, it will take a lot of time.(Y/N)')
                 choice = input()
                 if choice == 'Y' or choice == 'y':
                     return self.get_max_page(soup)
                 elif choice == 'N' or choice == 'n':
                     exit()
                 else:
                     print('invalid choice, exiting')
                     exit()
             else:
                 print('No of results: ', no_of_results)
                 return self.get_max_page(soup)
      except Exception as e:
         raise

   def get_max_page(self, response):
      # raw_html = response
      # soup = Bs(raw_html, 'html.parser')
      klass = '_2zg3yZ'
      try:
         raw_results = response.find('div', {'class': klass}).select_one('span').get_text()
         start = raw_results.index('of')
         no_of_pages = int(raw_results[start + 3:].replace(' ', ''))
      except AttributeError:
         no_of_pages = 1
         logging.info('Only first page found')
      return self.create_page_urls(no_of_pages)

   def create_page_urls(self, no_of_pages):
      pages_url_list = list()
      for urls in self.urls:
         for i in range(1, no_of_pages + 1):
            url = urls + '&page=' + str(i)
            pages_url_list.append(url)
      return self.validate_page_urls(pages_url_list)

   def validate_page_urls(self, pages_url_list):
      valid_page_url_list = list()
      for url in pages_url_list:
         logging.info('Checking page url: ' + url)
         for i in range(1, 4):
             try:
                 for j in range(1, 4):
                     response = requests.get(url)
                     if response.status_code == 200:
                         valid_page_url_list.append(url)
                         logging.info(url + ' is valid')
                         print(url + ' is valid')
                         break
                     else:
                         logging.error('Response: ' + str(response.status_code))
                         print('Retrying...' + str(j))
                         continue
             except:
                 logging.error('No connection')
                 print('Request not completed for ' + url + ', Retrying..' + str(i))
                 continue
             break
      if len(valid_page_url_list) is not None:
         return self.check_diplay_type(valid_page_url_list)
      else:
         print('No valid url found, exiting...')
         exit()

   def check_diplay_type(self, valid_page_url_list):
        # class = '_1HmYoV _35HD7C col-10-12' --> box format
        # _1HmYoV hCUpcT
      item = valid_page_url_list[0]
      response = requests.get(item)
      raw_html = response.text
      soup = Bs(raw_html, 'html.parser')
      try:
         for var in soup.find_all("div", class_='bhgxx2 col-12-12'):
             if var.find('a', {'class': '_2cLu-l'}) is not None:
                 logging.info('Box type screen structure found')
                 return self.get_product_info_box(valid_page_url_list)
             elif var.find('div', {'class': self.PRODUCT_CLASS_DICT['name']}) is not None:
                 return self.get_product_info(valid_page_url_list)
             else:
                 logging.error('screen type cannot be recognized')
      except AttributeError:
         logging.error('Wrong class name in check_display_type()')


   def get_product_info_box(self, valid_page_url_list):
      raw_name_list = list()
      raw_rating_list = list()
      raw_specs_list = list()
      raw_price_list = list()
      for item in valid_page_url_list:
         response = requests.get(item)
         raw_html = response.text
         soup = Bs(raw_html, 'html.parser')
         try:
             for var2 in soup.find_all("div", class_='bhgxx2 col-12-12'):
                  for var in var2.find_all("div" , class_='_3liAhj _1R0K0g'):
                     try:
                        if var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating']}) is not None:
                           rating = var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating']}).get_text()[:-2]
                           raw_rating_list.append(float(rating))
                        elif var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating2']}) is not None:
                           rating = var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating2']}).get_text()[:-2]
                           raw_rating_list.append(float(rating))
                        elif var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating3']}) is not None:
                           rating = var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating3']}).get_text()[:-2]
                           raw_rating_list.append(float(rating))
                        else:
                           rating = 0
                           raw_rating_list.append(rating)
                        if var.find('a', {'class': self.BOX_PRODUCT_CLASS_DICT['name']}) is None:
                           raw_name_list.append(None)
                        else:
                           name = var.find('a', {'class': self.BOX_PRODUCT_CLASS_DICT['name']}).get_text()
                           raw_name_list.append(name)
                        if var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['specs']}) is None:
                           raw_specs_list.append(None)
                        else:
                           specs = var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['specs']}).get_text()
                           raw_specs_list.append(specs)
                        if var.find("div", class_=self.BOX_PRODUCT_CLASS_DICT['price']) is None:
                           raw_price_list.append(None)
                        else:
                           price = var.find("div", class_=self.BOX_PRODUCT_CLASS_DICT['price']).get_text()[1:].replace(',', '')
                           raw_price_list.append(int(price))
                     except:
                        continue
             print('Scraping...please wait...')
         except AttributeError:
             print('Class name is different')
      df1 = ({'NAME': raw_name_list, 'RATING': raw_rating_list, 'SPECS': raw_specs_list, 'PRICE': raw_price_list})
      # df1 = df1.dropna()
      # print('No of valid products fetched: ' + str(df1.shape[0]))
      print('Thank-you for using Flipkart-Scraper.')
      return df1

   def get_product_info(self, valid_page_url_list):
      raw_name_list = list()
      raw_rating_list = list()
      raw_specs_list = list()
      raw_price_list = list()
      for item in valid_page_url_list:
         response = requests.get(item)
         raw_html = response.text
         soup = Bs(raw_html, 'html.parser')
         try:
            for var in soup.find_all("div", class_='bhgxx2 col-12-12'):
               if var.find('div', {'class': self.PRODUCT_CLASS_DICT['name']}) is None:
                  raw_name_list.append(None)
               else:
                  name = var.find('div', {'class': self.PRODUCT_CLASS_DICT['name']}).get_text()
                  raw_name_list.append(name)
               if var.find('ul', {'class': self.PRODUCT_CLASS_DICT['specs']}) is None:
                  raw_specs_list.append(None)
               else:
                  specs = var.find('ul', {'class': self.PRODUCT_CLASS_DICT['specs']}).get_text()
                  raw_specs_list.append(specs)
               if var.find("div", class_=self.PRODUCT_CLASS_DICT['price']) is None:
                  raw_price_list.append(None)
               else:
                  price = var.find("div", class_=self.PRODUCT_CLASS_DICT['price']).get_text()[1:].replace(',', '')
                  raw_price_list.append(int(price))
               if var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating']}) is not None:
                  rating = var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating']}).get_text()[:-2]
                  raw_rating_list.append(float(rating))
               elif var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating2']}) is not None:
                  rating = var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating2']}).get_text()[:-2]
                  raw_rating_list.append(float(rating))
               elif var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating3']}) is not None:
                  rating = var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating3']}).get_text()[:-2]
                  raw_rating_list.append(float(rating))
               else:
                  rating = 0
                  raw_rating_list.append(rating)
                 
            print('Scraping...please wait...')
         except AttributeError:
             print('Class name is different')
      df1 = ({'NAME': raw_name_list, 'RATING': raw_rating_list, 'SPECS': raw_specs_list, 'PRICE': raw_price_list})
      # df1 = df1.dropna()
      # print('No of valid products fetched: ' + str(df1.shape[0]))
      return df1


      







