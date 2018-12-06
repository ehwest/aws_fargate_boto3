`create_user.py` - create user with policy declared in `user_policy.json`. arguments to input: region, aceess key, secret key  
`create_infrastructure.py` - create infrastructure (VPC, ALB, Target Group, ECS Cluster, Task Definition, Service) and run `wnameless/mysql-phpmyadmin` docker container. arguments to input: region, aceess key, secret key   
`destroy_infrastructure.py` - destroy infrastructure. arguments to input: region, aceess key, secret key and state-file. When you create user/infrastructure script will write internal data in JSON format to `states/XXXXX` file which will contain needed data to destroy/remove   
`delete_user.py` - delete user. arguments to input: region, aceess key, secret key and delete-user  
`check_infrastructure.py` - script check infrastructure. arguments to input: dnsname (ALB DNS public address)  
`shared_functions.py` - contains shared functions between all scripts  

### Step by step guide  
0) Install requirements  
`pip3 install -r requirements.txt`  
1) Create user  
`python3 create_user.py --region us-east-1 --access-key AAAA --secret-key ZZZZ`  
New user created!  
User: fargate-user-1544100575  
Access Key ID: XXXXXXXXX  
Secret Access Key ID: YYYYYYYY   
SUCCESS: State states/fargate-user-1544100575 save on disk  
2) Make deploy  
`python3 create_infrastructure.py --region us-east-1 --access-key XXXXXX --secret-key YYYYYYYY`  
Create Network (VPC, Subnets)  
Create Security Groups  
Create Target Group  
Create ALB   
upw-test-985554023.us-east-1.elb.amazonaws.com  
Create cluser  
Create task definition  
Create service  
SUCCESS: State states/1544100736 save on disk  
3) Get ALB DNS name and check that cluster ready. You need wait sometime for cluster setup. You will see "Ready to work"     
python3 check_infrastructure.py upw-test-985554023.us-east-1.elb.amazonaws.com`  
http://upw-test-985554023.us-east-1.elb.amazonaws.com/phpmyadmin response 502  
Lets wait 10 seconds  
`...`  
*Ready to work*  
4) Destroy infrastructure. Provide state file (you can find it on step 2)    
`python3 destroy_infrastructure.py --region us-east-1 --access-key XXXXXXX --secret-key YYYYYYYY --state-file states/1544100736`  
Remove ALB  
Remove ECS cluster  
Lets wait 60 second for stopping tasks  
Remove task definition  
Remove target group  
Remove VPC  
Lets wait 60 seconds  
Romove state file  
5) Remove user. Provide user to delete (you can find it on step 1)  
`python3 delete_user.py --region us-east-1 --access-key AAAAAA --secret-key ZZZZZZZ --delete-user fargate-user-1544100575`  
 Try delete policy with same name as user: fargate-user-1544100575  
 Romove state file 
 