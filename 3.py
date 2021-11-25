import concurrent.futures
import time
import socket
import threading
import sys

class Chunks:
	def __init__(self):
		self.i = 0
		self._lock = threading.Lock()

	def update(self):
		with self._lock:
			self.i += 1
			if self.i >= 650:
				return -1
			else:
				return self.i-1

class Data:
	def __init__(self):
		self.data = [""] * ((total_size-1)//chunk_size + 1)
		self._lock = threading.Lock()

	def set(self, i, to_append):
		with self._lock:
			self.data[i] = to_append

	def read(self):
		return self.data

def download(index, chunks, data, HOST):
	print(f'TCP{index} started.')
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))
	chunks_downloaded = 0
	total_fetched = 0
	total_time = 0
	log = []

	chunk_num = chunks.update()
	while chunk_num != -1:
		while True:
			try:
				if chunks_downloaded % 100 == 0:
					s.close()
					s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					s.connect((HOST, PORT))

				start_time = time.time()

				request = f'GET /big.txt HTTP/1.1\r\nHost: {HOST}\r\nConnection: keep-alive\r\nRange: bytes={chunk_num*chunk_size}-{(chunk_num+1)*chunk_size - 1}\r\n\r\n'
				request = request.encode()
				s.send(request)
				fetched = 0
				response = ""
				to_receive = chunk_size if (chunk_num < (total_size-1)//chunk_size) else (total_size%chunk_size)
				while fetched < to_receive:
					packet = s.recv(4096).decode("utf-8")
					parsed = packet.split('\r\n\r\n')
					if len(parsed) == 2:
						packet = parsed[1]
					fetched += len(packet)
					response += packet

				total_fetched += fetched
				total_time += time.time() - start_time
				log.append((total_time, total_fetched))
				
				data.set(chunk_num, response)
				chunks_downloaded += 1
				chunk_num = chunks.update()
				break

			except:
				print('Offline.')
				t = 1
				while True:
					try:
						s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						host_ip = socket.gethostbyname(HOST)
						print('Trying', t)
						s.connect((host_ip, PORT))
						print('Back Online.')
						break
					except:
						t += 1
						pass

	print(f'TCP{index} downloaded {chunks_downloaded} chunks from {HOST}')
	logs[index-1] = log


file = open(sys.argv[1], 'r')
input = []
num_threads = 0
parsed = file.read().split('\n')
for line in parsed:
	if line=='':
		continue
	host, num = line.split(', ')
	num = int(num)
	input.append((host, num))
	num_threads += num

global PORT, total_size, chunk_size, logs
HOST = 'vayu.iitd.ac.in'
PORT = 80
total_size = 6488666
chunk_size = 10000

logs = [[]] * num_threads
chunks = Chunks()
data = Data()

with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
	thread = 1
	for pair in input:
		for i in range(pair[1]):
			executor.submit(download, thread, chunks, data, pair[0])
			thread += 1

content = ""
for pkt in data.read():
	content += pkt

import hashlib
md5 = hashlib.md5(content.encode())
print('md5 check: ', '70a4b9f4707d258f559f91615297a3ec' == md5.hexdigest())

file = open('big.txt', 'w')
print(content, end='', file=file)
file.close()

import matplotlib.pyplot as plt
import random
i = 0
for url in input:
	color = (random.random(), random.random(), random.random())
	for rep in range(url[1]):
		plt.plot([x[0] for x in logs[i]], [x[1] for x in logs[i]], c=color, label=url[0])
		i += 1

plt.xlabel('Time', fontsize=15)
plt.ylabel('Bytes', fontsize=15)
plt.title('Parallel TCP connections', fontsize=20)
plt.legend()
plt.show()