import copy
import time
from random import randint
import tempfile
from multiprocessing import Pool, Process, Lock, Manager, Semaphore
from concurrent.futures import ProcessPoolExecutor, Future, wait
import typing as T
from modeller import *
from modeller.automodel import *

log.verbose()
log.level(output=0, notes=0, warnings=1, errors=1, memory=0)
env = Environ()
env.io.atom_files_directory = ['/share/databases/PDB']






def read_pdb_sequence_db( alldb=False ) :
    global env
    sdb = SequenceDB(env)
    pirfile = '../pir/20220710_pdb95.pir'
    if alldb == True :
        pirfile = '../pir/pdball.pir'
    sdb.read(seq_database_file=pirfile, seq_database_format='PIR', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True)
#   sdb.write(seq_database_file='../pir/20220710_pdb95.pir.bin', seq_database_format='BINARY', chains_list='ALL')
    return sdb



# to find best profile
def write_read_profile( prf ) :
    prf.write(file='/tmp/' + seqcode + '_build_profile.prf', profile_format='TEXT')
    aln = prf.to_alignment()
    aln.write(file='/tmp/' + seqcode + '_build_profile.ali', alignment_format='PIR')

    with tempfile.NamedTemporaryFile() as prfile:
        prf.write(file=prfile, profile_format='TEXT')
        with open( prfile.name ) as ifile:
            toks = [ line.split() for line in ifile.readlines() if not line.startswith('#' ) ]
            toks = [ ( tok[1][:4], tok[1][4:], tok[10] ) for tok in toks if float(tok[10]) > 35.0 ]
            toks = sorted( toks, key=lambda x: x[2], reverse=True )

    return toks



def find_best_profile_0( prf ) :
    best_evalue = 9999.0
    best_fid = 0
    best_pdb = ""
    best_chain = ""
    for i in range( len(prf.positions) ) :
        itm = prf.__getitem__(i)
        if ( itm.evalue <= best_evalue and best_fid <= itm.fid ) :
            best_evalue = itm.evalue
            best_fid = itm.fid
            best_pdb = itm.code[:4]
            best_chain = itm.code[4]

    return ( best_pdb, best_chain, best_fid, best_evalue )



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
    global env
    code = aln[0].code
    prf = aln.to_profile()

    prf.build(seqdb, matrix_offset=-450, rr_file='${LIB}/blosum62.sim.mat',
              gap_penalties_1d=(-500, -50), n_prof_iterations=1,
              check_profile=False, max_aln_evalue=0.01)

    if( False ) :
        write_read_profile( prf )

    return find_best_profile( prf )



def align_sequence_structure_for_best_template( toks, code ):
    global env
    aln = Alignment(env)
    for tok in toks :
        pdb = tok[0]
        chain = str(tok[1])
        m = Model( env, file=pdb, model_segment=('FIRST:'+chain, 'LAST:'+chain) )
        aln.append_model( m, atom_files=pdb, align_codes=pdb+chain )

    try:
        aln.malign()
        aln.malign3d()
        aln.compare_structures()
        aln.id_table(matrix_file='/tmp/' + code + '_family.mat')
        env.dendrogram(matrix_file='/tmp/' + code + '_family.mat', cluster_cut=-1.0)
    except Exception as e:
        print( "\n===>Error : ", e )

    strn = aln[0]._Sequence__get_code()
    return ( strn[:4], strn[4] )



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







def queue_insert( lock, queue, seq ) :
    print( 'insert : ', seq.code )
    lock.acquire()
    queue.append( seq )
    lock.release()


def queue_pop( lock, queue ) :
    while 0 == len(queue) :
        pass

    lock.acquire()
    seq = queue.pop(0)
    lock.release()
    print( 'pop : ', seq.code )
    return seq



def sequence_string( seq ) :
    return ''.join( [ res.code for res in seq.residues ] )



def reader_func( lock, queue ) :
    seqfilenanme = '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences.fasta'
    seqfile = modfile.File( seqfilenanme )
    num = 0
    aln = Alignment(env)
    while aln.read_one( seqfile, alignment_format='FASTA' ) :
        seq = aln[-1]
        print( '\n\n===>reader ', len(queue), type(seq), ' : ', seq.code,  ' : ', seq.name, ' : ',  len(seq.residues),  ' : ',  seq._Sequence__get_nseg(), '\n\n' )
        # obj = MyObject( seq.code, sequence_string(seq) )
        queue_insert( lock, queue, seq )
        if len(aln) > 10 :
            break
    seqfile.close()
    queue_insert( lock, queue, null  )   # end of queue



def proc_func( lock, queue ) :
    while True :
        seq = queue_pop( lock, queue )
        print( '\n\n####>procfunc : ', seq.code, "\n\n" )
        if not seq.code :
            break


def main_0() :
    m = Manager()
    queue = m.list()
    lock = Lock()

    readerfunc = Process( target=reader_func, args=( lock, queue ) )
    procfunc = Process( target=proc_func, args=( lock, queue ) )

    readerfunc.start()
    procfunc.start()

    readerfunc.join()
    procfunc.join()




