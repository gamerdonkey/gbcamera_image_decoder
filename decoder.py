
import argparse
import json
import serial

from datetime import datetime
from PIL import Image

class GBCameraDecoder:
   TILE_WIDTH = 8
   TILE_HEIGHT = 8
   TILES_PER_LINE = 20

   def __init__(self, display_only=False, scale=1, log=False):
      self.__tiles = []
      self.__lines_since_init = []
      self.__timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
      self.__output_counter = 0

      self.display_only = display_only
      self.log = log
      self.scale = scale

      self.palette = []
      for i in reversed(range(4)):
         self.palette.append(Image.new('L', (scale, scale), color=i*85))

   def render_tiles_to_image(self, tiles):
      x_size = self.TILES_PER_LINE * self.TILE_WIDTH
      y_size = int(len(tiles) / 20) * self.TILE_HEIGHT
      image = Image.new('L', (x_size * self.scale, y_size * self.scale))

      tile_count = 0
      for tile in tiles:
         for i in range(self.TILE_HEIGHT):
            for j in range(self.TILE_WIDTH):
               x = j + (tile_count % self.TILES_PER_LINE) * self.TILE_WIDTH
               y = i + int(tile_count / self.TILES_PER_LINE) * self.TILE_HEIGHT
               image.paste(self.palette[tile[i][j]], (x * self.scale, y * self.scale))
         tile_count += 1
      return image

   def decode_tile(self, hexstring):
      byte_array = []

      for i in range(0, len(hexstring), 2):
         byte_array.append(int(hexstring[i:i+2], 16))

      tile = []
      for i in range(self.TILE_HEIGHT):
         tile.append([])
         for j in reversed(range(self.TILE_WIDTH)):
            lo_bit = (byte_array[i*2] >> j) & 1
            hi_bit = (byte_array[i*2 + 1] >> j) & 1
            tile[i].append((hi_bit << 1) | lo_bit)

      return tile

   def parse_line(self, line):
      self.__lines_since_init.append(line)

      if(len(line) == 0 or line[0] == '#'):
         return

      if(line[0] == '!'):
         data = json.loads(line[1:])

         if('command' in data):
            if(data['command'] == 'INIT'):
               self.__tiles = []
               self.__lines_since_init = [line]
            if(data['command'] == 'PRNT'):
               image = self.render_tiles_to_image(self.__tiles)
               if(self.display_only):
                  image.show()
               else:
                  filename = '{}-{:04d}'.format(self.__timestamp, self.__output_counter)
                  image.save(filename + '.png')
                  if(self.log):
                     with open(filename + '.txt', 'w') as output_file:
                        output_file.write('\n'.join(self.__lines_since_init))
                  self.__output_counter += 1

      else:
         hexstring = line.replace(' ', '')

         if(len(hexstring) != 32):
            print('Data line not 16 bytes: ', line)
            return


         self.__tiles.append(self.decode_tile(hexstring))
 


# --scale 1 --display-only --read-file <file> --read-serial <device> --log-input
parser = argparse.ArgumentParser(description="Reads data from the Arduino Gameboy Printer Emulator and decodes it into image files.")

parser.add_argument('-d', '--display-only', action='store_true', default=False, help='Only display images, do not save')
parser.add_argument('-l', '--log-input', action='store_true', default=False, help='Creates a text file with serial data for each image processed')
parser.add_argument('-x', '--scale', type=int, default=1, help='Scale images by multiplier. 1-3 work best.')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-s', '--read-serial', dest='serial_device', help='Read from serial device')
group.add_argument('-f', '--input-file', help='Read from file')

args = parser.parse_args()

gbcamera_decoder = GBCameraDecoder(display_only=args.display_only, scale=args.scale, log=args.log_input)

if(args.input_file):
   with open(args.input_file) as input_file:
      for line in input_file:
         gbcamera_decoder.parse_line(line.strip())
elif(args.serial_device):
   with serial.Serial(args.serial_device, 115200, timeout=30) as ser:
      print('Opened serial device...')
      line = ser.readline()
      while(line):
         gbcamera_decoder.parse_line(line.decode().strip())
         line = ser.readline()
      print('Timeout reached.')
