#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modified 21-12-2021

@author: Elena Cristina Rusu Hutu

This script containt the dictionaries used in santalucia.py 
to calculate the AG of primer interactions
"""

# nucleotide pair matings
match_dict = {"A": "T", "C": "G", "G": "C", "T": "A"}

# AG energy from dinucleotide pairs (eg. 5'-AT-3' matches 3'-TA-5' and it's 0,88)
match_AG_dict = {"AT":-0.88, "TA":-0.60, "AA":-1.02, "TT":-1.02, "AC":-1.46, 
                 "GT":-1.46, "CA":-1.46, "TG":-1.46, "TC":-1.32, "GA":-1.32, 
                 "AG":-1.29, "CT":-1.29, "CG":-2.17, "GC":-2.24, "GG":-1.83, 
                 "CC":-1.83}

# First nucleotide is match, second one is hanging
overhang_AG_dict = {"AA": -0.51, "AC": -0.96, "AG": -0.58, "AT": -0.50, 
                    "CA": -0.42, "CC": -0.52, "CG": -0.34, "CT": -0.02, 
                    "GA": -0.62, "GC": -0.72, "GG": -0.56, "GT": -0.48, 
                    "TA": -0.71, "TC": -0.58, "TG": -0.61, "TT": -0.10, 
                    "none": 0}

# First nucleotide is matched, second one is hanging
overhang_AG_dict_groupB = {"TA": -0.48, "GA": -0.92, "CA": -0.82, "AA": -0.12, 
                    "TC": -0.19, "GC": -0.23, "CC": -0.31, "AC": 0.28, 
                    "TG": -0.50, "GG": -0.44, "CG": -0.01, "AG": -0.01, 
                    "TT": -0.29, "GT": -0.35, "CT": -0.52, "AT": 0.13, 
                    "none": 0}

# mismatch AG dictionary
mismatch_AG_dict = {"AG-T": 0.71, "AT-G": 0.07, "CG-T": -0.47, "CT-G": -0.32, "GG-T": 0.08, 
                    "GT-G": -0.59, "TG-T": 0.43, "TT-G": 0.34, "AA-C": 0.88, "AC-A": 0.77, 
                    "CA-C": 0.75, "CC-A": 0.79, "GA-C": 0.81, "GC-A": 0.47, "TA-C": 0.92, 
                    "TC-A": 1.33, "AC-T": 0.64, "AT-C": 0.73, "CC-T": 0.62, "CT-C": 0.40, 
                    "GC-T": 0.62, "GT-C": 0.98, "TC-T": 0.97, "TT-C": 0.75, "AA-G": 0.14, 
                    "AG-A": 0.02, "CA-G": 0.03, "CG-A": 0.11, "GA-G": -0.25, "GG-A": -0.52, 
                    "TA-G": 0.42, "TG-A": 0.74, "AA-A": 0.61, "CA-A": 0.43, "GA-A": 0.17, 
                    "TA-A": 0.69, "AC-C": 1.33, "CC-C": 0.70, "GC-C": 0.79, "TC-C": 1.05, 
                    "AG-G": -0.13, "CG-G": -0.11, "GG-G": -1.11, "TG-G": 0.44, "AT-T": 0.69, 
                    "CT-T": -0.12, "GT-T": 0.45, "TT-T": -0.51}


positional_dict1 = {"0": 5, "1": 5, "2": 5, "3": 4, "4": 4, 
                   "5": 4, "6": 3, "7": 2, "8": 2, "9": 2, 
                   "10": 1, "11": 1, "12": 1, "13": 1,
                   "14": 1, "15": 1, "16": 1, "17": 1, "18": 1,
                   "19": 1, "20": 1, "21": 0, "22": 0, "23": 0,
                   "24": 0, "25": 0, "26": 0, "27": 0, "28": 0,
                   "29": 0, "30": 0, "31": 0, "32": 0, "33": 0, "34": 0,
                   "35": 0, "36": 0, "37": 0, "38": 0, "39": 0, "40": 0,
                   "41": 0, "42": 0, "43": 0, "44": 0, "45": 0, "46": 0, 
                   "47": 0, "48": 0, "49": 0, "50": 0, "51": 0, "52": 0, 
                   "53": 0, "54": 0, "55": 0, "56": 0, "57": 0, "58": 0, 
                   "59": 0, "60": 0, "61": 0, "62": 0, "63": 0, "64": 0, 
                   "65": 0, "66": 0, "67": 0, "68": 0, "69": 0, "70": 0, 
                   "71": 0, "72": 0, "73": 0, "74": 0, "75": 0, "76": 0, 
                   "overhang" : 3, 
                   "overhang_groupB" : 0} # others are 0 


positional_dict2 = {"0": 2.5, "1": 2.5, "2": 2.5, "3": 2, "4": 2, 
                   "5": 2, "6": 1.7, "7": 1.7, "8": 1.5, "9": 1.5, 
                   "10": 1, "11": 1, "12": 1, "13": 1,
                   "14": 1, "15": 1, "16": 1, "17": 1, "18": 1,
                   "19": 1, "20": 1, "21": 0, "22": 0, "23": 0,
                   "24": 0, "25": 0, "26": 0, "27": 0, "28": 0,
                   "29": 0, "30": 0, "31": 0, "32": 0, "33": 0, "34": 0,
                   "35": 0, "36": 0, "37": 0, "38": 0, "39": 0, "40": 0,
                   "41": 0, "42": 0, "43": 0, "44": 0, "45": 0, "46": 0, 
                   "47": 0, "48": 0, "49": 0, "50": 0, "51": 0, "52": 0, 
                   "53": 0, "54": 0, "55": 0, "56": 0, "57": 0, "58": 0, 
                   "59": 0, "60": 0, "61": 0, "62": 0, "63": 0, "64": 0, 
                   "65": 0, "66": 0, "67": 0, "68": 0, "69": 0, "70": 0, 
                   "71": 0, "72": 0, "73": 0, "74": 0, "75": 0, "76": 0, 
                   "overhang" : 1, 
                   "overhang_groupB" : 1} # others are 0 

# double mismatch AG value
double_mismatch = 0.6
# Attempts were made in order to weight this according to the nucleotides, 
# but resulted less accurate when tunning with the PrimerROC data

NUM_CONSEC_MATCHES = (11, 10, 9, 8, 7, 6, 5, 4)
# AG val for 6 matches, 7 matches, ... 11 matches in the 3' end 
CONSEC_MATCHES_3END = (-31, -29, -27, -25, -22, -17, -7, -5) 
# AG val for 6 matches, 7 matches, ... 11 matches anywhere in the primer 
CONSEC_MATCHES = (-12, -10, -8, -6, -4, -2, -1, -1)



def create_positional_dict_queues(l, n1, n2, n3, overhang, overhangB): 
    """
    This function returns de positional_dict used for the queues alignment. This dict is
    individually created for every primer depending on its length, in order to ensure: 
    Half of the bases at the 3' of the primer will have a weight of 2
    Other half of the bases + 2 at the 5' of the primer will have a weight of 1
    Rest of the bases will have a weight of 0 (avoiding queue-queue alignment values)
    Args: 
        l               [in] (int) Length of the primer WITHOUT the queue
        positional_dict [out] (dict) Positional dict returned
    """
    positional_dict = {}
    for i in range(0, int(l/2)): 
        positional_dict[str(i)] = n1
    for i in range(int(l/2), l+1): 
        positional_dict[str(i)] = n2
    for i in range(l+1, 120): 
        positional_dict[str(i)] = n3
    
    positional_dict["overhang"] = overhang
    positional_dict["overhang_groupB"] = overhangB
        
    return positional_dict
    