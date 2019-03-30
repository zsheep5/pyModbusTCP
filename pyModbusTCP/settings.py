import time
SERVER_IP_ADDRESS = '192.168.1.120'
PORT = 502
SERVER_NAME= ':memory:'
DATABASE_NAME='MPI_ModBus.db'
DATABASE_PATH= '/'  #empty uses the current working directory
DATABASE_BACKUP_PATH = ''
CLIENT_STARTING_IP= '192.168.1'
CSV_DUMP_Path= ''
SCAN_SLEEP_TIME=3  # the time the server sleeps between bit_command scans 
SERVER_PRINT_REGISTER_CHANGES = False
SERVER_BLOCKING = True
LOG=True
LOG_NAME='ModBus_Log_%s.log' % (str(time.localtime()).replace(':','-'))

