import torch
from torch import nn
from torch.distributions import MultivariateNormal
import torch.nn.functional as F
import numpy as np
##HRCC网络代码
class ActorCritic(nn.Module):
    def __init__(self,state_dim,state_length,action_dim,exploration_param=0.05,epsilon=0.2,device="cpu"):
        super(ActorCritic,self).__init__()
        self.layer1_shape = 128
        self.layer2_shape = 128
        self.numFcInput = 6144
        self.rConv1d = nn.Conv1d(1,self.layer1_shape,3)
        self.dConv1d = nn.Conv1d(1,self.layer1_shape,3)
        self.lConv1d = nn.Conv1d(1,self.layer1_shape,3)
        self.pConv1d = nn.Conv1d(1,self.layer1_shape,3)
        self.oConv1d = nn.Conv1d(1,self.layer1_shape,3)
        self.cConv1d = nn.Conv1d(1,self.layer1_shape,3)

        self.rConv1d_critic = nn.Conv1d(1,self.layer1_shape,3)
        self.dConv1d_critic = nn.Conv1d(1,self.layer1_shape,3)
        self.pConv1d_critic = nn.Conv1d(1,self.layer1_shape,3)
        self.lConv1d_critic = nn.Conv1d(1,self.layer1_shape,3)
        self.oConv1d_critic = nn.Conv1d(1,self.layer1_shape,3)
        self.cConv1d_critic = nn.Conv1d(1,self.layer1_shape,3)

        self.fc = nn.Linear(self.numFcInput,self.layer2_shape)
        #对应设计的动作域大小，采用线性层输出结果
        self.actor_output = nn.Linear(self.layer2_shape,action_dim)
        #对应观测到动作的奖励函数，因此输出为一个具体的数据
        self.critic_output = nn.Linear(self.layer2_shape,1)
        self.device = device
        self.action_var = torch.full((action_dim,),exploration_param**2).to(device)
        self.random_action = True
        self.epsilon = epsilon
        self.count = 0
        #True对应训练，False对应测试

    def forward(self,inputs):
        #actor
        # print(inputs)
        # print(inputs.shape)
        # self.count += 1
        receivingConv = F.relu(self.rConv1d(inputs[:,0:1,:]),inplace=True)
        delayConv = F.relu(self.dConv1d(inputs[:,1:2,:]),inplace=True)
        lossConv = F.relu(self.lConv1d(inputs[:,2:3,:]),inplace=True)
        predicationConv = F.relu(self.pConv1d(inputs[:,3:4,:]),inplace=True)
        overusedisConv = F.relu(self.oConv1d(inputs[:,4:5,:]),inplace=True)
        overusecapConv = F.relu(self.cConv1d(inputs[:,5:6,:]),inplace=True) 
        receiving_flattern = receivingConv.view(receivingConv.shape[0],-1)
        delay_flattern = delayConv.view(delayConv.shape[0],-1)
        loss_flattern = lossConv.view(lossConv.shape[0],-1)
        predication_flattern = predicationConv.view(predicationConv.shape[0],-1)
        overusedis_flattern = overusedisConv.view(overusedisConv.shape[0],-1)
        overusecap_flattern = overusecapConv.view(overusecapConv.shape[0],-1)

        merge = torch.cat([receiving_flattern,delay_flattern,loss_flattern,predication_flattern,overusedis_flattern,overusecap_flattern],1)
        fcOut = F.relu(self.fc(merge),inplace=True)
        action_mean = torch.sigmoid(self.actor_output(fcOut))
        cov_mat = torch.diag(self.action_var).to(self.device)
        dist = MultivariateNormal(action_mean,cov_mat)
        # if(self.count >= 500):
        #     self.random_action = False
        # else:
        #     self.random_action = True

        if not self.random_action:
            action = action_mean
        else:
            action = dist.sample()
        # if not self.random_action:
        #     action = action_mean
        # else:
        #     if np.random.random() < self.epsilon:
        #         action = dist.sample()
        #     else:
        #         action = action_mean
        action_logprobs = dist.log_prob(action)
        #critic
        receivingConv_critic = F.relu(self.rConv1d_critic(inputs[:,0:1,:]),inplace=True)
        delayConv_critic = F.relu(self.dConv1d_critic(inputs[:,1:2,:]),inplace=True)
        lossConv_critic = F.relu(self.lConv1d_critic(inputs[:,2:3,:]),inplace=True)
        predicationConv_critic = F.relu(self.pConv1d_critic(inputs[:,3:4,:]),inplace=True)
        overusedisConv_critic = F.relu(self.oConv1d_critic(inputs[:,4:5,:]),inplace=True) 
        overusecapConv_critic = F.relu(self.cConv1d_critic(inputs[:,5:6,:]),inplace=True)
        receiving_flattern_critic = receivingConv_critic.view(receivingConv_critic.shape[0],-1)
        delay_flattern_critic = delayConv_critic.view(delayConv_critic.shape[0],-1)
        loss_flattern_critic = lossConv_critic.view(lossConv_critic.shape[0],-1)
        predication_flattern_critic = predicationConv_critic.view(predicationConv_critic.shape[0],-1)
        overusedis_flattern_critic = overusedisConv_critic.view(overusedisConv_critic.shape[0],-1)
        overusecap_flattern_critic = overusecapConv_critic.view(overusecapConv_critic.shape[0],-1)
        merge_critic = torch.cat([receiving_flattern_critic,delay_flattern_critic,loss_flattern_critic,predication_flattern_critic,overusedis_flattern_critic,overusecap_flattern_critic],1)
        fcOut_critic = F.relu(self.fc(merge_critic),inplace=True)
        value = self.critic_output(fcOut_critic)
        return action.detach(),action_logprobs,value,action_mean

    def evaluate(self,state,action):
        _,_,value,action_mean = self.forward(state)
        cov_mat = torch.diag(self.action_var).to(self.device)
        dist = MultivariateNormal(action_mean,cov_mat)
        action_logprobs = dist.log_prob(action)
        dist_entropy = dist.entropy()
        return action_logprobs,torch.squeeze(value),dist_entropy    
