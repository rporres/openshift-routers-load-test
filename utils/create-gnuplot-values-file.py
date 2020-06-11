import sys
import lzma
from os import listdir
from os.path import isfile, join, basename, splitext

import pandas as pd

ROUND_PRECISION = 2

columns = ["start_request",
           "delay",
           "status",
           "written",
           "read",
           "method_and_url",
           "thread_id",
           "conn_id",
           "conns",
           "reqs",
           "start",
           "socket_writable",
           "conn_est",
           "tls_reuse",
           "err"]


def process(xz_file):
    with lzma.open(xz_file) as f:
        df = pd.read_csv(f, names=columns, keep_default_na=False)

    median = df['delay'].median() / 1e3

    http_errors = df['status'].apply(lambda x: int(x / 100) in [4, 5])
    total_http_errors = len(http_errors[http_errors==True])

    conn_errors = (df['err'] != '')
    total_conn_errors = len(conn_errors[conn_errors==True])

    total_requests = len(df)
    total_errors = total_http_errors + total_conn_errors

    end_time = df['start_request'][total_requests - 1]
    start_time = df['start_request'][0]
    attack_duration = end_time - start_time

    error_rate = round(total_errors / (attack_duration / 1e6), ROUND_PRECISION)
    request_rate = round(
        total_requests / (attack_duration / 1e6), ROUND_PRECISION)

    configuration = splitext(basename(xz_file))[0]
    print(configuration, request_rate, median, error_rate)


if __name__ == '__main__':
    directory = sys.argv[1]
    xz_files = sorted([f for f in listdir(directory) if f.endswith('.xz')])
    for f in xz_files:
        process(join(directory, f))
