# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.
 



"""Pcapy sniffer that parses packets and publishes a summary data dictionary indexed by IP address and a data_key"""


import sys
import pygeoip
import sys
import zmq
import zmq.auth
import time
import netifaces
import json
import os
import argparse
from requests import get

from threading import Thread
from pcapy import findalldevs, open_live, DLT_EN10MB, DLT_LINUX_SLL
from uuid import getnode as get_mac #identify mac address
from impacket.ImpactDecoder import EthDecoder, LinuxSLLDecoder
from impacket.ImpactPacket import IP


from multiprocessing import Process

   #DELETE SOON: old array structure: [packet_count 0, tcp_count 1, udp_count 2, icmp_count 3, data_into_mycomputer 4, data_out_of_mycomputer 5, new_packet_boolean 6, blank_boolean 7, delta_time 8, stream_data 9, collect_data_flag 10, geoip_info 11]



class Sniffer(Process): 
    """
    Pcapy open_live() packet sniffer that utilizies Impacket to parse packets and ZMQ PUB/SUB and Client/Server to transmit summmary data dictionary -> self.sniffer_data["ip_key"]["data_key"] and additional commands.

    For each IP in self.sniffer_data use any of these dictionary keys:

    packet_count
    tcp_count
    udp_count
    icmp_count
    data_in
    data_out
    new_packet_booleans
    blank_boolean
    delta_time
    stream_data
    collect_data_flag
    geoip_info

    e.g. self.sniffer_data['129.129.0.1']['packet_count']

    """


    def __init__(self, port = None) -> None:
        """Construct self.pcapy_sniffer"""

        super(Sniffer, self).__init__()

        print(port)
        if port is None:
            req_port = 20000
            sub_port = 20001
        else:
            req_port = port
            sub_port = req_port + 1


          



        self.mac_dict = {} #store mac address for each interface
        self.sniffer_dictionary = {} #Sniffed data will be stored here!

        self.sniffer_publish_to_client = True
        self.keep_alive = True
        self.active_sniffing = True

        self.city_database = pygeoip.GeoIP("../assets/geolocation/GeoLiteCity.dat") #geolocation database lookup of ip's
        self.old_time = time.time()
        self.type_ip = IP()
        self.dev = self.getInterface()
        self.pcapy_sniffer = open_live("en0", 1500, 0, 100)



        #identify correct Impacket Decoder() to use for datalink layer
        datalink = self.pcapy_sniffer.datalink()
        if DLT_EN10MB == datalink:
            self.decoder = EthDecoder()
        elif DLT_LINUX_SLL == datalink:
            self.decoder = LinuxSLLDecoder()
        else:
            raise Exception("Datalink type not supported: " % datalink)



        try:

            from zmq.asyncio import Context
            from zmq.auth.asyncio import AsyncioAuthenticator
            context = zmq.Context()

            #context = Context.instance()
            

            # auth_location = (
            #     zmq.auth.CURVE_ALLOW_ANY
            # )
            
            # Configure the authenticator
            # self.auth = AsyncioAuthenticator(context=context)
            # self.auth.configure_curve(domain="*", location=auth_location)
            # self.auth.allow("136.36.144.135")
            # self.auth.start()


            self.publish_socket = context.socket(zmq.PUB)
            
            keys = zmq.auth.load_certificate("../configuration/keys/server.key_secret")
            self.publish_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.publish_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.publish_socket.setsockopt(zmq.CURVE_SERVER, True)
            self.publish_socket.bind(f"tcp://*:{sub_port}")  

            self.msg_from_client_socket = context.socket(zmq.REP)
            self.msg_from_client_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.msg_from_client_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.msg_from_client_socket.setsockopt(zmq.CURVE_SERVER, True)
            self.msg_from_client_socket.bind(f"tcp://*:{req_port}")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            sys.exit("Issue with ZMQ setup! Try closing any old sniffy.py python processes.")
       



        self.run()
        




    def run(self) -> None : 
        """Called after Thread.start() - Start pcapy packet sniffing loop"""

    
        while self.keep_alive:

            current_time = time.time()
            delta_time = current_time - self.old_time 


            self.check_for_client_commands()
            
            #only send data dictionary after 1 second and client is asking for data
            if delta_time > 1 and self.sniffer_publish_to_client == True:

                self.old_time = current_time
                self.publish_data_to_clients()
                    
            if self.active_sniffing == True:
               

                try:
                    header, packet = self.pcapy_sniffer.next()
                    self.parse_packet(header, packet)
                except Exception as e:
                    pass
                #<class 'TypeError'> sniffy.py 129
                #<class 'AttributeError'> sniffy.py 129
                
                    # exc_type, exc_obj, exc_tb = sys.exc_info()
                    # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    # print(exc_type, fname, exc_tb.tb_lineno)
                    #print(e) #probably trying to parse NoneType
        


    
    def parse_packet(self, packet_header: object , packet_data: object ) -> None:

        """
        Called for each packet. Parse revelevant data and add to self.sniffer_dictionary[IP_Address][data_key]

        """

        #print(type(packet_header))
        #print(self.decoder.decode(packet_header).get_bytes())
        # print(type(packet_data))
        # print(packet_data.get_bytes())

      
        #TODO: confirm new timestamp calculation doesnt create downstream bugs
        timestamp = packet_header.getts() #returns tuple (seconds, microseconds) of the header
        timestamp = timestamp[0] + (float(timestamp[1])/1000000)

        ethernet_packet = self.decoder.decode(packet_data)
        ip_packet = ethernet_packet.child()
        transmision_packet  = ip_packet.child()
        payload = transmision_packet.child()



        #Only parsing IP packets to start
        if type(ethernet_packet.__dict__['_ProtocolLayer__child']) == type(self.type_ip): #find better way to check for IP protocol!

            source_IP_address = ip_packet.get_ip_src()
            destination_IP_address = ip_packet.get_ip_dst()
            transmission_protocol = ip_packet.get_ip_p()
            number_of_bytes_of_data = len(payload.get_bytes())
         
           

        
        
            if ethernet_packet.as_eth_addr(ethernet_packet.get_ether_dhost()) in self.mac_dict: #packet inbound (recieved)
            
                #print("Packet Inbound!")
                #print(ethernet_packet.as_eth_addr(ethernet_packet.get_ether_dhost()), "<--destination mac")
                #print(ethernet_packet.as_eth_addr(ethernet_packet.get_ether_shost()), "<--source mac")

                ip_index = source_IP_address #store appropraite ip_index for self.sniffer_dictionary entry
                geoip_info = self.city_database.record_by_addr(ip_index)
                
                

                if ip_index in self.sniffer_dictionary: # Previous self.sniffer_dictionary entry found
                    
                    self.sniffer_dictionary[ip_index]['packet_count'] += 1
                    self.sniffer_dictionary[ip_index]['new_packet_boolean'] = True
                    self.sniffer_dictionary[ip_index]['delta_time'] = timestamp
                    self.sniffer_dictionary[ip_index]['data_in'] += number_of_bytes_of_data
                    

                else: #initalize new self.sniffer_dictionary entry for new inbound packet
        
                    self.sniffer_dictionary[ip_index] = {} 

                    self.sniffer_dictionary[ip_index]['packet_count'] = 1
                    self.sniffer_dictionary[ip_index]['tcp_count'] = 0
                    self.sniffer_dictionary[ip_index]['udp_count'] = 0
                    self.sniffer_dictionary[ip_index]['icmp_count'] = 0
                    self.sniffer_dictionary[ip_index]['data_in'] = number_of_bytes_of_data  #data inbound
                    self.sniffer_dictionary[ip_index]['data_out'] = 0 #data outbound
                    self.sniffer_dictionary[ip_index]['new_packet_boolean'] = True
                    self.sniffer_dictionary[ip_index]['blank_boolean'] = False ##rename?
                    self.sniffer_dictionary[ip_index]['delta_time'] = timestamp
                    self.sniffer_dictionary[ip_index]['stream_data'] = ''
                    self.sniffer_dictionary[ip_index]['collect_data_flag'] = False
                    self.sniffer_dictionary[ip_index]['geoip_info'] = geoip_info
                    
                  
                    
                

                #TODO: use TCPdump and save to pcap file?
                if self.sniffer_dictionary[ip_index]['collect_data_flag'] == True:
                    self.sniffer_dictionary[ip_index]['stream_data'] += ethernet_packet.get_buffer_as_string()

            
                #switch to enum?
                if transmission_protocol == 6 : #TCP protocol
                    self.sniffer_dictionary[ip_index]['tcp_count'] += 1
                    self.sniffer_dictionary[ip_index]['last_packet'] = "TCP"
                    
                elif transmission_protocol == 17 : #UDP packets
                    self.sniffer_dictionary[ip_index]['udp_count'] += 1
                    self.sniffer_dictionary[ip_index]['last_packet'] = "UDP"
        
                elif transmission_protocol == 1 : #ICMP Packets
                    self.sniffer_dictionary[ip_index]['icmp_count'] += 1
                    self.sniffer_dictionary[ip_index]['last_packet'] = "ICMP"
            
                else: #some other IP packet
                    self.sniffer_dictionary[ip_index]['last_packet'] = "OTHER"


            else: #packet outbound (sent) ################################################################################

                #print("packet from me!")
                #print(ethernet_packet.as_eth_addr(ethernet_packet.get_ether_shost()), "<--source mac")
                #print(ethernet_packet.as_eth_addr(ethernet_packet.get_ether_dhost()), "<--destination mac")
                ip_index = destination_IP_address
                geoip_info = self.city_database.record_by_addr(destination_IP_address)


                if destination_IP_address in self.sniffer_dictionary:   # Previous self.sniffer_dictionary entry found for outbound destination
        
                    self.sniffer_dictionary[ip_index]['packet_count'] += 1
                    self.sniffer_dictionary[ip_index]['new_packet_boolean'] = True
                    self.sniffer_dictionary[ip_index]['delta_time'] = timestamp
                    self.sniffer_dictionary[ip_index]['data_out'] += number_of_bytes_of_data
                    
                                                        
                else: #initalize new self.sniffer_dictionary entry for new outbound packet destination

                    self.sniffer_dictionary[ip_index] = {} 

                    self.sniffer_dictionary[ip_index]['packet_count'] = 1
                    self.sniffer_dictionary[ip_index]['tcp_count'] = 0
                    self.sniffer_dictionary[ip_index]['udp_count'] = 0
                    self.sniffer_dictionary[ip_index]['icmp_count'] = 0
                    self.sniffer_dictionary[ip_index]['data_in'] = 0 #data inbound
                    self.sniffer_dictionary[ip_index]['data_out'] = number_of_bytes_of_data #data outbound
                    self.sniffer_dictionary[ip_index]['new_packet_boolean'] = True
                    self.sniffer_dictionary[ip_index]['blank_boolean'] = False ##rename?
                    self.sniffer_dictionary[ip_index]['delta_time'] = timestamp
                    self.sniffer_dictionary[ip_index]['stream_data'] = ''
                    self.sniffer_dictionary[ip_index]['collect_data_flag'] = False
                    self.sniffer_dictionary[ip_index]['geoip_info'] = geoip_info
                
                    
                

                if self.sniffer_dictionary[ip_index]['collect_data_flag'] == True:
                        self.sniffer_dictionary[ip_index]['stream_data'] += ethernet_packet.get_buffer_as_string() 
                

                #TODO:what is this again? haha
                self.sniffer_dictionary[destination_IP_address]['blank_boolean'] = True


                if transmission_protocol == 6 : #TCP protocol
                    self.sniffer_dictionary[ip_index]['tcp_count'] += 1
                    self.sniffer_dictionary[ip_index]['last_packet'] = "TCP"
    
                
                elif transmission_protocol == 17 : #UDP packets
                    self.sniffer_dictionary[ip_index]['udp_count'] += 1
                    self.sniffer_dictionary[ip_index]['last_packet'] = "UDP"


                elif transmission_protocol == 1 : #ICMP Packets
                    self.sniffer_dictionary[ip_index]['icmp_count'] += 1
                    self.sniffer_dictionary[ip_index]['last_packet'] = "ICMP"
                    
                else :
                    print('Protocol other than TCP/UDP/ICMP') #some other IP packet
                    self.sniffer_dictionary[ip_index]['last_packet'] = "OTHER"


        else: #Not an IP packet
            pass

         


    
    def getInterface(self) -> int:
        """Grab a list of interfaces that pcapy is able to detect. Populate self.mac_dict with discovered hardware addresses"""

        bin_mac = get_mac() 
        self.mac = ':'.join(("%012x" % bin_mac)[i:i+2] for i in range(0, 12, 2))
        


        interfaces = netifaces.interfaces()

        for i in interfaces:
            try:
                interface_dict = netifaces.ifaddresses(i)[netifaces.AF_LINK]
                if interface_dict[0]['addr'] == '00:00:00:00:00:00': #don't bother with loopback
                    continue
                else:
                    self.mac_dict[interface_dict[0]['addr']] = interface_dict[0]['addr']
            except Exception as e:
            #<class 'KeyError'> sniffy.py 305
            
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)


        interfaces = findalldevs()

        # No interfaces detected
        if 0 == len(interfaces):
            print("You don't have enough permissions to open any interface on this system.")
            sys.exit(1)

        # Only one interface available
        elif 1 == len(interfaces):
            print('Only one interface present, defaulting to it.')
            return interfaces[0]

        # Ask the user to choose an interface from the list.
        for i, interface in enumerate(interfaces):
            #print('%i - %s' % (i, interface))
            pass

        #index = int(input('Please select an interface: '))

        print("My hardware address: ", self.mac)
        
        return 'en0' #interfaces[index] 
        #TODO hack eth0 for webserver, en0 for local





    def check_for_client_commands(self) -> None:
        """Using ZMQ Client/Server architecture, check for any commands from client"""

        try:
    
            msg = self.msg_from_client_socket.recv(flags=zmq.NOBLOCK)
          
            if msg == b'reset':
                self.sniffer_dictionary.clear()
                self.msg_from_client_socket.send(b"received reset")
                print("triggered reset")
                
            elif msg == 'on':
                self.sniffer_publish_to_client = True
                self.msg_from_client_socket.send("received on")
                
            elif msg == 'off':
                self.sniffer_publish_to_client = False
                self.msg_from_client_socket.send("received off")

            elif msg == b'ip_info':

                ip = get('https://api.ipify.org').content
                self.msg_from_client_socket.send(ip)

  
        except zmq.ZMQError as e:
            pass
 
 
            
        
                
    def publish_data_to_clients(self) -> None:
        """Using ZMQ PUB/SUB architecture, pickle and publish self.sniffer_dictionary to any listening clients"""

        #TODO:encrypt pickled data in here
        json_data = json.dumps(self.sniffer_dictionary)
      

        self.publish_socket.send_string(json_data)
        



    def close(self) -> None:
        """Shutdown pcapy sniffer"""

        print("Sniffer is shutting down!")
        self.keep_alive = False
        self.publish_socket.close()
        self.msg_from_client_socket.close()





if __name__ == "__main__":

    parser = argparse.ArgumentParser( description= "Specify port to transmit data. The specified port (client/server) and port + 1 (publish/subscribe) will be used.")
    parser.add_argument("--port",  type=int, help="An interger between 1024-49150 not in use")
    args = parser.parse_args()
    
    sniffer = Sniffer(port = args.port)
