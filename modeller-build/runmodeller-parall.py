import os
import multiprocessing
from multiprocessing import Pool, Process, Lock, Manager, Semaphore
from concurrent.futures import ProcessPoolExecutor, Future, wait
import typing as T
import tempfile

from modeller import *
from modeller.automodel import *

log.verbose()
log.level(output=0, notes=0, warnings=0, errors=1, memory=0)
env = Environ()
env.io.atom_files_directory = ['/share/databases/PDB', '../atom_files']
env.libs.topology.read('${LIB}/top_heav.lib')
env.libs.parameters.read('${LIB}/par.lib')


if False :
    a = AutoModel(env,
                alnfile  = 'alignment.ali',
                knowns   = '5fd1',
                sequence = '1fdx')
    a.starting_model= 1
    a.ending_model  = 1

    a.make()



def binary_pdb_sequence_db( alldb=False ) -> str :
    global env
    sdb = SequenceDB(env)
    pirfile = '../pir/20220710_pdb95.pir'
    if alldb == True :
        pirfile = '../pir/pdball.pir'
    sdb.read(seq_database_file=pirfile, seq_database_format='PIR', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True)

    sdbfname = os.path.join( '/tmp', '20220710_pdb95.pir.bin' )
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
    global env
    code = aln[0].code
    prf = aln.to_profile()

    prf.build(seqdb, matrix_offset=-450, rr_file='${LIB}/blosum62.sim.mat',
              gap_penalties_1d=(-500, -50), n_prof_iterations=1,
              check_profile=False, max_aln_evalue=0.01)

    if( False ) :
        write_read_profile( prf )

    return find_best_profile( prf )




def sequence2string( seq ) -> str :
    return ''.join( [ res.code for res in seq.residues ] )




def read_sequence_fasta( f ) :
    aln = Alignment(env)
    while True :
        try :
            aln.read_one( f, alignment_format='FASTA' )
        except :
            pass
        yield aln




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



def build2( sdb, code, seq ) :
    print( 'builder3' )


def build_0( sdb, fname ) :
    with open( fname, 'r' ) as f :
        aln = Alignment(env)
        aln.append( f )
        aln.check()
        ( pdb, chain, fid, evalue ) = find_sequence_homology( sdb, aln )
        if( 30.0 < fid ) :
            print( "\n\n===> best homology found for %s : %s %s %f %f\n" % ( aln[0].code, pdb, chain, fid, evalue ) )
            print( "build", aln[0].code, sequence2string(aln[0]) )
            build_structure_from_template( pdb, chain, aln )
        else :
            print( "\n\n===> no   homology found for %s : %s %s %f %f... skipping...\n" % ( aln[0].code, pdb, chain, fid, evalue ) )


def build3( sdb, aln ) :
    print( aln[0].code )


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


def func( sdbfname, f ) :

    MAX_WORKERS : int = 12
    with ProcessPoolExecutor( max_workers=MAX_WORKERS ) as thread_pool :
        threads : T.List(Future) = []
        count = 0
        while True :
            aln = next( read_sequence_fasta( f ), None )
            if len( aln ) == 0 :
                break
            count = count + 1
            if 100 < count :
                break

            # aln.check()

            code : str = aln[0].code
            seq : str = sequence2string( aln[0] )
            threads.append( thread_pool.submit( build, sdbfname, code, seq ) )


            #with tempfile.TemporaryFile() as f :
                #aln.write(f)
                #f.seek(0)
                #aln2 = Alignment(env)
                #aln2.read_one(f)
                # threads.append( thread_pool.submit( build, sdb, aln2 ) )
            #print( count, aln[0].code )

            # mm = Manager()
            # mm.start()
            # mm.register( 'Alignment', Alignment )
            # m = mm.Alignment( env )
            # threads.append( thread_pool.submit( build, sdb, m ) )
            # m.close()


            #with StringIO() as f :
            #    aln.write( f )
            #    threads.append( thread_pool.submit( build, sdb, f ) )

            # seq = aln[0]
            #fname = str('/tmp/') + seq.code + '.alignment'
            #f = open( fname, 'w' )
            #aln.write( f )
            #f.close()
            # threads.append( thread_pool.submit( build, sdb, fname ) )

            #with StringIO() as f :
                #aln.write(f)
                #f.seek(0)
            #threads.append( thread_pool.submit( build, sdb, 'code' ) )

        wait( threads )


def main() :
    sdbfname = binary_pdb_sequence_db()
    filename = '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences.fasta'
    filename = '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences-100000.fasta'
    with open( filename, 'r' ) as f :
        func( sdbfname, f )


if __name__ == '__main__' :
    main()



