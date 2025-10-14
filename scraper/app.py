import argparse
import sys

def run_scraper(args):
    from scraper import run_scraper
    run_scraper(num_workers=args.workers)

def main():
    parser = argparse.ArgumentParser(
        description="🏍️ Vehicle Data Pipeline: crawler + scraper"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    # --- scraper ---
    scrape_parser = subparsers.add_parser("scrape", help="Scrape specs and HTML for pending models")
    scrape_parser.add_argument("--workers", type=int, default=2, help="Number of parallel workers")
    scrape_parser.set_defaults(func=run_scraper)

    # Parse and dispatch
    args = parser.parse_args()

    try:
        args.func(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
