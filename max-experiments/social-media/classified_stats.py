import pandas as pd

# Load the CSV file
file_path = 'out/reddit_top_10m_reddit_comments_2022_01_classified.csv'
df = pd.read_csv(file_path)

# Calculate the ratio of POSITIVE:NEGATIVE for each location
def calculate_ratio(df):
    
    
    
    # Filter out only the rows with POSITIVE and NEGATIVE classifications
    positive_df = df[df['sentiment_label'] == 'POSITIVE']
    negative_df = df[df['sentiment_label'] == 'NEGATIVE']
    
    # Group by location and count occurrences
    positive_counts = positive_df.groupby('location').size()
    negative_counts = negative_df.groupby('location').size()
    
    # Combine the counts into a single DataFrame
    combined_counts = pd.DataFrame({'POSITIVE': positive_counts, 'NEGATIVE': negative_counts}).fillna(0)
    
    # Calculate the ratio
    combined_counts['RATIO'] = combined_counts['POSITIVE'] / combined_counts['NEGATIVE']
    
    return combined_counts

# Calculate the ratios
ratios_df = calculate_ratio(df)

# Save the results to a new CSV file
output_file_path = 'out/location_positive_negative_ratios.csv'
ratios_df.to_csv(output_file_path)

print(f"Ratios calculated and saved to {output_file_path}")
