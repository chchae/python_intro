import cx_Oracle
import multiprocessing
import time
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor, Future, wait
import typing as T


from modeller import *
from modeller.automodel import *

log.verbose()
log.level(output=0, notes=0, warnings=0, errors=1, memory=0)
env = Environ()
env.io.atom_files_directory = ['/share/databases/PDB', '../atom_files']
env.libs.topology.read('${LIB}/top_heav.lib')
env.libs.parameters.read('${LIB}/par.lib')







def binary_pdb_sequence_db( alldb=False ) -> str :
    global env
    sdb = SequenceDB(env)
    pirfile = '../pir/20220710_pdb95.pir'
    if alldb == True :
        pirfile = '../pir/pdball.pir'
    sdb.read(seq_database_file=pirfile, seq_database_format='PIR', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True)

    sdbfname = os.path.join( tempfile.mkdtemp(), '20220710_pdb95.pir.bin' )
    sdb.write(seq_database_file=sdbfname, seq_database_format='BINARY', chains_list='ALL')
    print( "\n\n===>make temporary sequence db file", sdbfname )
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
    #fname = str( '/tmp/' ) + aln[0].code + '.alignment'
    #with open( fname, 'w+' ) as f :
    with tempfile.TemporaryFile() as f :
        aln.write( f )
        f.seek(0)
        aln.clear()
        aln.read_one(f)
        f.close()
        return aln

def build( sdbfname, code : str, seq : str ) :
    global env
    # print( "\nbuilder", code, seq )
    aln = Alignment(env)
    aln.append_sequence( seq )
    aln[0].code = code
    aln = writereadaln(aln)
    # print( "\nbuilder", aln[0].code, sequence2string( aln[0] ) )
    # aln.check()
    sdb = SequenceDB(env)
    sdb.read( seq_database_file=sdbfname, seq_database_format='BINARY', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True )
    # print( "\nbuilder", len(sdb), aln[0].code, sequence2string( aln[0] ) )
    ( pdb, chain, fid, evalue ) = find_sequence_homology( sdb, aln )
    if( 30.0 < fid ) :
        print( "\n===> best homology found for %s : %s %s %f %f\n" % ( aln[0].code, pdb, chain, fid, evalue ) )
        # print( "build", aln[0].code, sequence2string(aln[0]) )
        build_structure_from_template( pdb, chain, aln )
    else :
        print( "\n===> no   homology found for %s : %s %s %f %f... skipping...\n" % ( aln[0].code, pdb, chain, fid, evalue ) )







def initialize_oracle( url_db ) :
    with cx_Oracle.connect( url_db ) as conn :
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


def make_alignment( code, seq ) -> Alignment :
    global env
    aln = Alignment(env)
    aln.append_sequence( seq )
    aln[0].code = code
    aln = writereadaln(aln)
    return aln


def work_subr( sdb, aln ) :
    ( pdb, chain, fid, evalue ) = find_sequence_homology( sdb, aln )
    if 30.0 < fid :
        print( "\n---> best homology found for %s : %s %s %f %f\n" % ( aln[0].code, pdb, chain, fid, evalue ) )
        # print( "build", aln[0].code, sequence2string(aln[0]) )
        build_structure_from_template( pdb, chain, aln )
    else :
        print( "\n---> no   homology found for %s : %s %s %f %f... skipping...\n" % ( aln[0].code, pdb, chain, fid, evalue ) )



def work( url_db, sdbfname, jobid ) :
    global env
    sdb = SequenceDB(env)
    sdb.read( seq_database_file=sdbfname, seq_database_format='BINARY', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True )

    with cx_Oracle.connect( url_db ) as conn :
        with conn.cursor() as cursor :
            count = 0
            while True :
                code, seq = fetch_sequence_from_oracle( cursor )
                count = count + 1
                if 3 < count :
                    break
                if "" == code :
                    break
                print('--->', jobid, code)

                aln = make_alignment( code, seq )
                work_subr( sdb, aln )

        conn.commit()
        time.sleep(5)



def main() :
    sdbfname = binary_pdb_sequence_db()

    url_db = 'virusdb/virus4db@virusdb.camd.krict.re.kr/orcl'
    initialize_oracle(url_db)

    MAX_WORKERS : int = 4
    with ProcessPoolExecutor( max_workers=MAX_WORKERS ) as thread_pool :
        threads : T.List(Future) = []
        for i in range(MAX_WORKERS) :
            threads.append( thread_pool.submit( work, url_db, sdbfname, i, ) )

        wait( threads )





if __name__ == '__main__' :
    main()


