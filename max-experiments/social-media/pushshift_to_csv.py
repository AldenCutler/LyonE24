import json
import csv
from multiprocessing import Pool, cpu_count

def get_keywords(keywords_file='transit_keywords.txt'):
    with open(keywords_file, 'r') as f:
        keywords = f.read().splitlines()
    return keywords

def get_locations(keywords_file='transit_system_keywords.txt'):
    with open(keywords_file, 'r') as f:
        keywords = f.read().splitlines()
    return keywords

def process_line(line, keywords, locations=['lyon', 'paris', 'tokyo', 'boston', 'seattle', 'london', 'new york', 'nyc', 'berlin', 'prague']):
    line_lower = line.lower()
    if any(keyword.lower() in line_lower for keyword in keywords):
        try:
            entry = json.loads(line)
            num_keywords = sum(1 for keyword in keywords if keyword in line_lower)
            return {
                'link_id': entry.get('link_id', ''),
                'subreddit': entry.get('subreddit', ''),
                'ups': entry.get('ups', 0),
                'downs': entry.get('downs', 0),
                'body': entry.get('body', ''),
            }
        except json.JSONDecodeError:
            return None
    return None

def worker(line_and_keywords):
    line, keywords = line_and_keywords
    return process_line(line, keywords)

def export_to_csv(input_filename, output_filename):
    keywords = get_keywords()
    locations = get_locations()
    max_comments = 100000

    num_comments_processed = 0
    num_keyword_comments = 0

    with open(input_filename, 'r') as infile, open(output_filename, 'w', newline='') as csvfile:
        fieldnames = ['link_id', 'subreddit', 'ups', 'downs', 'body']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        with Pool(cpu_count()) as pool:
            for result in pool.imap(worker, ((line, keywords) for line in infile), chunksize=5000):
                num_comments_processed += 1

                if num_comments_processed % 50000 == 0:
                    print(f"{round(num_keyword_comments / max_comments * 100, 1)}% Complete.. ({num_keyword_comments} comments)")

                if num_keyword_comments > max_comments:
                    break

                if result:
                    
                    writer.writerow(result)
                    num_keyword_comments += 1

    print(f"Saved {num_keyword_comments} comments out of {max_comments} ({round(num_keyword_comments / max_comments * 100, 6)}%)")

if __name__ == '__main__':
    year = "2010"
    month = "04"
    input_filename = f'./RC_{year}-{month}'  # Replace with your input file name
    output_filename = f'out/reddit_comments_{year}_{month}_keywords.csv'  # Replace with your desired output file name
    export_to_csv(input_filename, output_filename)

