import boto3
#import argparse
import time
from shared_functions import parse_arguments
import os
import json


def write_state(policyARN, accessKey):
    if os.path.isfile(states_dir + username):
        print("WARNING: State {} already exists!".format(username))
        return
    else:
        with open(states_dir + username, "w") as newfile:
            result = {"policyARN": policyARN,
                      "accessKey": accessKey}
            newfile.write(json.dumps(result))
            print("SUCCESS: State {} save on disk".format(states_dir + username))


def create_user(region, access_key, secret_key, username, policy_name):
    client = boto3.client('iam',
                          region_name=region,
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
    client.create_user(UserName=username)
    create_policy = client.create_policy(
        PolicyName=policy_name,
        PolicyDocument=policy
    )
    policyARN = create_policy["Policy"]["Arn"]
    client.attach_user_policy(
        UserName=username,
        PolicyArn=policyARN
    )
    creds = client.create_access_key(UserName=username)
    return creds["AccessKey"]["AccessKeyId"], creds["AccessKey"]["SecretAccessKey"], policyARN


with open("user_policy.json") as p:
    policy = p.read()


global_identifier = str(int(time.time()))
states_dir = "states/"
username = "fargate-user-{}".format(global_identifier)
policy_name = username + "-policy"
region, access_key, secret_key, _, _ = parse_arguments()
new_key, new_secret, policyARN = create_user(region,
                                             access_key,
                                             secret_key,
                                             username,
                                             policy_name)

print("New user created!")
print()
print("User: {}".format(username))
print("Access Key ID: {}".format(new_key))
print("Secret Access Key ID: {}".format(new_secret))
write_state(policyARN, new_key)