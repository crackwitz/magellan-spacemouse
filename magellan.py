from __future__ import division
import time
import serial
import visual
from ctypes import *

def iround(x):
	return int(round(x))

def bitcount(n):
	c = 0
	while n:
		c += n&1
		n >>= 1
	return c

def enc(*values):
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
		
		self.ser.write(enc('p', dmax, dmin))
	
	def set_mode(self, dom=None, translation=None, rotation=None):
		mouse = 0 # 3D mode, not mouse mode
		
		# TODO: get_mode, handle None args
		
		self.ser.write(enc('m', bits(mouse, dom, translation, rotation))
	
	def get_mode(self):
		ser.write(enc("mQ"))
	
	def set_compression(self, compress=True):
		self.compressed = compress
		
		if compress:
			self.ser.write(enc('c', 0b0011, 0b0101))
		else:
			self.ser.write(enc('c', 0b0011, 0b0100))
	
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
	ser = serial.Serial(port=0, stopbits=serial.STOPBITS_TWO, rtscts=True, timeout=1.0)

	while ser.inWaiting() > 0:
		print "garbage:", repr(ser.read(1))
		
	# speed: 40ms
	ser.write(enc('p', 1, 1))

	compressed = True
	if compressed:
		ser.write(enc('c', 0b0011, 0b0101))
	else:
		ser.write(enc('c', 0b0011, 0b0100))

	buffer = ""
	lastcommand = timer()
	while True:
		n = ser.inWaiting()
		chunk = ser.read(max(1, n))
		if len(chunk) == 0:
			continue
		
		buffer += chunk
		
		while '\r' in buffer:
			pos = buffer.find('\r')
			assert(buffer[pos] == '\r')
			packet = buffer[:pos]
			buffer = buffer[pos+1:]

			ptype = packet[0]
			data = packet[1:]
			print "->", ptype, ":", hexdump(data), "."
			
			if compressed and ptype == 'd':
				nibbles = [ord(c) & 0x3f for c in data]
				assert sum(ord(b) for b in data[:-2]) == nibbles[-2]*64+nibbles[-1]
			else:
				nibbles = [ord(c) & 0xf for c in data]
			
			print "->", ptype, ":", ' '.join("%2d" % n for n in nibbles), "."
			
				
				
			t = timer()
			print "after %4.1f ms" % ((t-lastcommand)*1000)
			lastcommand = t
			

