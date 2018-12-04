from shared_functions import parse_arguments
import sys
import boto3
import json
import os

def del_user():
    client = boto3.client('iam',
                          region_name=region,
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
    print("Try delete policy with same name as user: {}".format(delete_user))
    try:
        client.detach_user_policy(
            UserName=delete_user,
            PolicyArn=data["policyARN"]
        )
        client.delete_policy(
            PolicyArn=data["policyARN"]
        )
    except Exception as e:
        print("WARNING : Something wrong while delete user policy, skipping")
        print(e)
        pass
    client.delete_access_key(
        UserName=delete_user,
        AccessKeyId=data["accessKey"]
    )
    client.delete_user(
        UserName=delete_user
    )


region, access_key, secret_key, _, delete_user = parse_arguments()
if not delete_user:
    print("Please specify --delete-user")
    sys.exit(1)
states_dir = "states/"
state_file = states_dir + delete_user
data = json.load(open(state_file))
del_user()
print("Romove state file")
os.remove(state_file)