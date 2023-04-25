
import csv
import datetime
import os
import sys
import time

from openpyxl import Workbook


target_dir = sys.argv[1]

temps = {}

csv_path = os.path.join(target_dir, 'temperatures.csv')
with open(csv_path, encoding='utf-8') as csv_file:
    for line in csv_file.readlines():
        ts, t1, t2 = [float(x) for x in line.split(',')]
        temps[int(ts)] = t1,t2


wb = Workbook()

vna1_count = 0
vna2_count = 0

# Iterate through data files in directory
for file in sorted(os.listdir(target_dir)):

    # check if the file is a .csv (and not the temperatures.csv file)
    if not file.endswith('.csv') or file == 'temperatures.csv':
        continue

    x = file.removesuffix('.csv').split('_')

    ts = int(time.mktime(datetime.datetime(int(x[0]), int(x[1]), int(x[2]), int(x[3]), int(x[4]), int(x[5])).timetuple()))

    # build name for new sheet
    if x[-1] == 'vna1':
        vna1_count += 1
        sheet_name = f'v1_{vna1_count}'
    elif x[-1] == 'vna2':
        vna2_count += 1
        sheet_name = f'v2_{vna2_count}'
    else:
        raise RuntimeError('Encountered a file with an invalid name.')
    
    print(sheet_name)

    # Create new sheet
    wb.create_sheet(sheet_name)
    ws = wb[sheet_name]

    # Add temperature at the top
    ws['A1'] = 'Temperature (degC):'

    temp = temps.get(ts)
    if temp is None:
        print(f'WARNING: Unable to find corresponding temperature for {sheet_name}')
    ws['B1'] = temp[0]  # TODO: must decide between temp1 and temp2

    # Add CSV below temperature
    fpath = os.path.join(target_dir, file)
    with open(fpath, encoding='utf-8') as dataf:
        for lino, line in enumerate(dataf.readlines()):
            if ',' in line:
                a,b = line.split(',')
                ws[f'A{3+lino}'] = a
                ws[f'B{3+lino}'] = b
            else:
                ws[f'A{3+lino}'] = line


# build path to save to
wb_path = os.path.join(target_dir, 'combined_data.xlsx')

# save the workbook
wb.save(wb_path)
