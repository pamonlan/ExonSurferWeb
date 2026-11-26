#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 29 15:32:42 2021

@author: Elena Cristina Rusu Hutu
"""

# Imported modules
import re
from numpy import mean


# My modules
from . import santalucia_dictionaries as d

################################################################################################
#                                    FUNCTIONS DEFINITION SITE                                 #
################################################################################################
def add_matchbars(upperseq, belowseq):
    """
    This function is for printing que hybridization between two sequences. 
    Args: 
        upperseq [in] (str) Upper sequence, with hyphens
        belowseq [in] (str) Below sequence, with hyphens
        bars [out] (str) | indicate match, space indicate mismatch
        cutpost1, cutpos2 [out] (int) To print like seq[c1:-c2], bars[c1:-c2]
    """
    bars = ""
    for i in range(0, len(upperseq)): 
        if upperseq[i] == "-" or belowseq[i] == "-": 
            bars = bars + " "
        elif upperseq[i] == d.match_dict[belowseq[i]]: 
            bars = bars + "|"
        else: 
            bars = bars + " "
    try: 
        cutpos1 = re.search("\|", bars).start() - 20
        cutpos2 = re.search("\|", bars[::-1]).start() - 20
    except: 
        cutpos1 = 0
        cutpos2 = 0
    return bars, cutpos1, cutpos2

################################################################################################

def sequential_matches(upperseq, belowseq, bars, minval): 
    """
    This function adds the values from CONSEC_MATCHES_3END and CONSEC_MATCHES to 
    minval in case there are NUM_CONSEC_MATCHES[i] matches in the 3' end or 
    elsewhere, respectively. 
    Args: 
        upperseq, belowseq [in] (str)
        bars [in] (str)
        minval [in|out] (float)
    
    """
    i = 0
    modified = False
    while i < len(d.NUM_CONSEC_MATCHES) and modified == False: 
        
        
        if "|"*d.NUM_CONSEC_MATCHES[i] in bars: 
            multimatch_i = re.search("\|"*d.NUM_CONSEC_MATCHES[i], bars).start()
            subs1 = upperseq[multimatch_i-1:multimatch_i+1]
            subs2 = belowseq[multimatch_i-1:multimatch_i+1]

            pat = "^-?[ACTG]{1}-?$"
            if re.match(pat, subs1) or re.match(pat, subs2): 
                minval = minval + d.CONSEC_MATCHES_3END[i]
                modified = True
            
            else: 
                # try in opposite direction
                multimatch_i = re.search("\|"*d.NUM_CONSEC_MATCHES[i], bars).end()
                subs1 = upperseq[multimatch_i-1:multimatch_i+1]
                subs2 = belowseq[multimatch_i-1:multimatch_i+1]
    
                pat = "^-?[ACTG]{1}-?$"
                if re.match(pat, subs1) or re.match(pat, subs2): 
                    minval = minval + d.CONSEC_MATCHES_3END[i]
                    modified = True
                
                else: 
                    minval = minval + d.CONSEC_MATCHES[i]
        i += 1
        
    return minval

################################################################################################

def AG_per_seq(seq1, seq2, pd, addminvals): 
    """
    This function calculates all the AG values for all the possible alignments between two DNA
    sequences, taking into account the positional weights for each sequence independently. 
    Args: 
        seq1, seq2 [in] (str) DNA String (Eg "ACTACCTGGG")
        all_AGvals [out] (list) List of sublists, one sublist per each alignment, and every sublist 
                                contains 2 floats (AG value), one per sequence.
        od
    """

    # rename sequences according to length
    if len(seq1) == len(seq2): 
        longest_s = seq1
        shortest_s = seq2
    else: 
        shortest_s = min((seq1, seq2), key = len)
        longest_s = max((seq1, seq2), key = len)
    
    rseq2 = shortest_s[::-1] # reversed (3' -> 5')
    upperseq = "-"*len(shortest_s) + longest_s + "-"*len(shortest_s) # longest is upper
    uppernum = "-."*len(shortest_s) + ".".join([str(x) for x in reversed(range(len(longest_s)))]) + ".-"*len(shortest_s)
    maxiter =  len(shortest_s) + len(longest_s) - 1 
    
    all_AGvals = [] # to return
    
    for i in range(2, maxiter): # iterate every possible alignment
        #print(i)
        belowseq = "-" * i + rseq2 
        difflen = len(upperseq) - len(belowseq)
        belownum = "-." * i + ".".join([str(x) for x in range(len(shortest_s))]) + ".-"*difflen
        
        belowseq = belowseq + "-"*difflen
        #print(upperseq)
        #print(belowseq + "\n")
        
        minval = AG_per_alignment(s1 = upperseq, s2 = belowseq, 
                                   a1 = uppernum, a2 = belownum, posdict = pd)
        
        if addminvals == True: 
            bars, c1, c2 = add_matchbars(upperseq, belowseq)
            
            minval = sequential_matches(upperseq, belowseq, bars, minval)
            """
            if minval < -10: 
                print("{}\n{}\n{}\nAG: {}".format(upperseq[c1:-c2], 
                                            bars[c1:-c2], 
                                            belowseq[c1:-c2], minval))  
            """
        all_AGvals.append(minval)
        #print("AG: {}\n".format(twovals))
        #print("*"*50)
    return all_AGvals


################################################################################################

def AG_per_alignment(s1, s2, a1, a2, posdict):
    """ 
    This function calculates the AG value for a specific alignment between 2 seqs
    Args: 
        s1,s2 [in] (str) DNA 5'-3' strings (uppercase) with hanging '-'
            Eg: s1 = "------TACCACTGG------" # 5' -> 3'
                s2 = "---------GGGCCCAT-----" # 3' -> 5'
        a1,a2 [in] (str) Position number (starting from the 3') delimited by '.'
            Eg: a1 = "-.-.-.-.-.-.8.7.6.5.4.3.2.1.0.-.-.-.-.-.-.-"
                a2 = "-.-.-.-.-.-.-.-.-.0.1.2.3.4.5.6.7.-.-.-.-.-"
        AGvals [out] (list) List of 2 floats, calculated for every seq separately
    """    
    a1 = a1.split(".")
    a2 = a2.split(".")
    
    o1 = "" # overlapping part form first seq (Eg CACTGG)
    o2 = "" # overlapping part form second seq (Eg GGGCCC)
    p1 = [] # iterator list for first seq (Eg ['4', '3', '2', '1', '0'])
    p2 = [] # iterator list for second seq (Eg ['0', '1', '2', '3', '4'])
    for i in range(0, len(s1)): 
        if s1[i] != "-" and s2[i] != "-": 
            o1 = o1 + s1[i]
            o2 = o2 + s2[i]
            p1.append(a1[i])
            p2.append(a2[i])
    p1 = p1[1:]
    p2 = p2[:-1]
    
    AGvals = []
    for p in (p1, p2):  # positional places are calculated once for every seq (return list of 2)
        
        AGvalue = 0
        #print("I am using p: {}".format(p))
        for i in range(0, len(o1)-1): 
            if i % 2 == 0: # even positions -> first seq
                dn1 = o1[i:i+2]
                dn2 = o2[i:i+2]  
            else:  # odd positions -> second seq
                dn1 = o2[i:i+2][::-1]
                dn2 = o1[i:i+2][::-1]        
            
            
            if d.match_dict[dn1[0]] == dn2[0] and d.match_dict[dn1[1]] == dn2[1]: 
                # both nucleotides match
                #print("match_AG_dict[dn1]: {} * {}".format(match_AG_dict[dn1], positional_dict[p[i]]))
                AGvalue += d.match_AG_dict[dn1] * posdict[p[i]]
            elif d.match_dict[dn1[0]] == dn2[0]: # but the other do not match
                #print("mismatch_AG_dict[dn1]: {} * {}".format(mismatch_AG_dict[dn1+"-"+dn2[1]], positional_dict[p[i]]))
                AGvalue += d.mismatch_AG_dict[dn1+"-"+dn2[1]] * posdict[p[i]]
            elif d.match_dict[dn1[1]] == dn2[1]: 
                # hay que hacerlo al reves
                #print("mismatch_AG_dict[dn1]: {} * {}".format(mismatch_AG_dict[dn2[::-1]+"-"+dn1[0]], positional_dict[p[i]]))
                AGvalue += d.mismatch_AG_dict[dn2[::-1]+"-"+dn1[0]] * posdict[p[i]]  
            else: 
                #print("doble mismatch!!")
                AGvalue += d.double_mismatch * posdict[p[i]] # valor tuneado con ROC      
                #mismatch = double_mismatch_dict[dn1[0]+dn1[0]] + double_mismatch_dict[dn1[1]+dn1[1]]
                #AGvalue = AGvalue + mismatch * positional_dict[p[i]]
        # add overhang value    
        if p == p1: # first seq
            try: 
                pos = re.search("[ACTG]-", s1).start()
            except: 
                print("nonetype object has not attribute start. S1: {}".format(s1))
            if "-" not in s2[pos:(pos+2)]: # s2 overhangs
                if s1[pos] == d.match_dict[s2[pos]]: # theres is a match in the last base
                    AGvalue = AGvalue + d.overhang_AG_dict[s2[pos:(pos+2)][::-1]] * posdict["overhang"]
        else: # second seq
            pos = re.search("-[ACTG]", s2).start() + 1
            if "-" not in s1[pos-1:pos+1]:
                if s1[pos] == d.match_dict[s2[pos]]: 
                    AGvalue = AGvalue + d.overhang_AG_dict[s1[(pos-1):(pos+1)]] * posdict["overhang"]
        AGvals.append(AGvalue)
    
    
    return min(AGvals)
        
################################################################################################

def calculate_min_AG(seq1, seq2, queue1, queue2, pd = d, addminvals = True, correct = True): 
    """
    This function calculates the minimum AG value between two primers
    Args: 
        seq1,seq2      [in] (str) DNA sequence (uppercase)
        queue1, queue2 [in] (str) DNA sequence of queues (uppercase)
        pd             [in] (d)   Positional dict (from santalucia_dictionaries)
        addminvals     [in] (bool) True in order to penalize consecutive matches (3' end or total)
        correct        [in] (bool) True in order to make GC and len correction
        value          [out] (float) Minimum AG value (weighted by position)

    """
    AGs = AG_per_seq(seq1, seq2, pd, addminvals)
    value = min(AGs) 
    #print("AG before correction: {}".format(value), end = "")
    if correct == "hola": 
        # i do not know if seq1 or seq2 are forward or reverse primers
        p1 = seq1.replace(queue1, "")
        p1 = p1.replace(queue2, "")
        p2 = seq2.replace(queue1, "")
        p2 = p2.replace(queue2, "")
        
        gc1 = ("G".count(p1) + "C".count(p1)) / len(p1)
        gc2 = ("G".count(p2) + "C".count(p2)) / len(p2)
        value = value / 2 * (len(p1) + len(p2)) # length adjustment
        value = value + value * 2.25 * mean([gc1, gc2]) # GC adjustment

    
    value = round(value, 3)
    #print("AG AFTER correction; {}".format(value))
    return value

