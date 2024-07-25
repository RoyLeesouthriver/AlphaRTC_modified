sudo rm /home/roylee/AlphaRTC/examples/peerconnection/serverless/corpus/webrtc.log
sudo docker rm alphartc
sudo docker run -d -v `pwd`/examples/peerconnection/serverless/corpus:/app -w /app --name alphartc alphartc peerconnection_serverless receiver_pyinfer.json
sudo docker exec alphartc peerconnection_serverless sender_pyinfer.json