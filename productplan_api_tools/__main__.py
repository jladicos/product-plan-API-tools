"""
Entry point for ProductPlan API Tools

Usage:
    python -m productplan_api_tools [arguments]

This makes the package executable while keeping the module structure clean.
"""

def main():
    """Main entry point"""
    from productplan_api_tools.cli import parse_arguments, route_command

    args = parse_arguments()
    route_command(args)


if __name__ == "__main__":
    main()
