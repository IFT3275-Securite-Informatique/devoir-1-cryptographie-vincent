from crypt import *
import os
import json
import random
from tqdm import tqdm
from symboles import *

def crypto_freq_adjacency_calculator(segments, found_symbols, threshold):
    # Function that calculates the frequencies and the adjacency matrix for a given set of segments

    # Calculate the frequencies of the segments
    freq_dict = {}
    total = len(segments)
    
    # First pass to calculate all frequencies
    for segment in segments:
        freq_dict[segment] = freq_dict.get(segment, 0) + 1
    
    freq_dict = {k: v/total for k, v in freq_dict.items() if (v/total) >= threshold}
    
    # Create the adjacency matrix
    adj_matrix = {
        'next': {},
        'prev': {}
    }
    
    # Initialize the dictionaries for all segments
    all_segments = set(segments)  
    for segment in all_segments:
        adj_matrix['next'][segment] = {symbol: 0 for symbol in found_symbols}
        adj_matrix['prev'][segment] = {symbol: 0 for symbol in found_symbols}
    
    # Calculate the transitions in both directions
    for i in range(len(segments)):
        current = segments[i]
            
        # Transitions to the next item
        if i + 1 < len(segments):
            next_item = segments[i + 1]
            if next_item in found_symbols:
                adj_matrix['next'][current][next_item] += 1
        
        # Transitions from the previous item
        if i > 0:
            prev_item = segments[i - 1]
            if prev_item in found_symbols:
                adj_matrix['prev'][current][prev_item] += 1
    
    # Normalize the adjacency matrices only for segments above the threshold
    filtered_segments = set(freq_dict.keys())
    normalized_adj_matrix = {
        'next': {},
        'prev': {}
    }
    
    for direction in ['next', 'prev']:
        for segment in filtered_segments: 
            segment_count = freq_dict[segment] * total
            if segment_count > 0:
                normalized_adj_matrix[direction][segment] = {k: v/segment_count 
                                                          for k, v in adj_matrix[direction][segment].items()}
    
    return freq_dict, normalized_adj_matrix




def ref_freq_adjacency_calculator(corpus, symboles, symboles_to_consider):
    # Function that calculates the frequencies and the adjacency matrix for a given corpus
    # Main difference with the crypto_freq_adjacency_calculator is the addition of the symboles_to_consider parameter
    
    freq_dict = {symbol: 0 for symbol in symboles} 

    adj_matrix = {
        'next': {s1: {s2: 0 for s2 in symboles} for s1 in symboles},
        'prev': {s1: {s2: 0 for s2 in symboles} for s1 in symboles}
    }

    corpus_len = len(corpus)
    
    i = 0
    total = 0
    
    with tqdm(total=corpus_len, desc="Analysing frequencies and adjacency") as pbar:
        prev_symbol = None
        symbols_list = []  
        
        while i < len(corpus)-1:
            current_symbol = None
            
            # Try the bigram first
            if i + 1 < len(corpus):
                bigram = corpus[i:i+2]
                if bigram in symboles:
                    current_symbol = bigram
                    freq_dict[bigram] += 1
                    total += 1
                    i += 2
                    pbar.update(2)
                else:
                    # Otherwise, process the single character
                    char = corpus[i]
                    if char in symboles:
                        current_symbol = char
                        freq_dict[char] += 1
                        total += 1
                    i += 1
                    pbar.update(1)
            
            if current_symbol is not None:
                symbols_list.append(current_symbol)
        
        # Calculate the transitions in both directions
        for j in range(len(symbols_list)):
            current = symbols_list[j]
            
            # Transitions to the next item
            if j + 1 < len(symbols_list):
                next_symbol = symbols_list[j + 1]
                adj_matrix['next'][current][next_symbol] += 1
            
            # Transitions from the previous item
            if j > 0:
                prev_symbol = symbols_list[j - 1]
                adj_matrix['prev'][current][prev_symbol] += 1
        
        # Normalize the frequencies
        if total > 0:
            freq_dict = {k: v/total for k, v in freq_dict.items()}
        
        # Normalize the adjacency matrices
        for direction in ['next', 'prev']:
            for symbol in symboles:
                total_transitions = sum(adj_matrix[direction][symbol].values())
                if total_transitions > 0:
                    adj_matrix[direction][symbol] = {k: v/total_transitions 
                                                   for k, v in adj_matrix[direction][symbol].items()}

    # After normalization, create a new simplified adjacency matrix
    simplified_adj_matrix = {
        'next': {},
        'prev': {}
    }
    
    # For each symbol in the corpus
    for symbol in symboles:
        simplified_adj_matrix['next'][symbol] = {}
        simplified_adj_matrix['prev'][symbol] = {}
        
        # Keep only the adjacencies with the symbols to consider
        for target_symbol in symboles_to_consider:
            # Probability that this symbol is followed by a target symbol
            if target_symbol in adj_matrix['next'][symbol]:
                simplified_adj_matrix['next'][symbol][target_symbol] = adj_matrix['next'][symbol][target_symbol]
            else:
                simplified_adj_matrix['next'][symbol][target_symbol] = 0
                
            # Probability that this symbol is preceded by a target symbol
            if target_symbol in adj_matrix['prev'][symbol]:
                simplified_adj_matrix['prev'][symbol][target_symbol] = adj_matrix['prev'][symbol][target_symbol]
            else:
                simplified_adj_matrix['prev'][symbol][target_symbol] = 0

    return freq_dict, simplified_adj_matrix




