# Array of investing-related subreddits
SUBREDDITS=(
    "wallstreetbets"
)

# Directory to store subreddit content
SUBREDDIT_DIR="reddit_data"
mkdir -p "$SUBREDDIT_DIR"

# Function to download subreddit posts
download_subreddit() {
    local subreddit="$1"
    echo "Downloading top posts from r/$subreddit..."
    curl "https://www.reddit.com/r/$subreddit/top.json?t=day&limit=100" > "$SUBREDDIT_DIR/$subreddit.json"
}

# Download content from each subreddit
for subreddit in "${SUBREDDITS[@]}"; do
    download_subreddit "$subreddit"
done

# Analyze the subreddit data using dir-assistant
echo "Analyzing sentiment of stocks mentioned in subreddits..."
cd "$SUBREDDIT_DIR"
ANALYSIS=$(dir-assistant -s "Using the attached reddit post data, analyze the sentiment of stock tickers mentioned and make a best effort guess of a sentiment score for tickers mentioned.  Return a list of the top 5 tickers with the most positive sentiment and the top 5 tickers with the most negative sentiment. Also return a score from -10.0 to 10.0 describing the sentiment of the tickers. Return ONLY a list of 10 tickers, 5 positive and 5 negative, and their sentiment scores with no other words. Format the data with one ticker per line a space and a sentiment score. Include no markdown, json, or other formatting. If any of this request is not possible, respond with a short message saying so (do not attempt to fix the issue). If data is provided, try your best to make sentiment scores using anything available.")

# Display the results
echo "Sentiment Analysis Results:"
echo "$ANALYSIS"

# Cleanup (optional)
#rm -r "$SUBREDDIT_DIR"
