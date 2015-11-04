from __future__ import division
import time
import serial
from ctypes import *

# see also:
# http://spacemice.org/pdf/Magellan_Programmers_Manual_2000.pdf
# http://paulbourke.net/dataformats/spacemouse/

def iround(x):
	return int(round(x))

def blocks(n, seq):
	block = []
	for x in seq:
		block.append(x)
		if len(block) >= n:
			yield block
			block = []
	if len(block) > 0:
		yield block

def bitcount(n):
	c = 0
	while n:
		c += n&1
		n >>= 1
	return c

def decode_nibbles(nibbles, width):
	N = len(nibbles)
	value = sum(n << (width * i) for i,n in enumerate(reversed(nibbles)))
	offset = 2 ** (width * N - 1)
	return value - offset

def magellan_encode(*values):
	values = list(values)
	res = []
	while values:
		v = values.pop(0)
		
		if isinstance(v, str):
			res.append(v)
		
		elif isinstance(v, int):
			assert 0 <= v <= 15
			v |= (3 + (bitcount(v)&1)) << 4
			res.append(chr(v))
			
		else:
			assert(False)
	
	return ''.join(res) + "\r"

def bits2int(*bits):
	res = 0
	for b in bits:
		res = (res << 1) | int(bool(b))
	return res

def splitfirst(sep, subj):
	if sep not in subj:
		return (None, subj)
		#raise ValueError("separator not found in string, nothing to split")

	pos = subj.find(sep)
	#assert(subj[pos:].startswith(sep))
	piece = subj[:pos]
	remainder = subj[pos+len(sep):]

	return (piece, remainder)


class Magellan(object):
	def __init__(self, comport):
		self.ser = serial.Serial(port=comport, stopbits=serial.STOPBITS_TWO, rtscts=True, timeout=1.0)
		self.compressed = False
		self.ondata = set()
		self.onmode = set()
		self.onkey = set()
		self.buffer = ''

	def set_rate(self, tmax=40, tmin=40):
		assert 20 <= tmax <= 320
		assert 20 <= tmin <= 320
		
		dmax = iround(tmax/20 - 1)
		dmin = iround(tmin/20 - 1)
		
		assert 0 <= dmax <= 15
		assert 0 <= dmin <= 15
		
		self.ser.write(magellan_encode('p', dmax, dmin))
	
	def set_mode(self, dom=None, translation=None, rotation=None):
		mouse = 0 # 3D mode, not mouse mode
		
		# TODO: get_mode, handle None args
		
		self.ser.write(magellan_encode('m', bits(mouse, dom, translation, rotation)))
	
	def get_mode(self):
		ser.write(magellan_encode("mQ"))
	
	def set_compression(self, compress=True):
		self.compressed = compress
		
		if compress:
			self.ser.write(magellan_encode('c', 0b0011, 0b0101))
		else:
			self.ser.write(magellan_encode('c', 0b0011, 0b0100))
	
	def dispatch(self):
		while True:
			n = ser.inWaiting()
			chunk = ser.read(max(1, n))
			if len(chunk) == 0:
				break

			self.buffer += chunk
			
			while '\r' in self.buffer:
				pos = self.buffer.find('\r')
				
				packet = self.buffer[:pos]
				self.buffer = self.buffer[pos+1:]
				
				self.dispatch_packet(packet)
			
			if not self.buffer:
				break
			
	def dispatch_packet(self, packet):
		ptype = packet[0]
		data = packet[1:]
		
		if ptype == 'd':
			pass
		
		elif ptype == 'm':
			pass
		
		elif ptype == 'k':
			pass
		
		else:
			assert False
	

hrfreq = c_uint64(0)
windll.kernel32.QueryPerformanceFrequency(byref(hrfreq))
hrfreq = hrfreq.value

def hrtimer():
	counter = c_uint64(0)
	windll.kernel32.QueryPerformanceCounter(byref(counter))
	
	return float(counter.value) / float(hrfreq)

timer = hrtimer

def hexdump(s):
	return ' '.join(c.encode('hex').upper() for c in s)

if 1:
	ser = serial.Serial(port="COM7", stopbits=serial.STOPBITS_TWO, rtscts=True, timeout=1.0)

	while ser.inWaiting() > 0:
		print "garbage:", repr(ser.read(1))
		
	# speed: 40ms
	ser.write(magellan_encode('p', 1, 1))

	compressed = True
	if compressed:
		ser.write(magellan_encode('c', 0b0011, 0b0101))
	else:
		ser.write(magellan_encode('c', 0b0011, 0b0100))

	buffer = ""
	lastcommand = timer()
	while True:
		n = ser.inWaiting()
		chunk = ser.read(max(1, n))
		if len(chunk) == 0:
			continue
		
		buffer += chunk
		
		while True:
			(packet, buffer) = splitfirst("\r", buffer)
			if packet is None: break

			ptype = packet[0]
			data = packet[1:]
			#print "->", ptype, ":", hexdump(data), "."
			
			nibblevalue = 0

			if compressed and ptype == 'd':
				nibblevalue = 6
				nibbles = [ord(c) & 0x3f for c in data]
				assert sum(ord(b) for b in data[:-2]) == (nibbles[-2] << nibblevalue) + nibbles[-1], "checksum failed"
				nibbles = nibbles[:-2]
			else:
				nibblevalue = 4
				nibbles = [ord(c) & 0xf for c in data]
			
			if ptype == 'd':
				values = [decode_nibbles(val, width=nibblevalue) for val in blocks(2, nibbles)]
				print "->", "T {0:4d} {1:4d} {2:4d} : R {3:4d} {4:4d} {5:4d}".format(*values)
			else:
				print "->", ptype, ":", ' '.join("%2d" % n for n in nibbles), "."

			
				
			t = timer()
			#print "after %4.1f ms" % ((t-lastcommand)*1000)
			lastcommand = t
			

