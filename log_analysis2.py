
import gzip
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import glob
import json
import csv

# This works by finding the Bitcoin logs after the beta upgrade 0.3.9

todays_date = datetime.utcnow().strftime('%Y-%m-%d')


# REG_EXP = r'^(.*)umbrel bitcoin.*UpdateTip.*height=([\d]*).*progress=([\d.]*)\s'
REG_EXP = rf'^({todays_date}.*).*UpdateTip.*height=([\d]*).*progress=([\d.]*)\s'
COUNT_LINES = 1000



# def get_line(f):
#     """ return a line from a file binary or regular """


def output_data(file,all_data, summary_data):
    if not os.path.exists('syslog_out'):
        os.mkdir('syslog_out')


    all_data_header = ['timestamp','block','percentage']
    summary_header = ['timestamp', 'percentage','interval','progress','blocks']
    f_name, f_ext = os.path.splitext(os.path.basename(file))
    print(f'Output - {f_name}')

    file_out = os.path.join('syslog_out', f_name + '_all_data.csv')
    with open(file_out, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(all_data_header)
        writer.writerows(all_data)

    file_out = os.path.join('syslog_out', f_name + '_summary_data.csv')
    with open(file_out, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(summary_header)
        writer.writerows(summary_data)


if __name__ == '__main__':
    latest = True

    print(os.system('vcgencmd measure_temp'))
    yearnow = datetime.utcnow().year


    pathlist = glob.glob('/var/log/syslog.*')
    if latest:
        pathlist = ['/home/umbrel/umbrel/bitcoin/debug.log']
    else:
        pathlist.sort(key=os.path.getmtime, reverse=False)


    for file in pathlist:
        all_data = []
        summary_data = []
        print(file)
        hour_last = 0
        data = []
        delta_p = 0.0
        delta_t = timedelta(minutes=1)
        a_line = True

        if re.search(r'.*gz', file):
            binary = True
            f = gzip.open(file, 'rb')
        else:
            binary = False
            f = open(file, 'r')

        while a_line:
            if binary:
                a_line = f.readline().decode()
            else:
                a_line = f.readline()
            ans = re.search(REG_EXP, a_line)
            if ans:
                tstamp = ans[1]
                d = datetime.strptime(tstamp, '%Y-%m-%dT%H:%M:%SZ ')
                data.append((d,ans[2],float(ans[3])))
                all_data.append((d,ans[2],float(ans[3])))
                # if len(data) > COUNT_LINES:
                # if delta_p > 0.001:
                while delta_t > timedelta(hours=1):

                    hour = data[-1][0].hour
                    if not hour == hour_last:
                        print(f'{data[-1][0]} - {data[-1][2]} - {delta_t} - {delta_p:0.3f} - {len(data)}')
                        summary_data.append((data[-1][0],data[-1][2],delta_t,delta_p,len(data)))
                    data.pop(0)
                    delta_t = data[-1][0] - data[0][0]
                    delta_p = (data[-1][2] - data[0][2]) * 100
                    hour_last = hour

                delta_t = data[-1][0] - data[0][0]
                delta_p = (data[-1][2] - data[0][2]) * 100
        first_day = f'{summary_data[0][0]:%Y-%m-%d}'
        output_data(first_day,all_data,summary_data)
        f.close()
