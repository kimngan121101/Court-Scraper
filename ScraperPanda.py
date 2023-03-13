# import related libraries for this scraper
import scrapy
from scrapy import FormRequest
from scrapy.crawler import CrawlerProcess
import pandas
from bs4 import BeautifulSoup
import requests
import re
import csv

# Create a new csv file with a header
fileName = 'Test.csv'
with open(fileName, 'w', encoding = 'utf8', newline='') as f:     
    header = ['Case Number', 'Date Filed', 'Plaintiff', 'Case Type', 'Attorney', 'Activity Date', 'Event Desc', 'Comments']
    w = csv.writer(f)
    w.writerow(header)
    f.close()
fileName1 = 'casenotfound.csv'
with open(fileName1, 'w', encoding= 'utf8', newline = '') as f:
    w = csv.writer(f)
    w.writerow(['Case Number'])
    f.close()

# create a Scrapy class to scrape data from a url
class CourtSpider(scrapy.Spider): 
    name = 'Court Cases'
    start_urls =['https://casesearch.cookcountyclerkofcourt.org/CivilCaseSearchAPI.aspx'] # Api url
    def parse(self, response): # Sumbit the request form to the url.
        try: # Catch exceptions if needed
            req = requests.get('https://casesearch.cookcountyclerkofcourt.org/CivilCaseSearchAPI.aspx') # Send a get request to check for http and connection errors
            r = req.status_code
           
            for i in range (1, 3): # Use for loop to scrape multiple cases in a sequence 
                caseNum = f'2023L00000{i}'
                # Create the form request with desired inputs
                data = {
                    'ctl00$MainContent$ddlDatabase': '2',
                    'ctl00$MainContent$rblSearchType': 'CaseNumber',
                    'ctl00$MainContent$txtCaseNumber': caseNum,
                    'ctl00$MainContent$btnSearch': 'Start New Search'
                    }
                yield FormRequest.from_response(response,formdata=data, callback=self.formatToCSV, dont_filter = True, cb_kwargs ={'caseNum': caseNum})
            for i in range (10, 13): 
                caseNum = f'2023L0000{i}'
                data = {
                    'ctl00$MainContent$ddlDatabase': '0',
                    'ctl00$MainContent$rblSearchType': 'CaseNumber',
                    'ctl00$MainContent$txtCaseNumber': caseNum,
                    'ctl00$MainContent$btnSearch': 'Start New Search'
                    }
                yield FormRequest.from_response(response,formdata=data, callback=self.formatToCSV, dont_filter = True, cb_kwargs ={'caseNum': caseNum})
            for i in range (300, 303): 
                caseNum = f'2023L000{i}'
                data = {
                    'ctl00$MainContent$ddlDatabase': '2',
                    'ctl00$MainContent$rblSearchType': 'CaseNumber',
                    'ctl00$MainContent$txtCaseNumber': caseNum,
                    'ctl00$MainContent$btnSearch': 'Start New Search'
                    }
                yield FormRequest.from_response(response,formdata=data, callback=self.formatToCSV, dont_filter = True, cb_kwargs ={'caseNum': caseNum})

        except requests.exceptions.HTTPError: # Display error's message when error is raised
            if r == 503:
                print('503 SERVER IS DOWN.')
            elif r == 404:
                print('404 PAGE NOT FOUND.')
            elif r == 403:
                print('403 FORBIDDEN PAGE')
            else:
                print(r, 'Error. Please try again or come back later.')
        except requests.exceptions.ConnectionError:
            print('CONNECTION ERROR.')
    
    def formatToCSV(self, response, caseNum): # Manipulate the data in the dataframe and then format it into a csv file
        try: # Catch exceptions if needed
            # initialize variables to an empty string
            activityDate = ''
            eventDesc = ''
            comment = ''
            attorney = ''

            # parse html data with Panda and Beautiful soup
            dfs = pandas.read_html(response.text) 
            soup = BeautifulSoup(response.text, 'html.parser')
            # print(dfs) to see how the case's dataset is presented in a dataframe
            for i, df in enumerate (dfs): # use for loop to loop through tables in the dataframe
            
                if df.size == 6: # if the table is Activity Date then execute this if statement
                    full_str = df.iloc[0,3] # save the value of Event Desc
                    keyword = 'Summons'

                    if re.search(keyword, full_str): # if there is 'Summons' keyword in the Event Desc, then execute this if statement
                        # Save values of Activity Date and Event Desc into variables
                        activityDate = df.iloc[0,1]
                        eventDesc = df.iloc[0,3]
                        # Check the value of Comment. Whether it has value or N/A.
                        notNan = not pandas.isna(df.iloc[0,5])
                        if notNan: # If Comment has value, then update comment variable
                            comment = df.iloc[0,5]
                        break # stop the loop when found the first Activity table that has the keyword
                
                else: # Save values of the case into variables
                    caseNum = soup.find('span', {'id': 'MainContent_lblCaseNumber'}).text
                    dateFiled = soup.find('span', {'id': 'MainContent_lblDateFiled'}).text
                    caseType = soup.find('span', {'id': 'MainContent_lblCaseType'}).text
                    plaintiff = ((str(soup.find('span', {'id': 'MainContent_lblPlaintiffs'}))).split('">')[1]).split('<b')[0] # Capture the first plaintiff
                    notNan = not pandas.isna(df.iloc[3,6]) # Check the value of Attorney. Whether it has value or N/A.
                    if notNan: # If Attorney has value, then capture the first attorney
                        attorney = ((str(soup.find('span', {'id': 'MainContent_lblAttorney'}))).split('">')[1]).split('<b')[0]         
            
            # Write case information that have collected into the existing Case's info csv file
            with open(fileName, 'a', encoding = 'utf8', newline='') as f:  
                caseInfo = {"Case Number": caseNum, "Date Filed": dateFiled, "Plaintiff": plaintiff, "Case Type": caseType, "Attorney": attorney, "Activity Date": activityDate, "Event Desc": eventDesc, "Comments": comment}
                w = csv.DictWriter(f, fieldnames=header) 
                w.writerow(caseInfo)
                f.close()       
        except : # Display error's message when error is raised
            print(caseNum, 'CASE NOT FOUND')
            # Write all cases not found into the existing CasenotFound csv file
            with open(fileName1, 'a', encoding= 'utf8', newline = '') as f: 
                w = csv.DictWriter(f, fieldnames=header)
                w.writerow({'Case Number': caseNum})
                f.close()

# Run Scrapy
process = CrawlerProcess()
process.crawl(CourtSpider)
process.start()
