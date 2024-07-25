```bash
#alphartc执行命令
#检查log文件，停止后不删除文件的alphartc容器：
sudo docker run -d -v `pwd`/examples/peerconnection/serverless/corpus:/app -w /app --name alphartc alphartc peerconnection_serverless receiver_pyinfer.json
#执行代码
sudo docker exec alphartc peerconnection_serverless sender_pyinfer.json
#查看log日志
docker logs alphartc
#删除已经停止的容器
sudo docker rm alphartc
```

***注意修改pyinfer.json中的各种指标***

### 尝试修改autoclose=90，回传信息正确，90s正常进行传输
原视频规格height:240 width:320 fps:10
### 尝试修改源文件，查看是否能够满足90s，视频的传输
视频规格height:360 width:640 fps:24


sudo docker run -d -v `pwd`/examples/peerconnection/serverless/corpus:/app -w /app --name alphartc alphartc peerconnection_serverless receiver_pyinfer.json
sudo docker run -d --rm -v `pwd`/examples/peerconnection/serverless/corpus:/app -w /app --name alphartc_pyinfer opennetlab.azurecr.io/challenge-env peerconnection_serverless receiver_pyinfer.json
sudo docker run -d -v `pwd`/examples/peerconnection/serverless/corpus:/app -w /app --name alphartc_pyinfer opennetlab.azurecr.io/challenge-env peerconnection_serverless receiver_pyinfer.json
sudo docker rm alphartc_pyinfer