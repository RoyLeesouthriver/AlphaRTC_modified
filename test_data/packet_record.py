import numpy as np

class PacketRecord:
    #可以修改特征回传间隔
    def __init__(self,base_delay_ms=0):
        self.base_delay_ms = base_delay_ms
        self.reset()
    
    def reset(self):
        self.packet_num = 0
        self.packet_list = [] #ms
        self.last_seqNo = {}
        self.timer_delta = None #ms
        self.min_seen_delay = self.base_delay_ms #ms
        self.last_interval_rtime = None #ms 记录上一个时隙内最后一个数据包的接收时间

    def clear(self):
        self.packet_num = 0
        if self.packet_list:
            #不为空，将lir记录为上一个时隙内最后一个数据包的时间戳
            self.last_interval_rtime = self.packet_list[-1]['timestamp']
        self.packet_list = []
    
    def on_receive(self,packet_info):
        # print("packet received!")
        assert (len(self.packet_list) == 0
                or packet_info.receive_timestamp
                >= self.packet_list[-1]['timestamp']),\
                "The incoming packets receive_timestamp disordered!"
        #计算丢包率
        loss_count = 0
        if packet_info.ssrc in self.last_seqNo:
            loss_count = max(0,packet_info.sequence_number - self.last_seqNo[packet_info.ssrc] - 1)
            #SSRC:同一个SSRC发送的数据包具有相同的时序和序列号间隔，因此可以基于SSRC将收到的数据包进行分组和排序
        self.last_seqNo[packet_info.ssrc] = packet_info.sequence_number
        #计算时延
        if self.timer_delta is None:
            #将基准时延作为第一个数据包的时延
            ##修改：delay一直是0，能不能不采用basedelay与其相减。 
            self.timer_delta = self.base_delay_ms - (packet_info.receive_timestamp - packet_info.send_timestamp)
            # self.timer_delta = (packet_info.receive_timestamp - packet_info.send_timestamp)
        delay = self.timer_delta + (packet_info.receive_timestamp - packet_info.send_timestamp)
        # delay = (packet_info.receive_timestamp - packet_info.send_timestamp)
        self.min_seen_delay = min(delay,self.min_seen_delay)

        #同步上次的lir
        if self.last_interval_rtime is None:
            self.last_interval_rtime = packet_info.receive_timestamp
        
        #记录当前数据包的相关数据
        packet_result = {
            'timestamp':packet_info.receive_timestamp,# ms
            'delay':delay,# ms
            'payload_byte':packet_info.payload_size, # Byte
            'loss_count':loss_count, #p
            'bandwidth_prediction':packet_info.bandwidth_prediction #bps
        }
        self.packet_list.append(packet_result)
        self.packet_num += 1
    
    def _get_result_list(self,interval,key):
        if self.packet_num == 0:
            return []
        result_list = []
        if interval == 0:
            interval = self.packet_list[-1]['timestamp'] - self.last_interval_rtime
        start_time = self.packet_list[-1]['timestamp'] - interval
        index = self.packet_num - 1
        while index >= 0 and self.packet_list[index]['timestamp'] > start_time:
            result_list.append(self.packet_list[index][key])
            #key:读取目标的数据
            index -= 1
        return result_list
    
    def calculate_average_delay(self,interval=0):
        '''
        计算上一个间隔时间内的平均时延
        interval=0代表基于所有的数据包进行计算
        单位为ms
        '''
        delay_list = self._get_result_list(interval=interval,key = 'delay')
        if  delay_list:
            return np.mean(delay_list) - self.base_delay_ms
            # return np.mean(delay_list)
        else:
            return 0
    
    def calculate_loss_ratio(self,interval=0):
        '''
        计算上一时间间隔内的平均丢包
        interval=0对应所有数据包进行统计
        返回值为packet/packet
        '''
        loss_list = self._get_result_list(interval=interval,key='loss_count')
        if loss_list:
            loss_num = np.sum(loss_list)
            received_num = len(loss_list)
            return loss_num / (loss_num + received_num)
        else:
            return 0
    
    def calculate_receiving_rate(self,interval=0):
        '''
        计算上一时隙内的接收速率
        interval=0对应所有数据包的信息
        单位为bps
        '''
        received_size_list = self._get_result_list(interval=interval,key='payload_byte')
        if received_size_list:
            received_nbytes = np.sum(received_size_list)
            if interval == 0:
                interval = self.packet_list[-1]['timestamp'] - self.last_interval_rtime
            return received_nbytes * 8 / interval * 1000
        else:
            return 0
    
    def calculate_latest_prediction(self):
        '''
        计算返回值bps
        '''
        if self.packet_num > 0:
            return self.packet_list[-1]['bandwidth_prediction']
        else:
            return 0


