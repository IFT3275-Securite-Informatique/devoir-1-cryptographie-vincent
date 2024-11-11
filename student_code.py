from crypt import *
from adj_score_15 import *
from find_frequencies import *
from symboles import *
import json
from tqdm import tqdm




def replace_segment(segments, segment_to_replace, replacement_symbol):
    # Function that replaces a segment by a replacement symbol in a list of segments
    
    print("Segment ", segment_to_replace, " replaced by ", replacement_symbol)
    return [replacement_symbol if seg == segment_to_replace else seg for seg in segments]





def similar_frequency_score(segment, symbol, crypto_freq_dict, ref_freq_dict):
    # Function that calculates the frequency similarity score between a segment and a symbol
    # These scores are made up and use the relative ratio between the two frequencies
    
    if segment not in crypto_freq_dict:
        return 0
        
    crypto_freq = crypto_freq_dict[segment]
    ref_freq = ref_freq_dict[symbol]
    
    if ref_freq == 0:
        return 0
    
    relative_diff = abs(crypto_freq - ref_freq) / ref_freq
    return 1 / (1 + relative_diff)





def similar_adjacency_score_rest(segment, symbol, direction, crypto_adj_matrix, ref_adj_matrix, found_symbols):
    # Function that calculates the adjacency similarity score between a segment and a symbol
    # These scores are made up and use the relative ratio between the two frequencies
    # They seem to be working pretty well after we have found 15 symbols.

    if segment not in crypto_adj_matrix[direction]:
        return 0
    
    scores = []
    
    for known_symbol in found_symbols:
        crypto_freq = crypto_adj_matrix[direction][segment].get(known_symbol, 0)
        ref_freq = ref_adj_matrix[direction][symbol].get(known_symbol, 0)
        
        if crypto_freq > 0 or ref_freq > 0:
            if ref_freq == 0:
                scores.append(0)
            else:
                relative_diff = abs(crypto_freq - ref_freq) / ref_freq
                score = 1 / (1 + relative_diff)  
                scores.append(score)
    
    if not scores:
        return 0
        
    return sum(scores) / len(scores)





