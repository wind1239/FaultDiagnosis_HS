# coding=UTF-8
import numpy as np
import random
import MySQLdb
import time



class MainBlock(object):
	"""docstring for MainBlock"""
	def __init__(self):
		super(MainBlock, self).__init__()

		self._1 = list();

		self._output = list();


###########################################################
# 01-Process the data
###########################################################
	def LoadData(self,feature,name,startTime,endTime):
		database = MySQLdb.connect('localhost','root','qwert','FaultDiagnosis');
		with database:
			cursor = database.cursor();
			cursor.execute('SELECT PublicationDate,{0} FROM Status_sensor WHERE id >= \'{1}\' AND id <= \'{2}\''.format(name,startTime,endTime));
			data = cursor.fetchall();
			for datum in data:
				feature.append([datum[0],float(datum[1])]);
			cursor.close();
		database.close();


	def outputReport(self,startTime,threshold,tolerance):
		# analyze feature
		for index in xrange(len(self._1)):
			# can not analyze with only one datum
			if index < 5:
				self._output.append([self._1[index][0],0,'正常','接力器反馈','无']);
				continue;
			elif np.abs(self._1[index][1]-self._1[index-1][1]) > tolerance:
				self._output.append([self._1[index][0],0,'正常']);
				continue;
			# inference
			globalK = np.abs((self._1[0][1] - self._1[index][1])/float(index/100.0));
			localK = np.abs((self._1[index-1][1] - self._1[index][1])/float(1/100.0));
			if globalK > threshold and localK > threshold:
				self._output.append([self._1[index][0],1,'接力器反馈异常','接力器反馈','接力器最快速度关闭时间斜率变化']);
			elif np.abs(globalK - localK) > 0.2:
				self._output.append([self._1[index][0],1,'接力器反馈异常','接力器反馈','接力器反馈采样值突变']);
			else:
				self._output.append([self._1[index][0],0,'正常','接力器反馈','无']);

		# print self._output;


		# edit log
		log_record = list();
		for index in xrange(len(self._output)):
			if index == 0:
				continue;

			if self._output[index][1] == 1 and self._output[index-1][1] == 0:
				log_record.append([self._output[index][0],self._output[index][2],self._output[index][3],self._output[index][4]]);
			elif self._output[index][1] == 1 and self._output[index-1][1] == 1 and self._output[index][2] != self._output[index-1][2]:
				log_record.append([self._output[index][0],self._output[index][2],self._output[index][3],self._output[index][4]]);

		# input log
		database = MySQLdb.connect('localhost','root','qwert','FaultDiagnosis');
		with database:
			cursor = database.cursor();
			for index in xrange(len(log_record)):
				cursor.execute('INSERT into Status_log(PublicationDate,LogInformation,ErrorEquipment,Reason) values(\'{0}\',\'{1}\',\'{2}\',\'{3}\')'.format(log_record[index][0],log_record[index][1],log_record[index][2],log_record[index][3]));
				database.commit();
			cursor.close();
		database.close();

		# input analysis
		database = MySQLdb.connect('localhost','root','qwert','FaultDiagnosis');
		with database:
			cursor = database.cursor();
			for x in xrange(len(self._output)):
				cursor.execute('INSERT into Status_prediction(id,PublicationDate,JieLiQiFanKui_2) values(\'{0}\',\'{1}\',\'{2}\')'.format(x+startTime,self._output[x][0],self._output[x][1]));
				database.commit();
			cursor.close();
		database.close();

def main():
	# initialize
	startTime = 401;
	endTime = startTime+99;
	threshold = 1.3;
	tolerance = 0.3*1;

	task = MainBlock();

	variableName = ['ServomotorFeedback_1'];
	variable = [task._1];
	for index in range(len(variable)):
		task.LoadData(variable[index],variableName[index],startTime,endTime);

	task.outputReport(startTime,threshold,tolerance);




if __name__ == '__main__': main();