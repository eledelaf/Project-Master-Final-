import trafilatura

def scrape_and_text(url, filename=None):
    """
    Download a webpage and return the main article text using trafilatura.
    """

    try:
        # 1) Download the HTML
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"[trafilatura] Could not download: {url}")
            return None

        # 2) Extract the main text (article body)
        text = trafilatura.extract(
            downloaded,
            output_format="txt",      # plain text
            include_comments=False,
            include_tables=False,
            include_images=False
        )

        if not text:
            print(f"[trafilatura] Could not extract text from: {url}")
            return None

        return text

    except Exception as e:
        print(f"[trafilatura] Error with {url}: {e}")
        return None
