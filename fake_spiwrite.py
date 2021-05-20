#-------------------------------------------------------------------------------
# Name:        fake_spiwrite
# Purpose:     Write commands to the awmf-0108 through the SPI interposer
#                 Writes nonsense data to hide Anokiwave's SPI interface
#
# Author:      Andy MacGregor
#              Grayson Colwell
#              
#
# Created:     12/12/2017
# Licence:     <tbd Anokiwave>
#-------------------------------------------------------------------------------

from ni8452io import SPI
#dll name is Ni845x.dll

#enumerate TXMODE, RXMODE, RX_11, SB
SB_MODE = 0
TX_MODE = 1
RX_MODE = 2
RX_11_MODE = 3

class SpiInitException(Exception):
  """Error from initializing SPI bus"""
  def __init__(self, fret, msg=""):
    self.fret = fret
    self.msg = msg 

class AwmfCommander:
  """
  Sends commands to the awmf through the SPI interposer 
  usage:

  AwmfCommander.initSpi()
  AwmfCommander.setBeam(....)
  """

  #SPi interface handle placeholder
  testSPI = 0 

  @classmethod
  def initSpi(cls):
    """ 
    opens the connection to the SPI bus and sets the clock
    """
    #open spi
    print("Searching for SPI Interface")

    cls.testSPI = SPI()
    fRet = cls.testSPI.ioOpen()
    #print('ioOpen():  \t{0}'.format(fRet))
    if fRet != 0:
      cls.testSPI.ioClose()
      raise SpiInitException(fRet, "ioOpen()")
    #set clock rate
    fRet = cls.testSPI.ioSetConfig(spiClk=1000)
    #print('ioSetConfig():\t{0}'.format(fRet))
    if fRet != 0:
      cls.testSPI.ioClose()
      raise SpiInitException(fRet, "ioSetConfig()")

    fRet = cls.testSPI.ioInit()
    #print('ioInit():  \t{0}'.format(fRet))
    if fRet != 0:
      cls.testSPI.ioClose()
      raise SpiInitException(fRet, "ioInit()")

    print("SPI initialized successfully")

  @classmethod
  def closeSPI(cls):
    """
    Close the SPI port and reset all ports to 0V
    """
    r = cls.testSPI.ioSafe()
    r1 = cls.testSPI.ioClose()
    if(r == 0 and r1 == 0):
      print("SPI closed successfully")
    else: 
      raise SpiInitException(r1, "ioClose()")
    
  @classmethod
  def setBeam(cls, mode, NE_phase, SE_phase, SW_phase, NW_phase,
                    NE_amp, SE_amp, SW_amp, NW_amp):
    """
    Writes fake signals on to the the spi bus.
      Doesn't actually use Anokiwave's SPI interface because I signed an NDA
    """
      
    #determine message and pack it 
    unpackedData = []
    fRet = 0
    if(mode == RX_MODE):
      print("Writing in RX_MODE")
      fRet = cls.testSPI.ioWriteDIO(2) #Set DIO RX_EN pin
      unpackedData = [NE_phase, NE_amp,
                   0x3D9, 0x3D9,
                   SE_phase, SE_amp,
                   0x3D9, 0x3D9,
                   SW_phase, SW_amp,
                   0x379, 0x379,
                   NW_phase, NW_amp,
                   0x379, 0x379]
    elif(mode == TX_MODE):
      print("Writing in TX_MODE")
      fRet = cls.testSPI.ioWriteDIO(1)
      unpackedData = [0x3DF, 0x3DF,
                   NE_phase, NE_amp,
                   0x3DF, 0x3DF,
                   SE_phase, SE_amp,
                   0x37F, 0x37F,
                   SW_phase, SW_amp,
                   0x37F, 0x37F,
                   NW_phase, NW_amp]
    elif(mode == SB_MODE):
      print("SB mode")
      fRet = cls.testSPI.ioWriteDIO(0)
      return []#Nothing programmed
    else:
      fRet = cls.testSPI.ioWriteDIO(3)
      print("RX_11 mode is not implemented ") 
      return []

    if fRet != 0:
      try:
        cls.closeSPI()
      except: 
        pass 
      raise SpiInitException(fRet, "ioWriteDIO()")

    wArr = cls.__packValues(unpackedData)
    # ioWriteSPI hits LDB pin automatically
    rData, fRet = cls.testSPI.ioWriteSPI2(wArr, 10) #send bits 8

    if fRet != 0:
      try:
        cls.closeSPI()
      except:
        pass
      raise SpiInitException(fRet, "ioWriteSPI2")

    return rData #return data from device
    

  @staticmethod
  def __packValues(vals, in_width = 12, packed_size = 8, big_endian=True):
    """
    takes a list of values (integers) and packs them as densely
    as possible into a  array of bits where each element is
    packed_size bits long

    assumes each element in vals is *in_width* bits wide
    """
    byteArray = []
    cB = 0
    cBi = 0

    for val in vals:
      #for each meaningful bit in the current value
      for i in range(in_width):
        #set the next bit in the current working byte
            #whether or not the next bit in val is set
            #      |                   index of cB to set
        cB |= ( (val & (1 << i)) >>  i) << cBi
        cBi += 1

        if(cBi >= packed_size):
          byteArray.append(cB)
          cBi = 0
          cB = 0

    #append the remaining bits if there are any
    if(cBi != 0):
      byteArray.append(cB)

    if big_endian:
      byteArray.reverse()

    return byteArray



