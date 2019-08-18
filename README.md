For the code simply run "python extractor.py"

find_movies_for_inp is the api function that takes in the search term and the imdbMovieDatabase object with the build_database function called beforehand

the build_database function can use build_names_mapping and build_names_mapping1

build_names_mapping extracts names from the whole cast list where build_names_mapping1 extracts just the name of casts present on the movie page

Creating a trie for fast searching