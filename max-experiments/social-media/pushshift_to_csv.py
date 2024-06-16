import json
import csv

def get_keywords(keywords_file='transit_keywords.txt'):
    with open(keywords_file, 'r') as f:
        keywords = f.readlines()
        f.close()
    return keywords



def export_to_csv(input_filename, output_filename):
    keywords = get_keywords()
    num_comments = sum(1 for _ in open(input_filename))
    
    num_comments_processed = 0
    num_keyword_comments = 0
    
    # Open the input file for reading
    with open(input_filename, 'r') as infile, open(output_filename, 'w', newline='') as csvfile:
        fieldnames = ['link_id', 'subreddit', 'ups', 'downs', 'body']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write the header row to the CSV file
        writer.writeheader()


        # Read and process the input file line by line
        for line in infile:
            
            num_comments_processed += 1
            
            if num_comments_processed % 50000 == 0:
                print(f"{round(num_comments_processed/num_comments*100, 1)}% Complete..")
            
            skip = True
            for keyword in keywords:
                if keyword in line:
                    skip = False
                    break
            if skip:
                continue
            
            num_keyword_comments += 1
            
            try:
                entry = json.loads(line)
                writer.writerow({
                    'link_id': entry.get('link_id', ''),
                    'subreddit': entry.get('subreddit', ''),
                    'ups': entry.get('ups', 0),
                    'downs': entry.get('downs', 0),
                    'body': entry.get('body', '')
                })
            except json.JSONDecodeError:
                # Handle JSON parsing errors
                print(f"Skipping invalid JSON line: {line}")
                
    print(f"Saved {num_keyword_comments} comments out of {num_comments} ({round(num_keyword_comments/num_comments*100, 6)}%)")
# Example usage
input_filename = 'data/RC_2010-04'  # Replace with your input file name
output_filename = 'out/reddit_2010_04.csv'  # Replace with your desired output file name
export_to_csv(input_filename, output_filename)

