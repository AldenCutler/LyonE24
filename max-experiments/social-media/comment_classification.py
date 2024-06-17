import csv
import torch
from transformers import pipeline, DistilBertTokenizer, AutoTokenizer, AutoModelForSequenceClassification

def get_locations(keywords_file='transit_system_keywords.txt'):
    with open(keywords_file, 'r') as f:
        keywords = f.read().splitlines()
    return keywords

def classify_comments(input_filename, output_filename):
    device = torch.device("mps") if torch.has_mps else torch.device("cpu")
    print(f"Using {device} for PyTorch")
    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    sentiment_pipeline = pipeline("sentiment-analysis", model=model_name, device=device)
    topic_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device)
    tokenizer = DistilBertTokenizer.from_pretrained(model_name)
    locations = get_locations()
    
    with open(input_filename, 'r') as infile:
        reader = csv.DictReader(infile)
        total_comments = sum(1 for row in reader)
        print(f"Got {total_comments} comments")
        infile.seek(0)  # Reset reader to the beginning of the file

        with open(output_filename, 'w', newline='') as csvfile:
            reader = csv.DictReader(infile)
            fieldnames = ['link_id', 'subreddit', 'ups', 'downs', 'num_keywords', 'location', 'sentiment_label', 'sentiment_score', 'about_other_prob', 'about_transit_prob', 'body']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            done_comments = 0

            for row in reader:
                done_comments += 1

                if done_comments % 5 == 0:
                    print(f"{round(done_comments / total_comments * 100, 2)}% done..")

                body = row['body']
                
                body_lower = str(row).lower()
                
                if not any(location in body_lower for location in locations):
                    continue
                
                location_comment = None
                for location in locations:
                    if location in body_lower:
                        location_comment = location
                        break

                tokens = tokenizer.encode(body, add_special_tokens=True, truncation=True, max_length=500)

                truncated_body = tokenizer.decode(tokens, clean_up_tokenization_spaces=True)

                sentiment_result = sentiment_pipeline(truncated_body)[0]
                row['sentiment_label'] = sentiment_result['label']
                row['sentiment_score'] = sentiment_result['score']

                # Tell if it is about public transit or not
                labels = ["comment with topic of transit", "comment not focusing on transit that mentions transit"]
                result_classify = topic_classifier(body, labels)
                scores = result_classify['scores']

                row['about_transit_prob'] = float(scores[0])
                row['about_other_prob'] = float(scores[1])
                
                row['location'] = location_comment
                
                if row['about_other_prob'] == float(scores[1]) > 0.3:
                    continue

                writer.writerow(row)

if __name__ == '__main__':
    input_filename = 'out/reddit_comments_2022_01_keywords.csv'  # Replace with your input file name
    output_filename = 'out/reddit_top_10m_reddit_comments_2022_01_classified.csv'  # Replace with your desired output file name
    classify_comments(input_filename, output_filename)
