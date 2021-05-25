#######################################################
#     Spiros Daskalakis                               #
#     last Revision: 17/05/2021                       #
#     Python Version:  3.9                            #
#     Email: Daskalakispiros@gmail.com                #
#######################################################


from NI845x import NI8452Interface

def main():
    """
    Entry point to the script
    :return: None
    """
    ni8452 = NI8452Interface()
    resource_name = ni8452.ni845xFindDevice()
    ni8452.ni845xOpen(resource_name)
    ni8452.ni845xSetIoVoltageLevel(12)
    ni8452.ni845xSetTimeout(20000)
    ni8452.ni845xSpiConfigurationOpen()
    ni8452.ni845xSpiConfigurationSetChipSelect(0)
    #print("ni845xSpiConfigurationGetChipSelect: ",ni8452.ni845xSpiConfigurationGetChipSelect())
    ni8452.ni845xSpiConfigurationSetClockPhase(0)
    #print("ni845xSpiConfigurationGetClockPhase: ", ni8452.ni845xSpiConfigurationGetClockPhase())
    ni8452.ni845xSpiConfigurationSetClockPolarity(0)
    # print("ni845xSpiConfigurationGetClockPolarity", ni8452.ni845xSpiConfigurationGetClockPolarity())
    # in Khz
    ni8452.ni845xSpiConfigurationSetClockRate(1000)
    # print("ni845xSpiConfigurationGetClockRate: ",ni8452.ni845xSpiConfigurationGetClockRate())
    ni8452.ni845xSpiConfigurationSetNumBitsPerSample(16)
    # print("ni845xSpiConfigurationGetNumBitsPerSample: ", ni8452.ni845xSpiConfigurationGetNumBitsPerSample())
    #ni8452.ni845xSpiConfigurationSetPort(0)
    # print("ni845xSpiConfigurationGetPort: ", ni8452.ni845xSpiConfigurationGetPort())

    # Configure Line 1
    PortNumber=0
    LineNumber=0
    ConfigurationValue=1 # 1 for output 0 for input
    #ni8452.ni845xSpiScriptDioConfigureLine(PortNumber, LineNumber, ConfigurationValue)

    PortNumber=0
    WriteData = 0 # 0 to 31

    fRet = 0
    print("Writing in TX_EN")
    WriteData = 0b0000_0001
    fRet = ni8452.ioWriteDIO(WriteData)  # Set DIO RX_EN pin
    print('Read TX_EN Pin: ',ni8452.ioReadDIO())

    print("Writing in RX_EN")
    WriteData = 0b0000_0010
    fRet = ni8452.ioWriteDIO(WriteData)  # Set DIO RX_EN pin
    print('Read RX_EN Pin: ', ni8452.ioReadDIO())



    #ni8452.ni845xDioWritePort(PortNumber, WriteData)

    #ni8452.ni845xSpiScriptDioWriteLine(PortNumber, LineNumber, ConfigurationValue)


    WriteAdress = [0x20, 0x00]
    BytesToWrite = 2
    BytesToRead = 2
    while True:
        ReadSize, ReadData = ni8452.ni845xSpiWriteRead(WriteAdress, BytesToWrite, BytesToRead)
        '''
        Data acquisition and calculation for adc128s102evm board:
        '''
        '''
        ReadByte0 = ReadData[0]
        ReadByte0 = ReadByte0 << 8
        ReadByte1 = ReadData[1]
        steps = int(ReadByte0) | int(ReadByte1)
        VoltageValue = (0.0004028320315+((steps-1)*0.0008056640625))
        print("VoltageValue: ",VoltageValue)
        time.sleep(0.001)
        '''

    ni8452.ni845xSpiConfigurationClose()
    ni8452.ni845xClose()


if __name__ == '__main__':
    main()