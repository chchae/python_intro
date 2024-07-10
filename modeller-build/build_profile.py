from modeller import *

log.verbose()
env = Environ()

sdb = SequenceDB(env)
sdb.read(seq_database_file='20220710_pdb95.pir', seq_database_format='PIR',
         chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True)



