import json
import csv
from multiprocessing import Pool, cpu_count
from transformers import pipeline, DistilBertTokenizer

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

            if not any(location in line_lower for location in locations):
                return None

            return {
                'link_id': entry.get('link_id', ''),
                'subreddit': entry.get('subreddit', ''),
                'ups': entry.get('ups', 0),
                'downs': entry.get('downs', 0),
                'num_keywords': num_keywords,
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
    num_comments = sum(1 for _ in open(input_filename))

    num_comments_processed = 0
    num_keyword_comments = 0

    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)
    tokenizer = DistilBertTokenizer.from_pretrained(model_name)

    with open(input_filename, 'r') as infile, open(output_filename, 'w', newline='') as csvfile:
        fieldnames = ['link_id', 'subreddit', 'ups', 'downs', 'num_keywords', 'sentiment_label', 'sentiment_score', 'body']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        with Pool(cpu_count()) as pool:
            for result in pool.imap(worker, ((line, keywords) for line in infile), chunksize=1000):
                num_comments_processed += 1

                if num_comments_processed % 50000 == 0:
                    print(f"{round(num_comments_processed / num_comments * 100, 1)}% Complete..")

                if result:
                    body = result['body']
                    tokens = tokenizer.encode(body, add_special_tokens=True, truncation=True, max_length=500)

                    truncated_body = tokenizer.decode(tokens, clean_up_tokenization_spaces=True)

                    sentiment_result = sentiment_pipeline(truncated_body)[0]
                    result['sentiment_label'] = sentiment_result['label']
                    result['sentiment_score'] = sentiment_result['score']
                    writer.writerow(result)
                    num_keyword_comments += 1

    print(f"Saved {num_keyword_comments} comments out of {num_comments} ({round(num_keyword_comments / num_comments * 100, 6)}%)")

if __name__ == '__main__':
    input_filename = 'data/RC_2010-04'  # Replace with your input file name
    output_filename = 'out/reddit_2010_04.csv'  # Replace with your desired output file name
    export_to_csv(input_filename, output_filename)
