import adi
import numpy as np
import time
import math
from datetime import datetime
from commpy.filters import rcosfilter

def calculateBCH(data):

    if(len(data) == 26):
        g = np.array([1,0,1,0,1,0,0,1,1,1,0,0,1])
        data = np.append(data,np.repeat(0,12))
    elif(len(data) == 61):
        g = np.array([1,0,0,1,1,0,1,1,0,1,1,0,0,1,1,1,1,0,0,0,1,1])
        data = np.append(data,np.repeat(0,21))
    else:
        raise ValueError("Data must be either 26 bits or 61 bits long, but data is " + str(len(data)) + " bits long")

    while np.where(data==1)[0][0] + len(g) <= len(data):
        index = np.where(data==1)[0][0]
        data[index:index+len(g)] = data[index:index+len(g)]^g

    if(len(data) == 38):
        bchCode = data[-12:]
    elif(len(data) == 82):
        bchCode = data[-21:]

    return bchCode

sign = lambda x: math.copysign(1, x)

def dec2bin(n,minBits = 0):
    n = int(n)
    stringBinary = bin(n)[2:]
    binaryValue = []

    for i in range(0,len(stringBinary)):
        binaryValue.append(int(stringBinary[i]))

    if(minBits != 0):
        binaryValue = np.append(np.repeat(0,minBits - len(binaryValue)),binaryValue)
                           
    return binaryValue

def createPacket(gps):
    #HEX ID: 2E1C010002FFBFF
    bitSynch = np.array([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1])
    frameSynch = np.array([0,0,0,1,0,1,1,1,1])
    formatFlag = np.array([1])
    protocolFlag = np.array([0])
    countryCode = np.array([0,1,0,1,1,1,0,0,0,0])
    protocolCode = np.array([1,1,1,0])
    encodedPositionSource = np.array([1])
    testProtocol = np.array([0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1])
    packet = np.concatenate([bitSynch,frameSynch,formatFlag,protocolFlag,countryCode,protocolCode,testProtocol])

    if(gps.latitude > 0):
        packet = np.concatenate([packet, np.array([0])])
    else:
        packet = np.concatenate([packet, np.array([1])])

    packet = np.concatenate([packet, dec2bin(round(abs(gps.latitude)/0.25),9)])
    
    if(gps.longitude > 0):
        packet = np.concatenate([packet, np.array([0])])
    else:
        packet = np.concatenate([packet, np.array([1])])

    packet = np.concatenate([packet, dec2bin(round(abs(gps.longitude)/0.25),10)])

    #Add first error detection block
    packet = np.concatenate([packet,calculateBCH(packet[24:85]), np.array([1,1,0,1]), encodedPositionSource, np.array([0])])
    
    #Calculate positional offsets
    latitudeOffset = abs(gps.latitude) - round(abs(gps.latitude)/0.25)*0.25
    packet = np.concatenate([packet, np.array([int(max(sign(latitudeOffset),0))]) ])
    latitudeOffset = abs(latitudeOffset)
    packet = np.concatenate([packet, dec2bin(math.floor(60*latitudeOffset),5), dec2bin(round(60*((60*latitudeOffset)%1)/4),4)])

    longitudeOffset = abs(gps.longitude) - round(abs(gps.longitude)/0.25)*0.25
    packet = np.concatenate([packet, np.array([int(max(sign(longitudeOffset),0))]) ])
    longitudeOffset = abs(longitudeOffset)
    packet = np.concatenate([packet, dec2bin(math.floor(60*longitudeOffset),5), dec2bin(round(60*((60*longitudeOffset)%1))/4,4)])

    #Add second error detection block
    packet = np.concatenate([packet, calculateBCH(packet[106:132])])

    return packet

def transmitPacket(sdr,packet,dataRate,samplesPerBit):
    oneBit = np.repeat(np.array([1.1,-1.1]),samplesPerBit/2)
    zeroBit = np.repeat(np.array([-1.1,1.1]),samplesPerBit/2)
    outputSignal = np.array([])

    for i in range(0,len(packet)):
        if(packet[i] == 1):
            outputSignal = np.concatenate([outputSignal,oneBit])
        else:
            outputSignal = np.concatenate([outputSignal,zeroBit])

    filt = rcosfilter(132,0.8,dataRate,dataRate*samplesPerBit)[1]
    x = np.array([])
    x = np.concatenate([x, np.repeat(1, int(0.160*(samplesPerBit*dataRate)))])
    x = np.concatenate([x,np.convolve(filt,np.exp(1j*outputSignal))])
    x *= 2**14
    sdr.tx(x)

class gps:
    def __init__(self):
        gps.latitude =  0
        gps.longitude = 0


if __name__ == "__main__":

    dataRate = 400
    samplesPerBit = 170*10
    sampRate = dataRate*samplesPerBit

    sdr = adi.Pluto(uri='ip:192.168.2.1') # or whatever your Pluto's IP is
    sdr.sample_rate = int(sampRate)
    sdr.tx_hardwaregain_chan0 = 0
    sdr.tx_lo = 406025000
    sdr.tx_rf_bandwidth = 200000

    #Enter your favorite GPS coordinates here
    gpsCoords = gps()
    gpsCoords.latitude = 38.624593
    gpsCoords.longitude = -90.185037

    lastTransmitTime = 0

    while True:

        #Transmit the beacon packet every 60 seconds
        if(time.time() - lastTransmitTime >= 60):
            lastTransmitTime = time.time()
            
            packet = createPacket(gpsCoords)
            transmitPacket(sdr,packet,dataRate,samplesPerBit)

