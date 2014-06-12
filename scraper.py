from selenium import webdriver
from bs4 import BeautifulSoup
import os, time, sys, re
import requests

url = 'http://www.reddit.com/r/pics' #enter subreddit url to parse
custom_folder_name = "" #leave blank for default naming
pages = 1 #set how many pages to parse

driver = webdriver.PhantomJS(executable_path='phantomjs/phantomjs')
driver.get(url)
driver.set_window_size(1024, 768)


try: #If over 18 subreddit, then accept
	yes_btn = driver.find_element_by_xpath('/html/body/div[3]/div[2]/form/p[2]/button[1]').click()
except:
	pass

is_image = re.compile('.*.jpg|.*.png|.*.gif')
is_album = re.compile('.*imgur.*/a/.*')
downloaded = []

ctr=0
album=0
sites= []
size = 0
cur_date = time.strftime("%Y-%m-%d")
start_time = time.clock()
if custom_folder_name == "":
	folder_name = "%s %s" %(url[url.rfind('/') + 1:], cur_date )
else:
	folder_name = custom_folder_name

sd = os.path.dirname(__file__)
directory = os.path.join(sd, folder_name)
if not os.path.exists(directory): os.mkdir(directory)

html_source = driver.page_source
site = BeautifulSoup(html_source)

# Download function
def download_file(url, fname):
    local_filename = fname
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return local_filename

for x in range(1,pages + 1): 
	print ('Parsing page %d.' %x)
	for link in site.find_all("a", {"class": re.compile("thumbnail") }):

		img_url = link.get('href')
		if is_image.match(img_url):
			ctr += 1

			if img_url in downloaded:
				continue
			else:
				downloaded.append(img_url)
		
			
			ext = img_url[img_url.rfind(".") + 1: img_url.rfind(".") + 4]

			file_name = "%s/%d.%s" %(folder_name,ctr,ext)
			try:
				download_file(img_url, file_name)
				size_of_pic = os.path.getsize(file_name)
				if size_of_pic < 1000: #not an image file
					os.remove(file_name)
					ctr -= 1
					continue


				size += int(size_of_pic)
			except Exception, e:
				print "Error occured : %s" %e

			print ("%s -- Page: %d -- Total Size: %d MB" %(img_url, x, round(size / 1024 / 1024, 4)))

		elif is_album.match(img_url):
			sites.append(img_url)


	for link in sites: #parse through albums
		site = BeautifulSoup(requests.get(link).text)
		album += 1
		for img in site.find_all("a", {"class":"zoom"}):
			img_url = img.get('href')
			if is_image.match(img_url):
				ctr += 1
				img_url = "http:" + img_url


				if img_url in downloaded:
					continue
				else:
					downloaded.append(img_url)

				ext = img_url[img_url.rfind(".") + 1: img_url.rfind(".") + 4]

				file_name = "%s/A%d-%d.%s" %(folder_name,album,ctr,ext)
				
				try:
					download_file(img_url, file_name )
					size_of_pic = os.path.getsize(file_name)
					if size_of_pic < 1000: #not an image file
						os.remove(file_name)
						ctr -= 1
						continue
						
					size += int(size_of_pic)
				except:
					continue

				print ("%s -- Page: %d -- Total Size: %d MB" %(img_url, x, round(size / 1024 / 1024, 4)))



	time.sleep(2)

	tmp = 0
	while True:
		tmp += 1
		try:
			next_btn = driver.find_element_by_partial_link_text("next").click()
			break
		except:
			print ("Failed to locate Next Button... retrying...")
			time.sleep(5) #if failed, wait 5 seconds before trying again
			if tmp == 5:
				
				sys.exit("Error: Next page button not found, exiting. Network issue or with reddit.\nLast URL: %s" %driver.current_url)
				driver.close()
			continue



	html_source = driver.page_source
	site = BeautifulSoup(html_source)

print ("%d Pictures downloaded, %d MB in total, taking %d seconds." %(ctr, round(size / 1024 / 1024, 4), time.clock() - start_time ) )
print ("Last URL parsed: %s" %driver.current_url)
driver.close()