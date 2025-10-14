import argparse
import sys

def crawl_brands():
    from crawler import crawl_brands
    crawl_brands()

def crawl_models():
    from crawler import crawl_models
    crawl_models()

def main():
    parser = argparse.ArgumentParser(
        description="🏍️ Vehicle Data Pipeline: crawl brands or models from Bikez.com"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- crawl command ---
    crawl_parser = subparsers.add_parser(
        "crawl",
        help="Crawl and collect new motorcycle data (brands or models)"
    )

    group = crawl_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--brands", action="store_true", help="Crawl and insert new brands")
    group.add_argument("--models", action="store_true", help="Crawl and insert new models by year")

    crawl_parser.set_defaults(func=run_crawl_command)

    # Parse and dispatch
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def run_crawl_command(args):
    """Decide which crawler to run based on flags."""
    if args.brands:
        crawl_brands()
    elif args.models:
        crawl_models()
    else:
        print("⚠️ Please specify either --brands or --models")
        sys.exit(1)


if __name__ == "__main__":
    main()