def decrypt(C):
    # Function that decrypts a cryptogram
    
    segments = [C[i:i+8] for i in range(0, len(C), 8)]
    
    # Get the reference values based on the corpus
    ref_freq_dict, ref_adj_matrix = find_relative_frequencies(symboles)
    
    found_symbols = set()
    available_symbols = set(symboles)
    available_segments = set(segments)

    # First calculation of the frequencies and the adjacency matrix for the segments
    crypto_freq_dict, crypto_adj_matrix = crypto_freq_adjacency_calculator(segments, found_symbols, 0.01)


    # First Iteration. This one specifically targets the symbol "e "
    sorted_crypto_freq_dict = sorted(crypto_freq_dict.items(), key=lambda x: x[1], reverse=True)
    sorted_ref_freq_dict = sorted(ref_freq_dict.items(), key=lambda x: x[1], reverse=True)

    most_frequent_segment = sorted_crypto_freq_dict[0][0]
    most_frequent_symbol = sorted_ref_freq_dict[0][0]
    
    available_symbols.remove(most_frequent_symbol)
    available_segments.remove(most_frequent_segment)
    found_symbols.add(most_frequent_symbol)


    segment_to_symbol = {most_frequent_segment: most_frequent_symbol}
    segments = replace_segment(segments, most_frequent_segment, most_frequent_symbol)

    # Criteria is used to determine the minimum scores to accept a match
    base_criteria = 0.6
    criteria = base_criteria
    
    # Performance is only respectable on the first 200 symbols or so.
    while len(found_symbols) < 200 and len(available_segments) > 0:
        
        # We start with the largest frequencies and progressively lower the threshold
        if len(found_symbols) < 8:
            threshold = 0.01
        elif len(found_symbols) < 15:
            threshold = 0.005
        elif len(found_symbols) < 40:
            threshold = 0.001
        else:
            threshold = 0.0
            
        # Calculate the frequencies and the adjacency matrix for the current segments
        crypto_freq_dict, crypto_adj_matrix = crypto_freq_adjacency_calculator(segments, found_symbols, threshold)
        scores_list = []  

        for segment in available_segments:
            
            if len(found_symbols) < 3:
                first_symbols = [[" d"], ["qu"]] # First symbols to consider with good performance
                available_symbols_to_consider = first_symbols[len(found_symbols)-1]
            else:
                # After the first 3 symbols, we consider all available symbols
                available_symbols_to_consider = available_symbols

            for symbol in available_symbols_to_consider:
              
                # We use different scoring methods for the first 15 symbols
                if len(found_symbols) < 15:
                  frequency_score = similar_frequency_score(segment, symbol, crypto_freq_dict, ref_freq_dict)  
                  next_adjacency_score = similar_adjacency_score_first_15(segment, symbol, "next", crypto_adj_matrix, ref_adj_matrix, found_symbols)
                  prev_adjacency_score = similar_adjacency_score_first_15(segment, symbol, "prev", crypto_adj_matrix, ref_adj_matrix, found_symbols)
                else:
                  frequency_score = similar_frequency_score(segment, symbol, crypto_freq_dict, ref_freq_dict)  
                  next_adjacency_score = similar_adjacency_score_rest(segment, symbol, "next", crypto_adj_matrix, ref_adj_matrix, found_symbols)
                  prev_adjacency_score = similar_adjacency_score_rest(segment, symbol, "prev", crypto_adj_matrix, ref_adj_matrix, found_symbols)

                score = 0

                # The criteria are different for the first 3, 9 and 50 symbols
                # This seems to improve performance upon trial and error
                if len(found_symbols) < 3:
                  score = (frequency_score * 0.15 + 
                          next_adjacency_score * 0.25 + 
                          prev_adjacency_score * 0.60) if next_adjacency_score >= 0.2 and prev_adjacency_score >= 0.2 else 0
                elif len(found_symbols) < 9:
                  if frequency_score > criteria and next_adjacency_score > criteria and prev_adjacency_score > base_criteria:
                    score = (frequency_score * 0.15 + 
                            next_adjacency_score * 0.25 + 
                            prev_adjacency_score * 0.60)
                  else:
                    score = 0
                elif len(found_symbols) < 50:
                  if frequency_score >= criteria*0.5 and next_adjacency_score >= criteria*0.75 and prev_adjacency_score >= criteria:
                    score = (frequency_score * 0.2 + 
                            next_adjacency_score * 0.4 + 
                            prev_adjacency_score * 0.4)
                  else:
                    score = 0
                else:
                  if frequency_score >= criteria*0.5 and next_adjacency_score >= criteria*0.75 and prev_adjacency_score >= criteria*0.75:
                    score = (frequency_score * 0.1 + 
                            next_adjacency_score * 0.45 + 
                            prev_adjacency_score * 0.45)
                  else:
                    score = 0

                # Store the scores that are non-zero for further processing
                if score > 0:  
                    scores_list.append({
                        'score': score,
                        'segment': segment,
                        'symbol': symbol,
                        'frequency_score': frequency_score,
                        'next_score': next_adjacency_score,
                        'prev_score': prev_adjacency_score
                    })

        # Sort the scores in descending order
        scores_list.sort(key=lambda x: x['score'], reverse=True)
        
        # Reduces the criteria if no valid matches are found
        if not scores_list:
            if criteria > 0:
                criteria = max(criteria - base_criteria * 0.1, 0)
                continue
            else:
                print("No valid matches found!")
                break
            
        # Use the best match and update the data structures accordingly
        best_match = scores_list[0]
        available_symbols.remove(best_match['symbol'])
        available_segments.remove(best_match['segment'])
        found_symbols.add(best_match['symbol'])
        segment_to_symbol[best_match['segment']] = best_match['symbol']
        segments = replace_segment(segments, best_match['segment'], best_match['symbol'])
        criteria = base_criteria

    # Replace the segments that are not decrypted by dots. 
    decrypted_segments = []
    for seg in segments:
        if seg in found_symbols:
            decrypted_segments.append(seg)
        else:
            decrypted_segments.append(".")
    
    decrypted_text = "".join(decrypted_segments)

    return decrypted_text


