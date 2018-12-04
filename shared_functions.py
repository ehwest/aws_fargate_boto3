import argparse


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", required=True)
    parser.add_argument("--access-key", required=True)
    parser.add_argument("--secret-key", required=True)
    parser.add_argument("--state-file", required=False)
    parser.add_argument("--delete-user", required=False)
    args = parser.parse_args()
    return args.region,\
           args.access_key,\
           args.secret_key,\
           args.state_file if args.state_file else False,\
           args.delete_user if args.delete_user else False
