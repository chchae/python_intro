import oracledb
import math
import multiprocessing
import sys, os, time, tempfile
from concurrent.futures import ProcessPoolExecutor, Future, wait
import typing as T

from modeller import *
from modeller.automodel import *


#
# oracle db : isworking = 0 : intact, 1 : working, 2 : done, 3 : fail
#


log.verbose()
log.level(output=0, notes=0, warnings=0, errors=1, memory=0)
env = Environ()
env.io.atom_files_directory = ['/share/databases/PDB', '../atom_files']
env.libs.topology.read('${LIB}/top_heav.lib')
env.libs.parameters.read('${LIB}/par.lib')


def generate_cpu_load(interval=30,utilization=50):
    start_time = time.time()
    for i in range(0,int(interval)):
        while time.time()-start_time < utilization/100.0:
            a = math.sqrt(64*64*64*64*64)
        # print(str(i) + ". About to sleep")
        time.sleep(1-utilization/100.0)
        start_time += 1

def burner() :
    generate_cpu_load( 30, 30 )



def binary_pdb_sequence_db( alldb=False ) -> str :
    global env
    sdb = SequenceDB(env)
    pirfile = '../pir/20220710_pdb95.pir'
    if alldb == True :
        pirfile = '../pir/pdball.pir'
    sdb.read(seq_database_file=pirfile, seq_database_format='PIR', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True)

    # sdbfname = os.path.join( tempfile.mkdtemp(), '20220710_pdb95.pir.bin' )
    sdbfname = next( tempfile._get_candidate_names() )
    sdbfname = os.path.join( '/tmp', sdbfname )
    sdb.write(seq_database_file=sdbfname, seq_database_format='BINARY', chains_list='ALL')
    print( f"\n--->made temporary sequence db file [{sdbfname}]...\n" )
    return sdbfname



def find_best_profile( prf ) :
    best_evalue = 9999.0
    best_fid = 0
    best_pdb = ""
    best_chain = ""
    best_neqv = 0
    for itm in prf :
        if ( itm._Sequence__get_evalue() <= best_evalue and best_fid <= itm._Sequence__get_fid() and best_neqv <= itm._Sequence__get_neqv() ) :
            best_evalue = itm._Sequence__get_evalue()
            best_fid = itm._Sequence__get_fid()
            code = itm._Sequence__get_code()
            best_pdb = code[:4]
            best_chain = code[4]
            best_neqv = itm._Sequence__get_neqv()

    return ( best_pdb, best_chain, best_fid, best_evalue )


def find_sequence_homology( seqdb, aln ) :
    code = aln[0].code
    prf = aln.to_profile()

    prf.build(seqdb, matrix_offset=-450, rr_file='${LIB}/blosum62.sim.mat',
              gap_penalties_1d=(-500, -50), n_prof_iterations=1,
              check_profile=False, max_aln_evalue=0.01)

    return find_best_profile( prf )




def sequence2string( seq ) -> str :
    return ''.join( [ res.code for res in seq.residues ] )


def build_structure_from_template( pdb, chain, aln0 ) :
    global env
    aln = Alignment(env)
    mdl = Model(env, file=pdb, model_segment=('FIRST:'+chain, 'LAST:'+chain) )
    aln.append_model(mdl, align_codes=pdb+chain, atom_files='pdb'+pdb+'.ent.gz')
    aln.append_profile( aln0.to_profile() )
    aln.align2d(max_gap_length=50)

    a = AutoModel(env, alnfile=aln,
        knowns=pdb+chain, sequence=aln[1].code,
        assess_methods=(assess.DOPE,
        #soap_protein_od.Scorer(),
        assess.GA341))
    a.starting_model = 1
    a.ending_model = 1
    a.make()


def writereadaln( aln ) -> Alignment :
    with tempfile.TemporaryFile() as f :
        aln.write( f )
        f.seek(0)
        aln.clear()
        aln.read_one(f)
        f.close()
        return aln


def db_connect( url ) :
    return oracledb.connect( user=url[0], password=url[1], dsn=url[2] )


