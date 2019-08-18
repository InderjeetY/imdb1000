import re
import requests
from bs4 import BeautifulSoup
from urlparse import urljoin
from collections import defaultdict

class imdbMovieDatabase(object):
	def __init__(self):
		# different datasets
		# direct map of movies url to it's name and cast
		self.movies_map = {}
		# map a cast's name to the set of movies urls
		self.names_to_movie = defaultdict(set)
		# creating a trie with casts names
		# names will be split on space and then added to the tries
		# makes extraction of movies faster
		# the trie stores the urls that will be uesd to fetch movie
		# names from movies_map
		self.names_to_movie_trie = dict()

	# function only looks at cast in the movies page
	def build_names_mapping1(self, movie_url, movie_name):
		# fetching html page for the movie
		r = requests.get(movie_url)
		movie_soup = BeautifulSoup(r.text, 'html.parser')
		movie_details = movie_soup.find('div', {'class':re.compile('plot_summary .*')})

		# fetch all movie summary items
		movie_summary_items = movie_details.findAll('div', {'class':'credit_summary_item'})
		
		# loop over summary items and extract names
		# 3 possible summary's are directors, writers and actors
		for movie_summary_item in movie_summary_items:
			# extract all names in the summary
			names_list = [names.text.lower() for names in movie_summary_item.findAll('a')]
			self.movies_map[movie_url].update({
				movie_summary_item.find('h4').text[:-1].lower(): names_list
			})
			# loop over the names
			for names in names_list:
				# the list might contain "see full cast list"
				if 'cast' in names:
					continue
				self.names_to_movie[names].add(movie_url)
				# split names by space
				names_parts = names.split(' ')
				# create the trie
				for names_part in names_parts:
					mapping_names = self.names_to_movie_trie
					# only storing name parts in length longer than 2
					if len(names_part)>2:
						for ch in names_part:
							if ch not in mapping_names:
								mapping_names[ch] = dict()
							mapping_names = mapping_names[ch]
						if 'movie_urls' not in mapping_names:
							mapping_names['movie_urls'] = set()
						mapping_names['movie_urls'].add(movie_url)

	# function fetches the whole cast of the movie
	def build_names_mapping(self, movie_url, movie_name):
		# fetching html page for the movie
		r = requests.get(movie_url)
		movie_soup = BeautifulSoup(r.text, 'html.parser')

		# get the url for the whole cast
		movie_details = movie_soup.find('a', {'href':re.compile('fullcredits/?.*')})
		movie_credit_list = urljoin(movie_url, movie_details['href'])

		# fetch the whole page of the cast
		r = requests.get(movie_credit_list)
		movie_credit_soup = BeautifulSoup(r.text, 'html.parser')
		# extracting the div of the whole cast
		movie_credit_soup = movie_credit_soup.find('div', {'id':'fullcredits_content'})
		# fetching all the names in the div
		movie_char_names = movie_credit_soup.findAll('a', {'href':re.compile('/name/.*')})
		
		# loop over the names
		for movie_char_name in movie_char_names:
			movie_char_name = movie_char_name.text.lower().strip()
			self.names_to_movie[movie_char_name].add(movie_url)
			# split the name by space and generate the trie
			names_parts = movie_char_name.split(' ')
			for names_part in names_parts:
				mapping_names = self.names_to_movie_trie
				if len(names_part)>2:
					for ch in names_part:
						if ch not in mapping_names:
							mapping_names[ch] = dict()
						mapping_names = mapping_names[ch]
					if 'movie_urls' not in mapping_names:
						mapping_names['movie_urls'] = set()
					mapping_names['movie_urls'].add(movie_url)

	# function to build the database
	def build_database(self):
		# base url
		URL = "https://www.imdb.com/search/title/?groups=top_1000&sort=user_rating&view=simple"
		while True:
			# fetch the page with the list of the movies
			r = requests.get(URL)
			page_soup = BeautifulSoup(r.text, 'html.parser')
			# extract the movie block
			movie_blocks = page_soup.findAll('div', {'class':'lister-item-content'})
			# loop over the blocks to extract details
			for movie_block in movie_blocks:
				# movie name
				movie_name = movie_block.find('a').text

				# movie page extraction
				movie_url = urljoin(URL, movie_block.find('a')['href'])

				# movie map
				self.movies_map[movie_url] = {
					'movie_name': movie_name
				}

				self.build_names_mapping(movie_url, movie_name)

			# get nexet page and break if there isn't any
			next_page_content = page_soup.find('a', {'class':'lister-page-next next-page'})
			if not next_page_content:
				break
			URL = urljoin(URL, next_page_content['href'])

# takes the search term part in whole and database object
def find_movies(search_term, imdbMovieDatabaseObj):
	# search the term in the trie
	names_to_movie_trie = imdbMovieDatabaseObj.names_to_movie_trie
	movies_map = imdbMovieDatabaseObj.movies_map
	for ch in search_term:
		names_to_movie_trie = names_to_movie_trie.get(ch, {})
		if not names_to_movie_trie:
			break
	return set([
		movies_map[movie_url]['movie_name'] \
		for movie_url in names_to_movie_trie.get('movie_urls', set())
	])

# the main api function that recieves the database object and input
def find_movies_for_inp(inp, imdbMovieDatabaseObj):
	# check if the input is in the names_to_movie mapping
	# if not split the inputs and create an intersection
	# for the movies for them
	res = imdbMovieDatabaseObj.names_to_movie.get(inp.lower())
	if not res:
		res = None
		for inp_part in inp.split(' '):
			fetched_movies = find_movies(inp_part.lower(), imdbMovieDatabaseObj)
			if not fetched_movies:
				break
			if not res:
				res = fetched_movies
			else:
				res = res.intersection(fetched_movies)
	else:
		res = set([imdbMovieDatabaseObj.movies_map[r]['movie_name'] for r in res])
	return res

def main():
	# create an instance of the databse class and build the database
	imdbMovieDatabaseObj = imdbMovieDatabase()
	imdbMovieDatabaseObj.build_database()

	# ask for input and send it to the api
	while True:
		print "Enter search value, if you want to break just press enter"
		inp = raw_input()
		if not inp:
			break
		print find_movies_for_inp(inp, imdbMovieDatabaseObj)

if __name__=='__main__':
	main()