def read_single_sequence( seqfile, format ) :
    try :
        aln = Alignment(env)
        aln.read_one( seqfile, alignment_format='FASTA' )
        # seq = aln[-1]
        # print( '\n===>reader ', len(aln), type(seq), ' : ', seq.code,  ' : ', seq.name, ' : ',  len(seq.residues),  ' : ',  seq._Sequence__get_nseg(), '\n' )
    except :
        print( '\n===>reader exception : ', aln[0].code,  ' : ', aln[0].name, ' : ',  len(aln[0].residues),  ' : ',  aln[0]._Sequence__get_nseg(), '\n' )
    return aln


def reader( fname ) :
    seqfile = modfile.File( fname )
    alns = []
    while True :
        aln = read_single_sequence( seqfile, "FASTA" )    
        alns.append( aln )
        #if 100 <= len(alns) :
        #    break
        if ( 0 == ( len(alns) % 1000 ) ) :
            print( len(alns) )
    seqfile.close()

    if False :
        print( f"\n\n===>total num of sequences : {len(alns)}\n" )
        for aln in alns :
            seq = aln[0]
            print( type(seq), ' : ', seq.code,  ' : ', seq.name, ' : ',  len(seq.residues),  ' : ',  seq._Sequence__get_nseg(), '\n' )

    return alns


def reader_1( fname ) :
    aln = Alignment(env)
    aln.append( fname, alignment_format='FASTA' )
    return aln


def builder( sema, sdb, aln ) :
    sema.acquire()
    ( pdb, chain, fid, evalue ) = find_sequence_homology( sdb, aln )
    if( 30.0 < fid ) :
        print( "\n\n===> best homology found for %s : %s %s %f %f\n" % ( aln[0].code, pdb, chain, fid, evalue ) )
        build_structure_from_template( pdb, chain, aln )
    else :
        print( "\n\n===> no   homology found for %s : %s %s %f %f... skipping...\n" % ( aln[0].code, pdb, chain, fid, evalue ) )
    sema.release()



def main_1() :
    seqfilenanme = '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences.fasta'
    alns = reader( seqfilenanme )

    sdb = read_pdb_sequence_db()
    procs = [ Process( target=builder, args=(sdb, aln, ) ) for aln in alns ]

    for proc in procs :
        proc.start()

    for proc in procs :
        proc.join()



def read_and_build( sdb, fname ) :
    concurrency = 16
    sema = Semaphore( concurrency )
    processes = []
    

    seqfile = modfile.File( fname )
    aln = Alignment(env)
    num = 0
    while True:
        aln = read_single_sequence( seqfile, format )
        p = Process( target=builder, args=( sema, sdb, aln,) )
        p.start()
        processes.append( p )

        num = num + 1
        if 100 <= num :
            break
        if 0 == ( num % 100 ) :
            print( '===>', num, aln[0].code,  ' : ', aln[0].name, ' : ',  len(aln[0].residues),  ' : ', '\n' )
    seqfile.close()

    for p in processes :
        p.join()

    

def main_2() :
    sdb = read_pdb_sequence_db()
    seqfilenanme = '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences.fasta'
    alns = read_and_build( sdb, seqfilenanme )





class MyClass :
    def __init__( self, code, seq ) :
        self.code = code
        self.seq = seq

def sequence_string( seq ) :
    return ''.join( [ res.code for res in seq.residues ] )


def builder2( sdb, obj ) :
    print( '1--->', obj.code, obj.seq )
    aln = Alignment( env )
    aln.append_sequence( obj.seq )
    aln[0].code = obj.code
    print( '2--->', aln[0].code, sequence_string(aln[0]) )

    ( pdb, chain, fid, evalue ) = find_sequence_homology( sdb, aln )
    print( '\n\n===>builder ', aln.keys(),  ' : ', aln._Sequence__get_name(), ' : ',  aln._Sequence__get_nres(),  ' : ',  aln._Sequence__get_nseg() )

    if 30.0 < fid :
        print( "\n\n===> best homology found for %s : %s %s %f %f\n" % ( aln[0].code, pdb, chain, fid, evalue ) )
        build_structure_from_template( pdb, chain, aln )
    else :
        print( "\n\n===> no   homology found for %s : %s %s %f %f... skipping...\n" % ( aln[0].code, pdb, chain, fid, evalue ) )


def read_and_build_func( sdb, fname ) :
    MAX_WORKERS : int = 4
    thread_pool : ProcessPoolExecutor = ProcessPoolExecutor( max_workers=MAX_WORKERS )
    threads : T.List(Future) = []

    seqfile = modfile.File( fname )
    num = 0
    while True:
        aln = read_single_sequence( seqfile, format )
        obj = MyClass( aln[0].code, sequence_string( aln[0] ) )
        threads.append( thread_pool.submit( builder2, sdb, obj ) )

        num = num + 1
        if 0 == ( num % 10 ) :
            print( '===>', num, aln[0].code,  ' : ', aln[0].name, ' : ',  len(aln[0].residues),  ' : ', '\n' )
        if 20 <= num :
            break
    seqfile.close()

    wait( threads )


def main() :
    sdb = read_pdb_sequence_db()
    seqfilenanme = '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences-100000.fasta'
    read_and_build_func( sdb, seqfilenanme )
    # aln = Alignment(env)
    # aln.append( seqfilenanme, alignment_format='FASTA' )
    # print( len(aln) )




if __name__ == '__main__' :
    main()





