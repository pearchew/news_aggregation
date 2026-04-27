import urllib.request
import json
from datetime import datetime, timedelta, timezone

# Configuration
TOKEN = "fm5s2FoN_YsNt-zvc3qtPRpfJ8w2JlSZPhBqFztw15s"
API_URL = "https://api.producthunt.com/v2/api/graphql"

def fetch_top_products(posted_after, posted_before, limit=10):
    """
    Fetches the top products from Product Hunt for a given timeframe.
    """
    
    # We define the GraphQL query with variables to keep it clean and prevent string-formatting errors.
    query = """
    query GetTopProducts($postedAfter: DateTime, $postedBefore: DateTime, $limit: Int) {
      posts(first: $limit, order: VOTES, postedAfter: $postedAfter, postedBefore: $postedBefore) {
        edges {
          node {
            name
            tagline
            description
            votesCount
            url
          }
        }
      }
    }
    """
    
    variables = {
        "postedAfter": posted_after,
        "postedBefore": posted_before,
        "limit": limit
    }
    
    # Prepare the payload and headers
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(API_URL, data=payload, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    
    # Execute the request
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            if "errors" in response_data:
                print("GraphQL Errors:", response_data["errors"])
                return []
            return response_data["data"]["posts"]["edges"]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def print_products(title, edges):
    """
    Helper function to cleanly print the product data to the terminal.
    """
    print(f"\n========== {title.upper()} ==========\n")
    if not edges:
        print("No products found for this timeframe.")
        return

    for i, edge in enumerate(edges, 1):
        node = edge["node"]
        name = node.get("name", "Unknown")
        votes = node.get("votesCount", 0)
        tagline = node.get("tagline", "")
        description = node.get("description", "No description available.")
        url = node.get("url", "")
        
        # Terminal output formatting
        print(f"{i}. {name} | ⬆ {votes} Upvotes")
        print(f"   Tagline: {tagline}")
        print(f"   Desc:    {description}")
        print(f"   Link:    {url}")
        print("-" * 50)

# --- Execution Logic ---

if __name__ == "__main__":
    # Calculate timestamps using UTC to align with Product Hunt's server time
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    # Format strictly to ISO 8601 strings required by the Product Hunt API
    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    day_ago_str = day_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    week_ago_str = week_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Fetch and print top 10 of the day
    daily_posts = fetch_top_products(posted_after=day_ago_str, posted_before=now_str)
    print_products("Top Products of the Day", daily_posts)

    # Fetch and print top 10 of the week
    weekly_posts = fetch_top_products(posted_after=week_ago_str, posted_before=now_str)
    print_products("Top Products of the Week", weekly_posts)