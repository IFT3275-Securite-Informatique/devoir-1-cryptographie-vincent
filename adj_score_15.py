def similar_adjacency_score_first_15(segment, symbol, direction, crypto_adj_matrix, ref_adj_matrix, found_symbols):
    # The first 15 symbols are the hardest to decrypt and influence the rest of the decryption
    # It was really important to get this right. This is why this function is complex and separate from the rest
    # of the chars.

    # Hyperparameters for symbol association based on adjacency to other symbols
    ADJACENCY_THRESHOLD = 0.02  # Threshold for significant adjacency
    ADDITIONAL_ADJACENCY_BONUS = 1.02 # Bonus for each additional adjacency
    HIGH_FREQ_BONUS = 1.5 # Bonus for high frequencies that correspond
    HIGH_FREQ_THRESHOLD = 0.10  # Threshold for high frequencies
    MIN_CRYPTO_FREQ = 0.003 # Minimum frequency for a symbol to be considered significant
    MAX_MULTIPLIER = 3  # Maximum multiplier for additional adjacencies
    SINGLE_SCORE_PENALTY = 0.9  # Penalty for a single score (multiplier)
    
    if segment not in crypto_adj_matrix[direction]:
        return 0
    
    scores = []
    significant_adjacencies = False
    
    for known_symbol in found_symbols:
        crypto_freq = crypto_adj_matrix[direction][segment].get(known_symbol, 0)
        ref_freq = ref_adj_matrix[direction][symbol].get(known_symbol, 0)
        
        # If the reference is significant but our frequency is too low
        if ref_freq > 0.05 and crypto_freq < MIN_CRYPTO_FREQ:
            return 0
        
        # Check if at least one of the frequencies is significant
        if crypto_freq > ADJACENCY_THRESHOLD or ref_freq > ADJACENCY_THRESHOLD:
            significant_adjacencies = True
            if ref_freq == 0:
                scores.append(0)
                continue
            
            if crypto_freq == 0:
                scores.append(0)
                continue
            
            relative_diff = abs(crypto_freq - ref_freq) / ref_freq
            
            if crypto_freq > ref_freq:
                relative_diff = relative_diff * min(0.25 + 0.025*len(found_symbols), 0.5)
                
            score = max(0, 1 - relative_diff)
            
            # Bonus for corresponding high frequencies
            if (crypto_freq > HIGH_FREQ_THRESHOLD and 
                ref_freq > HIGH_FREQ_THRESHOLD and 
                abs(crypto_freq - ref_freq) / ref_freq <= 0.35):
                score *= HIGH_FREQ_BONUS
            
            scores.append(score)
    
    # If no significant adjacencies were found
    if not significant_adjacencies:
        return 0.25
        
    # If no valid score was calculated despite significant adjacencies
    if not scores:
        return 0
        
    # Calculate the average score
    avg_score = sum(scores) / len(scores)
    
    if len(scores) > 1:
        # Limit the multiplier
        bonus_multiplier = ADDITIONAL_ADJACENCY_BONUS ** min(MAX_MULTIPLIER, (len(scores) - 1))
        avg_score = min(1.0, avg_score * bonus_multiplier)
    else:
        # Penalize single scores
        avg_score *= SINGLE_SCORE_PENALTY
    
    return avg_score