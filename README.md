`create_user.py` - create user with policy declared in `user_policy.json`. arguments to input: region, aceess key, secret key  
`create_infrastructure.py` - create infrastructure (VPC, ALB, Target Group, ECS Cluster, Task Definition, Service) and run `wnameless/mysql-phpmyadmin` docker container. arguments to input: region, aceess key, secret key   
`destroy_infrastructure.py` - destroy infrastructure. arguments to input: region, aceess key, secret key and state-file. When you create user/infrastructure script will write internal data in JSON format to `states/XXXXX` file which will contain needed data to destroy/remove   
`delete_user.py` - delete user. arguments to input: region, aceess key, secret key and delete-user  
`check_infrastructure.py` - script check infrastructure. arguments to input: dnsname (ALB DNS public address)  
`shared_functions.py` - contains shared functions between all scripts  