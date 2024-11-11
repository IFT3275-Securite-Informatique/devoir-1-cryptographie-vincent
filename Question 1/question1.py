import math
import random as rnd
import numpy as np
import requests
from collections import Counter
import gmpy2
import os
import json
from datetime import datetime, timedelta
from tqdm import tqdm


# SECTION FOR THE PROVIDED FUNCTIONS
# convert string to list of integer
def str_to_int_list(x):
  z = [ord(a) for a in x  ]
  for x in z:
    if x > 256:
      print(x)
      return False
  return z

# convert a strint to an integer
def str_to_int(x):
  x = str_to_int_list(x)
  if x == False:
    print("Le text n'est pas compatible!")
    return False

  res = 0
  for a in x:
    res = res * 256 + a
  i = 0
  res = ""
  for a in x:
    ci = "{:08b}".format(a )
    if len(ci)>8:
      print()
      print("long",a)
      print()
    res = res + ci
  res = eval("0b"+res)
  return res

# exponentiation modulaire
def modular_pow(base, exponent, modulus):
    result = 1
    base = base % modulus
    while exponent > 0:
        if (exponent % 2 == 1):
            result = (result * base) % modulus
        exponent = exponent >> 1
        base = (base * base) % modulus
    return result

def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

# inverse multiplicatif de a modulo m
def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception("Pas d'inverse multiplicatif")
    else:
      return x % m
    



# QUESTION 1.1
# Public key 
N = 143516336909281815529104150147210248002789712761086900059705342103220782674046289232082435789563283739805745579873432846680889870107881916428241419520831648173912486431640350000860973935300056089286158737579357805977019329557985454934146282550582942463631245697702998511180787007029139561933433550242693047924440388550983498690080764882934101834908025314861468726253425554334760146923530403924523372477686668752567287060201407464630943218236132423772636675182977585707596016011556917504759131444160240252733282969534092869685338931241204785750519748505439039801119762049796085719106591562217115679236583
e = 3

# Ciphertext
C = 1101510739796100601351050380607502904616643795400781908795311659278941419415375


# Direct square root attack based on the small e == 3
# We know that the cypher is a known public figure's name
print("Début de la question 1.1")

def encrypt_name(name, e, N):
    binary = ''.join(format(ord(c), '08b') for c in name)
    M = int(binary, 2)
    result = modular_pow(M, e, N)
    return result

def test_author(author_name, C, e, N):
    try:
        encrypted = encrypt_name(author_name, e, N)
        return encrypted == C
    except Exception as e:
        print(f"Erreur dans test_author: {e}")
        return False

def decode_message(cubic_root):
    binary = bin(int(cubic_root))[2:] 
    
    while len(binary) % 8 != 0:
        binary = '0' + binary
    
    message = ''
    for i in range(0, len(binary), 8):
        byte = binary[i:i+8]
        char_code = int(byte, 2)
        message += chr(char_code)
    
    return message

# We are using gmpy2 to handle big numbers with more precision
cubic_root, _ = gmpy2.iroot(C, 3)

## allow for some error
if abs(round(cubic_root) ** 3 - C) < 1000:
    message = decode_message(round(cubic_root))
    print(f"Message décodé: {message}")
else:
    print("L'attaque par racine cubique simple n'a pas fonctionné")
print()

# The answer is "Umberto Eco"




# QUESTION 1.2
# Public key
N = 172219604291138178634924980176652297603347655313304280071646410523864939208855547078498922947475940487766894695848119416017067844129458299713889703424997977808694983717968420001033168722360067307143390485095229367172423195469582545920975539060699530956357494837243598213416944408434967474317474605697904676813343577310719430442085422937057220239881971046349315235043163226355302567726074269720408051461805113819456513196492192727498270702594217800502904761235711809203123842506621973488494670663483187137290546241477681096402483981619592515049062514180404818608764516997842633077157249806627735448350463
e = 173

# Cyphertext
C = 25782248377669919648522417068734999301629843637773352461224686415010617355125387994732992745416621651531340476546870510355165303752005023118034265203513423674356501046415839977013701924329378846764632894673783199644549307465659236628983151796254371046814548224159604302737470578495440769408253954186605567492864292071545926487199114612586510433943420051864924177673243381681206265372333749354089535394870714730204499162577825526329944896454450322256563485123081116679246715959621569603725379746870623049834475932535184196208270713675357873579469122917915887954980541308199688932248258654715380981800909


print("Début de la question 1.1")

def clean_author_name(name):
    # Clean the author name to remove any non-alphabetic characters and split the 
    # name into first and last name
    # This format is based on the answer of question 1.1
    
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            last_name = parts[0].strip()
            first_name = parts[1].strip()
            if all(part.replace(' ', '').replace('-', '').isalpha() 
                  for part in [last_name, first_name]):
                return f"{first_name} {last_name}"
    
    return None


# Get the list of famous authors from the API
# We are going to fetch 10000 authors to make sure we have enough
def get_famous_authors(limit=10000):
    cache_file = 'authors_cache.json'
    
    # Check if the cache exists
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            try:
                cache_data = json.load(f)
                print("Utilisation du cache...")
                return cache_data['authors']
            except:
                print("Cache invalide, récupération depuis l'API...")
    
    base_authors = set()
    url = "https://gutendex.com/books/"
    page = 1
    
    print("Récupération des auteurs depuis l'API...")
    
    try:
        # This loop can take quite a while to run
        # This is why we are caching the results
        while len(base_authors) < limit:
            response = requests.get(f"{url}?page={page}")
            
            if response.status_code != 200:
                print(f"Erreur API: {response.status_code}")
                break
                
            data = response.json()
            
            for book in data['results']:
                for author in book['authors']:
                    if 'name' in author:
                        # We are cleaning the names according to the format of question 1.1
                        clean_name = clean_author_name(author['name'])
                        if clean_name:  
                            base_authors.add(clean_name)
            
            print(f"Récupéré {len(base_authors)} auteurs...")
            
            if not data['next']:
                break
                
            page += 1
            
    except Exception as e:
        print(f"Erreur: {e}")
    
    authors = list(base_authors)
    print(f"\nNombre total d'auteurs: {len(authors)}")
    print("Exemples d'auteurs:", authors[:5])
    
    # Save the results in the cache
    cache_data = {
        'authors': authors
    }
    with open(cache_file, 'w', encoding='utf-8') as file:
        json.dump(cache_data, file)
    
    return authors

# Usage of mpz to handle big numbers
N = N
e = 173
C = C

# Test the authors
authors = get_famous_authors()
print(f"Testing {len(authors)} authors...")

for author in tqdm(authors, desc="Testing authors"):
    # For each of our cleaned author names, we are testing if it matches the cyphertext
    if test_author(author, C, e, N):
        print(f"\nFound match: {author}")
        break

# The answer is "Marcel Proust"