import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1

max_requests = 1000
max_requests_jitter = 50