def initialize_oracle( url ) :
    with db_connect(url) as conn :
        with conn.cursor() as cursor :
            sql = "UPDATE VirusSequence SET isworking = 0 where isworking <> 0"
            cursor.execute( sql )
        conn.commit()


def fetch_sequence_from_oracle( cursor ) :
    sql = """
        UPDATE VirusSequence SET isworking = 1
        WHERE isworking = 0 and ROWNUM = 1
        RETURNING code, sequence into :ret_code, :ret_seq
        """
    ret_code = cursor.var(str)
    ret_seq  = cursor.var(str)
    cursor.execute( sql, ret_code=ret_code, ret_seq=ret_seq )
    code = ret_code.getvalue()[0]
    seq  = ret_seq.getvalue()[0]
    return code, seq



def fetch_sequence_from_oracle_connection( conn ) :
    with conn.cursor() as cursor :
        sql = """
            UPDATE VirusSequence SET isworking = 1
            WHERE isworking = 0 and ROWNUM = 1
            RETURNING code, sequence into :ret_code, :ret_seq
            """
        ret_code = cursor.var(str)
        ret_seq  = cursor.var(str)
        cursor.execute( sql, ret_code=ret_code, ret_seq=ret_seq )
        conn.commit()
        code = ret_code.getvalue()[0]
        seq  = ret_seq.getvalue()[0]
        return code, seq


def mark_oracle_as_done( conn, code, ISDONE = 0 ) :
    with conn.cursor() as cursor :
        sql = f"UPDATE VirusSequence SET isworking = {ISDONE} WHERE code = '{code}'"
        #print( sql )
        cursor.execute( sql )
        conn.commit()


def make_alignment( code, seq ) -> Alignment :
    global env
    aln = Alignment(env)
    aln.append_sequence( seq )
    aln[0].code = code
    aln = writereadaln(aln)
    return aln


def work_subr( sdb, aln ) -> int :
    (pdb, chain, fid, evalue ) = find_sequence_homology( sdb, aln )
    if 30.0 < fid :
        print( "\n---> best homology found for %s (%d) : %s %s %f %f\n" % ( aln[0].code, aln[0].naln, pdb, chain, fid, evalue ) )
        build_structure_from_template( pdb, chain, aln )
        return 1
    else :
        print( "\n---> no   homology found for %s (%d) : %s %s %f %f... skipping...\n" % ( aln[0].code, aln[0].naln, pdb, chain, fid, evalue ) )
        return 0



def work_parallel( url_db, sdbfname, jobid ) :
    print( f"\n\n###>worker {jobid} begins...\n" )

    global env
    sdb = SequenceDB(env)
    sdb.read( seq_database_file=sdbfname, seq_database_format='BINARY', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True )

    with db_connect( url_db ) as conn :
        count = 0
        while True :
            code, seq = fetch_sequence_from_oracle_connection( conn )
            if "" != code :
                print('--->', jobid, code, len(seq) )
                aln = make_alignment( code, seq )
                ret = work_subr( sdb, aln )

                if 0 < ret :
                    ISDONE = 2
                    mark_oracle_as_done( conn, code, ISDONE )
                    count = count + 1
                else :
                    ISFAIL = 3
                    mark_oracle_as_done( conn, code, ISFAIL )

                if 3 < count :
                    break

    print( f"\n\n###>worker {jobid} ends...\n\n" )



def main() :
    sdbfname = binary_pdb_sequence_db()

    url_db = ( 'virusdb', 'virus4db', 'virusdb.camd.krict.re.kr/orcl' )
    initialize_oracle(url_db)

    MAX_WORKERS : int = multiprocessing.cpu_count() - 1
    with ProcessPoolExecutor( max_workers=MAX_WORKERS ) as thread_pool :
        threads : T.List(Future) = []
        for i in range(MAX_WORKERS) :
            threads.append( thread_pool.submit( work_parallel, url_db, sdbfname, i, ) )

        wait( threads )

    os.remove( sdbfname )




if __name__ == '__main__' :
    main()


