from modeller import * 
from modeller.automodel import * 
import tempfile
import time
from multiprocessing import Pool, Process, Lock
from multiprocessing import Manager

log.verbose()
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



def main0() :
    sdb = read_pdb_sequence_db()

    aln = Alignment(env)

    seqfilenanme = '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences.fasta'
    seqfile = modfile.File( seqfilenanme )

    num = 0
    while aln.read_one( seqfile, alignment_format='FASTA' ) :
        print( '\n\n===>', aln[0].code,  ' : ', aln[0]._Sequence__get_name(), ' : ',  aln[0]._Sequence__get_nres(),  ' : ',  aln[0]._Sequence__get_nseg() )
		
        ( pdb, chain, fid, evalue ) = find_sequence_homology( sdb, aln )
        print( "\n===> found best homology for %s : %s %s %f %f\n" % ( aln[0].code, pdb, chain, fid, evalue ) )

        if( 30.0 < fid ) :
            build_structure_from_template( pdb, chain, aln )
            num = num + 1
            if num > 10 : 
                break

        aln.clear()

    seqfile.close()



def func(aln) :
    print( '\n\n\n\n===>', aln[0].code,  ' : ', aln[0]._Sequence__get_name(), ' : ',  aln[0]._Sequence__get_nres(),  ' : ',  aln[0]._Sequence__get_nseg() )
    return
    ( pdb, chain, fid, evalue ) = find_sequence_homology( sdb, aln )
    print( "\n===> found best homology for %s : %s %s %f %f\n" % ( aln.code, pdb, chain, fid, evalue ) )
    if( 30.0 < fid ) :
        build_structure_from_template( pdb, chain, aln )
    return    



def main2() :

    # sdb = read_pdb_sequence_db()

    seqfilenanme = '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences.fasta'
    seqfile = modfile.File( seqfilenanme )

    num = 0
    with Pool(processes=12) as pool :
        aln = Alignment(env)
        while aln.read_one( seqfile, alignment_format='FASTA' ) :
            print( '\n\n===>For target protein ', aln[0].code,  ' : ', aln[0]._Sequence__get_name(), ' : ',  aln[0]._Sequence__get_nres(),  ' : ',  aln[0]._Sequence__get_nseg() )

            pool.map( func, (aln,) )
            break
            
            num = num + 1
            if num > 10 : 
                break

            aln.clear()

        seqfile.close()

    print( "\n\n===> total ", len( alns ), " sequences read...\n\n" )

    processes = [ Process( target=func, args=(aln,)) for aln in alns ]        
    for p in processes :
        p.start()
    for p in processes :
        p.join()







def cfg_queue_push( lock, queue, aln ) :
    with lock:
        queue.append( aln )
        a = queue[-1]
        print( '####>', aln[0].code, len(queue), type(a), type(a[0]), dir(a) )


def cfg_queue_pop( lock, queue ) :
    with lock :
        return queue.pop(0)


def reader_func( lock, queue ) :
    seqfilenanme = '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences.fasta'
    seqfile = modfile.File( seqfilenanme )

    num = 0
    aln = Alignment(env)
    while aln.read_one( seqfile, alignment_format='FASTA' ) :
        print( '\n\n===>reader ', len(queue), ' : ', aln[0].code,  ' : ', aln[0]._Sequence__get_name(), ' : ',  aln[0]._Sequence__get_nres(),  ' : ',  aln[0]._Sequence__get_nseg() )
        cfg_queue_push( lock, queue, aln )
        num = num + 1
        if num > 10 : 
            break
        aln.clear()

    seqfile.close()

   
def builder_func( lock, queue ) :
    print( "\n\n\n===>Builder func ", len(queue), "\n\n\n")
    while True :
        aln=cfg_queue_pop( lock, queue )
        # print( '\n\n===>builder ', len(queue), aln.keys(),  ' : ', aln._Sequence__get_name(), ' : ',  aln._Sequence__get_nres(),  ' : ',  aln._Sequence__get_nseg() )
        print( '\n\n===>builder ', len(queue), aln[0].code )


    




def main() :
    
    m = Manager()
    cfg_queue = m.list()
    cfg_lock = Lock()

    reader = Process( target=reader_func, args=(cfg_lock,cfg_queue,) )
    builder = Process( target=builder_func, args=(cfg_lock,cfg_queue,) )
    
    reader.start()
    print("queue=", len(cfg_queue))
    time.sleep(3)
    builder.start()
    
    reader.join()
    builder.join()


if __name__ == "__main__":
    main()





