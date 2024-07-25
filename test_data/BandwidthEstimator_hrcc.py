from deep_rl.ppo_agent_raw import PPO
import torch
from packet_info import PacketInfo
from packet_record import PacketRecord
from BandwidthEstimator_gcc import GCCEstimator

class Estimator(object):
    def __init__(self,model_path="ppo_2021_07_25_04_57_11_with500trace.pth",step_time=200):
        exploration_param = 0.1
        K_epochs = 37
        ppo_clip=0.1
        gamma=0.99
        lr=3e-5
        betas = (0.9,0.999)
        self.state_dim = 6
        self.state_length = 10
        action_dim = 1
        self.device = torch.device("cpu")
        self.ppo = PPO(self.state_dim,self.state_length,action_dim,exploration_param,lr,betas,gamma,K_epochs,ppo_clip)
        self.ppo.policy.load_state_dict(torch.load('ppo_2021_07_25_04_57_11_with500trace.pth'))
        self.packet_record = PacketRecord()
        self.packet_record.reset()
        self.step_time = step_time
        self.state = torch.zeros((1,self.state_dim,self.state_length))
        self.time_to_guide = False
        self.counter = 0
        self.bandwidth_prediction = 300000
        self.gcc_estimator = GCCEstimator()
        self.receiving_rate_list = []
        self.delay_list=[]
        self.loss_ratio_list = []
        self.bandwidth_prediction_list = []
        self.overuse_flag= 'NORMAL'
        self.overuse_distance = 5
        self.last_overuse_cap = 1000000
    
    def report_states(self,stats:dict):
        packet_info = PacketInfo()
        packet_info.payload_type = stats["payload_type"]
        packet_info.ssrc = stats["ssrc"]
        packet_info.sequence_number = stats["sequence_number"]
        packet_info.send_timestamp = stats["send_time_ms"]
        packet_info.receive_timestamp = stats["arrival_time_ms"]
        packet_info.padding_length = stats["padding_length"]
        packet_info.header_length = stats["header_length"]
        packet_info.payload_size = stats["payload_size"]
        packet_info.bandwidth_prediction = self.bandwidth_prediction

        self.packet_record.on_receive(packet_info)
        self.gcc_estimator.report_states(stats)
    
    def get_estimated_bandwidth(self)->int:
        self.receiving_rate = self.packet_record.calculate_receiving_rate(interval=self.step_time)
        self.receiving_rate_list.append(self.receiving_rate)
        self.delay = self.packet_record.calculate_average_delay(interval=self.step_time)
        self.delay_list.append(self.delay)
        self.loss_ratio = self.packet_record.calculate_loss_ratio(interval=self.step_time)
        self.loss_ratio_list.append(self.loss_ratio)

        self.gcc_decision,self.overuse_flag = self.gcc_estimator.get_estimated_bandwidth()
        if len(self.receiving_rate_list) == self.state_length:
            self.receiving_rate_list.pop(0)
            self.delay_list.pop(0)
            self.loss_ratio_list.pop(0)
        
        self.counter += 1

        if self.counter % 4 == 0:
            self.time_to_guide = True
            self.counter = 0
        
        if self.time_to_guide == True:
            action,_,_,_ = self.ppo.policy.forward(self.state)
            self.bandwidth_prediction = self.gcc_decision * pow(2,(2*action - 1))
            self.gcc_estimator.change_bandwidth_estimation(self.bandwidth_prediction)
            self.time_to_guide = False
        else:
            self.bandwidth_prediction = self.gcc_decision
        
        return self.bandwidth_prediction