def find_relative_frequencies(symboles):
    # Function that creates a corpus if it doesn't exist and calculates the frequencies and the adjacency matrix
    # The corpus is used as a reference to calculate the frequencies and the adjacency matrix of the cryptograms.

    # Check if the files already exist
    if (os.path.exists('frequencies.json') and 
        os.path.exists('adjacency.json') and 
        os.path.exists('corpus.txt') ):
        
        with open('frequencies.json', 'r', encoding='utf-8') as f:
            freq_dict = json.load(f)
        with open('adjacency.json', 'r', encoding='utf-8') as f:
            adj_matrix = json.load(f)
        return freq_dict, adj_matrix
    
    corpus = ""
    urls = ["https://www.gutenberg.org/ebooks/13846.txt.utf-8",
            "https://www.gutenberg.org/ebooks/4650.txt.utf-8",
            "https://www.gutenberg.org/ebooks/63979.txt.utf-8",
            "https://www.gutenberg.org/ebooks/72773.txt.utf-8",
            "https://www.gutenberg.org/ebooks/17808.txt.utf-8",
            "https://www.gutenberg.org/ebooks/18627.txt.utf-8",
            "https://www.gutenberg.org/ebooks/74061.txt.utf-8",
            "https://www.gutenberg.org/ebooks/60199.txt.utf-8",
            "https://www.gutenberg.org/ebooks/73832.txt.utf-8",
            "https://www.gutenberg.org/ebooks/28605.txt.utf-8",
            "https://www.gutenberg.org/ebooks/51591.txt.utf-8",
            "https://www.gutenberg.org/ebooks/36729.txt.utf-8",
            "https://www.gutenberg.org/ebooks/70369.txt.utf-8",
            "https://www.gutenberg.org/ebooks/48529.txt.utf-8",
            "https://www.gutenberg.org/ebooks/51666.txt.utf-8",
            "https://www.gutenberg.org/ebooks/68603.txt.utf-8",
            "https://www.gutenberg.org/ebooks/22394.txt.utf-8",
            "https://www.gutenberg.org/ebooks/52611.txt.utf-8",
            "https://www.gutenberg.org/ebooks/51405.txt.utf-8",
            "https://www.gutenberg.org/ebooks/43784.txt.utf-8"]
    

    for url in urls:
        current_corpus = load_text_from_web(url)
        if current_corpus: 
            # Existing corpus processing
            a = random.randint(round(0.0*len(current_corpus)), round(0.05*len(current_corpus)))
            b = random.randint(round(0.8*len(current_corpus)), round(0.90*len(current_corpus)))
            l = a+b
            c = random.randint(0, len(current_corpus)-l)
            current_corpus = current_corpus[c:c+l]
            corpus += current_corpus

    with open('corpus.txt', 'w', encoding='utf-8') as f:
        f.write(corpus)

    freq_dict, adj_matrix = ref_freq_adjacency_calculator(corpus, symboles, symboles)
    
    with open('frequencies.json', 'w', encoding='utf-8') as f:
        json.dump(freq_dict, f, ensure_ascii=False, indent=4, sort_keys=True)
    
    with open('adjacency.json', 'w', encoding='utf-8') as f:
        json.dump(adj_matrix, f, ensure_ascii=False, indent=4, sort_keys=True)
    
    return freq_dict, adj_matrix


find_relative_frequencies(symboles)