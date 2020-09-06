"""
The Plan:
- Open given file
- Parse XML
- Record given fields to CSV
"""
cur_ver="1.0"
print("--[ aCar to Fuellio convertor v"+cur_ver+"]--")

import codecs
import xml.etree.ElementTree as ET



def get_xml_val(xml_obj, name):
	ret = xml_obj.find(name).text
	if (ret):
		return ret
	else:
		return ''

def date_convert(src_date):
	date_l1 = src_date.split(' - ')
	date_l2 = date_l1[0].split('/')
	new_date = ' '.join(['-'.join([date_l2[2],date_l2[0],date_l2[1]]), date_l1[1]])
	return new_date

def re_round(value, how_much=0):
	if(value):
		try:
			rounded_value = float(value)
		except:
			pass
	else:
		rounded_value = 0.0

	if(how_much):
		rounded_value = str(round(rounded_value, how_much))
	else:
		rounded_value = str(round(rounded_value))

	return rounded_value 

quick_help = "\n--[ Quick help | Справка ]--\
\nIn order to use convertor you should:\
\n 1. Copy backup from your phone to PC. \
\n 2. Rename aCar-050920-0707.abp to aCar-050920-0707.abp.zip \
\n 3. Extract files vehicles.xml and event-subtypes.xml to same folder as this convertor. \
\n 4. After program finishes (with no error) copy <car-name>.xml files to \
\n    <android_flash>/Fuelio/backup-csv on your phone \
\n 5. In Fuelio go to Settings->Backup(Create/Restore)->ImportCSV and import every car.\
\n ------------------------------------------------------------------------------------ \
\n 1. Скопируйте резервную копию с телефона на комп. \
\n 2. Переименуйте aCar-050920-0707.abp в aCar-050920-0707.abp.zip \
\n 3. Распакуйте файлы vehicles.xml и event-subtypes.xml в директорию с этой программой. \
\n 4. После запуска программы (если небыло ошибок) скопируйте файлы <car-name>.xml \
\n    в <android_flash>/Fuelio/backup-csv на телефоне \
\n 5. В Fuelio зайдите Settings->Backup(Create/Restore)->ImportCSV, импорт для каждой машины.\
"

print("--[ Loading XML files]--")
print("    vehicles.xml...               ", end=" ")
try:
	tree = ET.parse('vehicles.xml')
	print ("[ done ]")
except:
	print ("\n/!\\ WARINING! File not found, program terminated")
	print (quick_help)
	quit()

print("    event-subtypes.xml...         ", end=" ")
try:
	event_tree = ET.parse('event-subtypes.xml')
	print ("[ done ]")
except:
	print ("\n/!\\ WARINING! File not found, program terminated")
	print (quick_help)
	quit()

root = tree.getroot()
event_root = event_tree.getroot()

