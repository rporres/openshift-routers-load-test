import sys
import lzma
import statistics
from os import listdir
from os.path import isfile, join, basename

ROUND_PRECISION = 2

# Process an xz file
def process(xz_file):
    with lzma.open(xz_file) as f:
        lines = f.read().decode().strip('\n').split('\n')

        first_request = lines[0].split(",")
        last_request = lines[-1].split(",")
        latencies = []
        end_times = []
        status = {}
        errors = 0
        for line in lines:
            fields = line.split(",")
            if len(fields) != 15:
                raise Exception("Unknown line format [%s])" % line)

            latencies.append(int(fields[1]))
            end_times.append(int(fields[0]) + int(fields[1]))
            if fields[2] in status:
                status[fields[2]] += 1
            else:
                status[fields[2]] = 1

            if fields[14]:
                errors += 1

        total_requests = len(latencies)
        attack_duration = int(last_request[0]) - int(first_request[0])
        request_rate = round(total_requests / (attack_duration/1e6),
                             ROUND_PRECISION)
        median = statistics.median(latencies) / 1e3
        for code, i in status.items():
            if code[0] == "4" or code[0] == 5:
                errors += i

        error_rate = round(errors / (attack_duration/1e6), ROUND_PRECISION)

        print("%s %s %s %s" % (basename(xz_file)[0:-3], request_rate, median,
                               error_rate))

# We may want to reorder this afterwards
directory = sys.argv[1]
xz_files = sorted([f for f in listdir(directory) if f[-3:] == ".xz"])
for f in xz_files:
    process(join(directory, f))