# ------------------------------------------------------------------------------
# Tests 
# ------------------------------------------------------------------------------
def main():

  pvTest = False
  dioTest = True
  spiTest = False
  NE_phase=2
  NE_amp=10

  unpackedData = [0x3002, 0x23,
                  NE_phase, NE_amp]
  for i in unpackedData:
    print(bin(i))
  wArr = AwmfCommander._AwmfCommander__packValues(unpackedData, packed_size = 10)
  print()
  for i in wArr:
      print(bin(i))
  ######__pack_values
  if pvTest:
    pv = AwmfCommander._AwmfCommander__packValues
    c1 = pv(range(20))
    print(c1)
    pass #break here and inspect manually


  ##### Verify dio pins 
  if dioTest:
    print("**Interactive setBeam test. Get out an o'scope")
    AwmfCommander.initSpi()

    # print("Verify that everything is low")
    # _ = raw_input("Press Enter to continue: \n")


    # r = AwmfCommander.setBeam(RX_11_MODE, 16, 16, 1, 1, 8, 8, 8, 8)
    # print(r)
    # print("Verify that RX_EN and TX_EN are high")
    # _ = raw_input("Press Enter to continue: \n")
    
    r = AwmfCommander.setBeam(RX_MODE, 16, 16, 1, 1, 8, 8, 8, 8)
    print(r)
    print("Verify that RX_EN is high")
    #raw_input("Press Enter to continue: \n")

    # r = AwmfCommander.setBeam(TX_MODE, 16, 16, 1, 1, 8, 8, 8, 8)
    # print(r)
    # print("Verify that TX_EN is high")
    # _ = raw_input("Press Enter to continue: \n")
    #
    # r = AwmfCommander.setBeam(SB_MODE, 16, 16, 1, 1, 8, 8, 8, 8)
    # print(r)
    # assert(r == [])
    # print("Verify that TX_EN and RX_EN are low")
    # _ = raw_input("Press Enter to continue: \n")
    
    AwmfCommander.closeSPI()    
    
  if spiTest:
    AwmfCommander.initSpi()
    
    print("** Look at what the spi bus says when its talking")
    for x in range(10):
      for d in range(32):
        r = AwmfCommander.setBeam(RX_MODE, 5, 6, 7, 8, 9, 10, 11, 12)
        
    AwmfCommander.closeSPI()

if __name__ == '__main__':
    main()