print ("\n--[ Processing vehicles ]--")
for this_car in root.iter('vehicle'):
	print("\n    ->Processing "+get_xml_val(this_car, 'name'))

	dst_list = []
	dst_list.append('"## Vehicle"')
	dst_list.append('"'+'","'.join([
		'Name','Description','DistUnit','FuelUnit','ConsumptionUnit','ImportCSVDateFormat','VIN',
		'Insurance','Plate','Make','Model','Year','TankCount','Tank1Type','Tank2Type','Active',
		'Tank1Capacity','Tank2Capacity','FuelUnitTank2','FuelConsumptionTank2'
		])+'"'
	)
	# --[ CAR DATA ]--
	if (this_car.find('active').text): is_active="1"	
	dst_list.append('"'+'","'.join([
		get_xml_val(this_car, 'name'), '', '0', '0', '0', 'yyyy-MM-dd',
		get_xml_val(this_car,'vin'), get_xml_val(this_car,'insurance-policy'), 
		get_xml_val(this_car,'license-plate'), get_xml_val(this_car,'make'),
		get_xml_val(this_car,'model'), get_xml_val(this_car,'year'),
		'1','100','0',is_active,
		get_xml_val(this_car,'fuel-tank-capacity'),'0.0','0','0'
		])+'"'
	)

	print("    converting fuel records...    ", end=" ")
	dst_list.append('"## Log"')
	dst_list.append('"'+'","'.join([
		'Data','Odo (km)','Fuel (litres)','Full','Price (optional)','l/100km (optional)',
		'latitude (optional)','longitude (optional)','City (optional)','Notes (optional)',
		'Missed','TankNumber','FuelType','VolumePrice','StationID (optional)','ExcludeDistance',
		'UniqueId','TankCalc'
		])+'"'
	)
	# --[ FUEL RECORDS ]--
	"""
	ToDo: fix fuel type table
	"""
	for fuel_rec in this_car.iter('fillup-record'):
		is_full="1"
		if (get_xml_val(fuel_rec,'partial') == 'true'):
			is_full="0"
			
		has_missed="0"
		if (get_xml_val(fuel_rec,'previous-missed-fillups') == 'true'):
			has_missed="1"

		dev_lat = "0.0"
		if (get_xml_val(fuel_rec,'device-latitude')):
			dev_lat = re_round(get_xml_val(fuel_rec,'device-latitude'), 5)
		
		dev_lon = "0.0"
		if (get_xml_val(fuel_rec,'device-longitude')):
			dev_lon = re_round(get_xml_val(fuel_rec,'device-longitude'), 5)	

		fuel_part1 = '"'+'","'.join([
				date_convert(get_xml_val(fuel_rec, 'date')),
				get_xml_val(fuel_rec, 'odometer-reading'),
				re_round(get_xml_val(fuel_rec, 'volume'), 1),
				is_full, get_xml_val(fuel_rec, 'total-cost'),
				re_round(get_xml_val(fuel_rec, 'fuel-efficiency'), 2), 
				dev_lat, dev_lon
			])+'"'
		fuel_part2 = '"'+'","'.join([get_xml_val(fuel_rec,'notes').replace('\n', '; '),
				has_missed, '1', '110', 
				get_xml_val(fuel_rec,'price-per-volume-unit'), '0', '0.0',
				fuel_rec.get('id'), '0.0',
			])+'"'

		dst_list.append(",".join([fuel_part1,'',fuel_part2]))

	print ("[ done ]")

	dst_list.append('"## CostCategories"')
	dst_list.append('"CostTypeID","Name","priority","color"')

	cat_list = [
			['1','Service','0'],
			['2','Maintenance','0'],
			['4','Registration','0'],
			['5','Parking','0'],
			['6','Wash','0'],
			['7','Tolls','0'],
			['8','Tickets/Fines','0'],
			['9','Tuning','0'],
			['31','Insurance','0']
		]

	for join_me in cat_list:
		dst_list.append('"'+'","'.join(join_me)+'",""')

	print("    converting service records... ", end=" ")
	dst_list.append('"## Costs"')
	dst_list.append('"'+'","'.join([
		'CostTitle','Date','Odo','CostTypeID','Notes','Cost','flag','idR','read','RemindOdo','RemindDate',
		'isTemplate','RepeatOdo','RepeatMonths','isIncome','UniqueId'
		])+'"'
	)
	# --[ SRVICE RECORDS ]--
	for svc_rec in this_car.iter('event-record'):
		record_type = get_xml_val(svc_rec,'type')
		job_name="Service"

		if (record_type == 'service'):
			cost_type='1'
			all_jobs = []
			
			for svc_type in svc_rec.find('subtypes'):
				all_jobs.append(event_tree.find('.//event-subtype[@id="'+svc_type.get('id')+'"]/name').text)
			
			all_jobs_string=", ".join(all_jobs) 
			if all_jobs_string: job_name = all_jobs_string			
			if len(job_name) > 127:
				job_name=job_name[:127]

		if (record_type == 'purchased'):
			cost_type='4'
			job_name='Registration'

		dst_list.append('"'+'","'.join([
				job_name,
				date_convert(get_xml_val(svc_rec,'date')),
				re_round(get_xml_val(svc_rec,'odometer-reading')),
				cost_type,
				get_xml_val(svc_rec,'notes').replace('\n', '; '),
				get_xml_val(svc_rec,'total-cost'),
				'0','0','1','0','2011-01-01','0','0','0','0',
				svc_rec.get('id')
			])+'"'
		)

	print ("[ done ]")
	dst_list.append('"## Category"')
	cost_list = [
			['IdCategory','Name'],
			['1','Private'],
			['2','Work']
		]

	for join_me in cost_list:
		dst_list.append('"'+'","'.join(join_me)+'"'
	)

	write_me_to_file = "\n".join(dst_list)
	print("    writing records to csv file...", end=" ")
	with codecs.open("fl_"+get_xml_val(this_car, 'name').replace(' ',"-")+".csv", "w", "utf-8") as csv_file:
		csv_file.write(write_me_to_file)
		csv_file.close()
	print ("[ done ]")

print("\n --[ Conversion complete! ]--")
