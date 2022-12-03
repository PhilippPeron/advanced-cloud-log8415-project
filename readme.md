## What's next?
- Current Problem: Slave node does not connect to master node
- Solution: Wait for solution in slack


## Standalone Benchmark
1. Create instance with 'python main.py --standalone'
2. SSH into instance using command printed in terminal
3. Execute over SSH 'sh cloud-log8415-project/remote/setup_standalone_mysql.sh' \
5. Copy results back with 'scp -i .\private_key_PROJECT_KEY.pem ubuntu@[IP]:/home/ubuntu/results_standalone.txt ./results_standalone.txt' 

- Copy files with: \
scp -i .\private_key_PROJECT_KEY.pem ./remote/setup_master_mysql.sh ubuntu@[IP]:/home/ubuntu/setup_master_mysql.sh 