
import argparse
import json

from PIL import Image

class GBCameraDecoder:
   TILE_WIDTH = 8
   TILE_HEIGHT = 8
   TILES_PER_LINE = 20

   def __init__(self):
      self.__tiles = []

   def render_tiles_to_image(self, tiles):
      x_size = self.TILES_PER_LINE * self.TILE_WIDTH
      y_size = int(len(tiles) / 20) * self.TILE_HEIGHT
      image = Image.new('L', (x_size, y_size))

      tile_count = 0
      for tile in tiles:
         for i in range(self.TILE_HEIGHT):
            for j in range(self.TILE_WIDTH):
               x = j + (tile_count % self.TILES_PER_LINE) * self.TILE_WIDTH
               y = i + int(tile_count / self.TILES_PER_LINE) * self.TILE_HEIGHT
               image.putpixel((x, y), (3-tile[i][j]) * 85)
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
      if(len(line) == 0 or line[0] == '#'):
         return

      if(line[0] == '!'):
         data = json.loads(line[1:])

         if('command' in data):
            if(data['command'] == 'INIT'):
               self.__tiles = []
            if(data['command'] == 'PRNT'):
               self.render_tiles_to_image(self.__tiles).show()

      else:
         hexstring = line.replace(' ', '')

         if(len(hexstring) != 32):
            print('Data line not 16 bytes: ', line)
            return


         self.__tiles.append(self.decode_tile(hexstring))
 


# --scale 1 --display-only --read-file <file> --read-serial <device> --log-input
parser = argparse.ArgumentParser(description="Reads data from the Arduino Gameboy Printer Emulator and decodes it into image files.")
parser.add_argument('-d', '--display-only', action='store_true', default=False, help='Only display images, do not save')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-s', '--read-serial', dest='serial_device', help='Read from serial device')
group.add_argument('-f', '--input-file', help='Read from file')
args = parser.parse_args()
print(args)
with open(args.input_file) as input_file:
   gbcamera_decoder = GBCameraDecoder()
   for line in input_file:
      gbcamera_decoder.parse_line(line.strip())
