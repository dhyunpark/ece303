# Written by S. Mevawala, modified by D. Gitzel

import logging
import string
import channelsimulator
import utils
import sys
import socket
import zlib

class Receiver(object):

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=0.01, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout)

    def receive(self):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class BogoReceiver(Receiver):

    def __init__(self):
        super(BogoReceiver, self).__init__(timeout=3)

    def checksum(data):
        sum1 = 0
        sum2 = 0
        i = 0
        while i < len(data):
            sum1 = (sum1 + ord(data[i]))%65535
            sum2 = (sum2 + sum1)%65535
            i+=1
        x = sum1*65536 + sum2
        checksum = bytearray.fromhex('{:08x}'.format(x))
        pad = bytearray(32-len(checksum))
        return pad + checksum

    def int2bi(self, number):
        #converts number to a 4 byte bytearray
        bytArr = bytearray([(number & 0xFF000000) >> 24, (number & 0xFF0000) >> 16, (number & 0xFF00) >> 8, (number & 0xFF)])
        return bytArr

    def bi2int(self, bytArr):
        #converts a 4 byte bytearray to an integer
        number = int(''.join([string.zfill(s,8) for s in map(lambda n : n[2:], map(bin, bytArr))]), 2)
        return number

    def checksum(self, data):
        sum1 = 0
        sum2 = 0
        i = 0
        data = str(data)
        while i < len(data):
            sum1 = (sum1 + ord(data[i]))%65535
            sum2 = (sum2 + sum1)%65535
            i+=1
        x = sum1*65536 + sum2
        checksum = bytearray.fromhex('{:08x}'.format(x))
        pad = bytearray(32-len(checksum))
        return pad + checksum

    def receive(self):
        PACKET_SIZE = 1016 # +4 sequence bytes +4 Checksum

        end = False
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        rList = {}

        while True:
            try:
                packet = self.simulator.u_receive()  # receive data
                print len(packet)
                '''
                if len(packet) < 1024:
                    end = True  #denote the end of transmission
                    print "end set to true"
                '''
                #extract seqNum checksum and calculate data's checksum
                seqNum = self.bi2int(packet[:3])
                chkSum = self.bi2int(packet[-4:])
                dataSum = self.checksum(packet[4:-5])

                #if the data checksum is equal to calculated checksum. if corrupted, pass
                if dataSum == chkSum:
                    print "not corrupted"
                    #create a checksum for the sequence number of the ACK corresponding to the received packet being sent back
                    ackNum = self.int2bi(seqNum)
                    ack = seqNum + self.checksum(ackNum)

                    if (seqNum % 300) == 149 and len(rList) == 300:
                        print "deleting 151 to 300"
                        for i in xrange(150, 299):
                            del rList[i]

                    #if the packet has been received and acked already, then pass on the packet and retransmit ack
                    if (seqNum%300) in rList:
                        if rList[seqNum%300]['acked']:
                            self.simulator.u_send(ack)

                    else: #if new packet, create an entry, and send ack
                        rList[seqNum%300] = {
                            'packet': packet,
                            'acked': False,
                        }
                        #send ACK packet
                        self.simulator.u_send(ack)
                        rList[seqNum%300]['acked'] = True

                    #if the entries fill up the dictionary then flush to output and delete first half of dictionary
                    if len(rList) == 300:
                        for entry in rList:
                            sys.stdout.write(rList[entry]['packet'][4:-5])
                        for i in xrange(0, 149):
                            del rList[i]
                else:
                    pass

            except socket.timeout:
                if end:
                    break
                else:
                    pass
        sys.exit()

if __name__ == "__main__":
    # test out BogoReceiver
    rcvr = BogoReceiver()
    rcvr.receive()
