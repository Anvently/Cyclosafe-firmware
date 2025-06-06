import rclpy
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import Range
from rcl_interfaces.msg import ParameterDescriptor
from datetime import datetime
from rclpy.time import Time
import time, logging
from rclpy.node import Node
from serial import Serial, serialutil

FOV = 0.00523599
MS_TO_NS = (1000 * 1000)
TOF_FRAME_HEADER = 0x57  #Define frame header 定义帧头
TOF_FUNCTION_MARK = 0x00 #Define function code 定义功能码

class LidarNode(Node):
	
	last_message_stamp = datetime.now()
	query=[0x57,0x10,0xff,0xff,0x00,0xff,0xff,0x63] #Query the command with ID 0 查询ID为0的命令

	def __init__(self):
			super().__init__('lidar')

			self.buffer = bytes()
			self.serial = None
			self.TOF_rx_data=[0] * 16 #Create a list with 16 members 创建一个拥有16个成员的列表
			self.TOF_tx_data=[0x57,0x10,0xff,0xff,0x00,0xff,0xff,0x63] #Query the command with ID 0 查询ID为0的命令

			self.declare_parameter('port', '/dev/ttyS0', ParameterDescriptor(description="device from which the serial data will be read"))
			self.declare_parameter('baud', 921600, ParameterDescriptor(description="serial interface baudrate"))
			self.declare_parameter('period', 0.05, ParameterDescriptor(description="read interval"))
			self.declare_parameter('start_time', 0.0, ParameterDescriptor(description="Time to be used as the beginning of the simulation. Float value of seconds since epoch."))
			self.period = self.get_parameter('period').get_parameter_value().double_value
			self.port = self.get_parameter('port').get_parameter_value().string_value
			self.baud = self.get_parameter('baud').get_parameter_value().integer_value

			self.start_time = Time(seconds=self.get_parameter('start_time').get_parameter_value().double_value, clock_type=self.get_clock().clock_type)

			self.pub = self.create_publisher(Range, "range", 10)
			self.frame_id = f"{self.get_namespace()}/range"

			self.timer = self.create_timer(0, self.routine)
			self.count = 0
			logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
					level=logging.INFO,
					datefmt='%Y-%m-%d %H:%M:%S')
		
	def	get_current_timestamp(self) -> int:
		"""Return the current time in ms from the beginning of the simulation"""
		now: Time = self.get_clock().now()
		return (int((now - self.start_time).nanoseconds / MS_TO_NS))
	
	def routine(self):
		try:
			if not self.serial:
				self.serial: Serial = Serial(self.port, self.baud)
				self.get_logger().info(f"listening on port {self.port}, baud={self.baud}")
				self.timer.timer_period_ns = self.period * 1000 * 1000 * 1000
			self.TOF_Active_Decoding()

		except (serialutil.SerialException, OSError) as e:
			self.get_logger().error(f"Failed to read from serial: {e}\nRetrying...")
			self.timer.timer_period_ns = 10 * 1000 * 1000 * 1000
			self.serial = None

		except Exception as e:
			self.get_logger().error(f"Exception while parsing: {str(e)}")
			self.timer.timer_period_ns = 3 * 1000 * 1000 * 1000
			self.serial = None

	def publish(self, data: int):
		msg = Range()
		msg.header.stamp = self.get_clock().now().to_msg()
		msg.header.frame_id = self.frame_id
		msg.field_of_view = FOV
		msg.range = float(data) / 1e3
		msg.max_range = msg.range
		msg.min_range = msg.range
		msg.radiation_type = Range.ULTRASOUND
		self.pub.publish(msg)
		self.get_logger().debug(f"Published : {data}")

	def trigger_measure(self,id = 0):
		query = LidarNode.query
		query[4] = id #Add the ID you want to query to the command 将需要查询的ID添加到命令中
		query[7] = id + 0x63 #Update Checksum 更新校验和
		checksum = 0

		self.serial.flush() #Clear the serial port buffer 清空串口缓存
		self.serial.write(bytearray(query)) #Start query 开始查询
		time.sleep(0.01) #Waiting for the sensor to return data 等待传感器返回数据
		rx_data = list(self.serial.read(16)) #Reading sensor data 读取传感器数据

		for i in range (0,15):
			checksum = (checksum + rx_data[i]) & 0xFF #Calculate the checksum and take the lowest byte 计算检验和并取最低一个字节

		#Determine whether the decoding is correct 判断解码是否正确
		if (rx_data[0] == TOF_FRAME_HEADER) and (rx_data[1] == TOF_FUNCTION_MARK) and (checksum == rx_data[15]):
			# print("TOF id is: "+ str(rx_data[3]))  #ID of the TOF module TOF 模块的 ID

			system_time = rx_data[4] | rx_data[5]<<8 | rx_data[6]<<16 | rx_data[7]<<24
			# print("TOF system time is: "+str(system_time)+'ms') #The time after the TOF module is powered on TOF模块上电后经过的时间        

			distance = (rx_data[8]) | (rx_data[9]<<8) | (rx_data[10]<<16)
			# print("TOF distance is: "+str(distance)+'mm') #The distance output by the TOF module TOF模块输出的距离   
	
			status = rx_data[11]
			# print("TOF status is: "+str(status)) #Distance status indication output by TOF module TOF模块输出的距离状态指示
	
			signal_strength = rx_data[12] | rx_data[13]<<8
			# print("TOF signal strength is: "+str(signal_strength)) #The signal strength output by the TOF module TOF模块输出的信号强度

			range_precision = rx_data[14]
			# print("TOF range precision is: "+str(range_precision)) #The repeatability accuracy reference value output by the TOF module is invalid for Type C, Type D and Mini. TOF模块输出的重复测距精度参考值，对于C型,D型和Mini型是无效的
			self.get_logger().debug(f"distance={distance},status={status},strength={signal_strength},precision={range_precision}")

			if (distance == 0.0 or signal_strength == 0.0):
				distance = float('NaN')

			self.serial.flushInput() #Clear the serial port input register 清空串口输入寄存器
		else:
			raise Exception("Verification failed.")
		
		self.publish(distance)

	def TOF_Active_Decoding(self):
		self.serial.flushInput() #Clear the serial port input register 清空串口输入寄存器
		while True: #Waiting for serial port data 等待串口数据
			self.TOF_peek = ord(self.serial.read(1))  #Read a byte and convert it into an integer 读取一个字节并转换成整数
			if self.TOF_peek == TOF_FRAME_HEADER: #If it is a frame header, restart the loop count 如果是帧头,则重新开始循环计数
				self.count_i = 0
				self.TOF_rx_data[self.count_i] = self.TOF_peek #Store the read data into a tuple for later decoding 将读取到的数据存入元组中，用于后面解码使用
			else:
				self.TOF_rx_data[self.count_i] = self.TOF_peek #Store the read data into a tuple for later decoding 将读取到的数据存入元组中，用于后面解码使用

			self.count_i = self.count_i + 1 #Loop count +1 循环计数+1

			if self.count_i > 15:#If the number of received data is greater than 15, the count variable can be cleared and a decoding can be performed. 接收数量大于15,则可以将计数变量清零并进行一次解码
				self.count_i = 0
				for i in range (0,15):
					self.check_sum = (self.check_sum + self.TOF_rx_data[i]) & 0xFF #Calculate the checksum and take the lowest byte 计算检验和并取最低一个字节

				#Determine whether the decoding is correct 判断解码是否正确
				if (self.TOF_rx_data[0] == TOF_FRAME_HEADER) and (self.TOF_rx_data[1] == TOF_FUNCTION_MARK) and (self.check_sum == self.TOF_rx_data[15]):

					distance = (self.TOF_rx_data[8]) | (self.TOF_rx_data[9]<<8) | (self.TOF_rx_data[10]<<16)
			
					status = self.TOF_rx_data[11]
			
					signal_strength = self.TOF_rx_data[12] | self.TOF_rx_data[13]<<8

					range_precision = self.TOF_rx_data[14]

					if (distance == 0.0 or signal_strength == 0.0):
						distance = float('NaN')

					self.get_logger().debug(f"distance={distance},status={status},strength={signal_strength},precision={range_precision}")
					self.publish(distance)
					break
				else:
					raise Exception("Verification failed.")
			self.check_sum = 0 #Clear Checksum 清空校验和

def main(args=None):
	try:
		rclpy.init(args=args)
		sensor_publisher = LidarNode()
		rclpy.spin(sensor_publisher)
	
	except (KeyboardInterrupt, ExternalShutdownException):
		pass


if __name__ == '__main__':
	main()
