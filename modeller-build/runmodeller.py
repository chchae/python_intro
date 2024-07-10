from modeller import *
from modeller.automodel import *
import tempfile

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


def find_sequence_homology( seqdb, code, sequence ) :
    global env
    aln = Alignment(env)
    #aln.append(file=seqcode + '.fasta', alignment_format='PIR', align_codes='ALL')
    aln.append_sequence( sequence )
    aln[-1].code = code
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



def build_structure_from_template( pdb, chain, code, sequence ) :
    global env
    mdl = Model(env, file=pdb, model_segment=('FIRST:'+chain, 'LAST:'+chain) )
    aln = Alignment(env)
    aln.append_model(mdl, align_codes=pdb+chain, atom_files='pdb'+pdb+'.ent.gz')
    
    aln.append_sequence( sequence )
    aln[-1].code = code
    
    aln.align2d(max_gap_length=50)
    
    a = AutoModel(env, alnfile=aln,
        knowns=pdb+chain, sequence=code,
        assess_methods=(assess.DOPE,
        #soap_protein_od.Scorer(),
        assess.GA341))
    a.starting_model = 1
    a.ending_model = 1
    a.make()



def get_target_seq() :
    data = {
        'map3k3' : 'WRRGKLLGQGAFGRVYLCYDVDTGRELASKQVQFDPDSPETSKEVSALECEIQLLKNLQHERIVQYYGCLRDRAEKTLTIFMEYMPGGSVKDQLKAYGALTESVTRKYTRQILEGMSYLHSNMIVHRDIKGANILRDSAGNVKLGDFGASKRLQTICMSGTGMRSVTGTPYWMSPEVISGEGYGRKADVWSLGCTVVEMLTEKPPWAEYEAMAAIFKIATQPTNPQLPSHISEHGRDFLRRIFVEARQRPSAEELLTHHFA',
        'mp2k3'  : 'LVTISELGRGAYGVVEKVRHAQSGTIMAVKRIRATVNSQEQKRLLMDLDINMRTVDCFYTVTFYGALFREGDVWICMELMDTSLDKFYRKVLDKNMTIPEDILGEIAVSIVRALEHLHSKLSVIHRDVKPSNVLINKEGHVKMCDFGISGYLVDSVAKTMDAGCKPYMAPERINPELNQKGYNVKSDVWSLGITMIEMAILRFPYESWGTPFQQLKQVVEEPSPQLPADRFSPEFVDFTAQCLRKNPAERMSYLELMEHPFF',
        'epha7'  : 'IKIERVIGAGEFGEVCSGRLKLPGKRDVAVAIKTLKVGYTEKQRRDFLCEASIMGQFDHPNVVHLEGVVTRGKPVMIVIEFMENGALDAFLRKHDGQFTVIQLVGMLRGIAAGMRYLADMGYVHRDLAARNILVNSNLVCKVSDFGLSRVIEDDPEAVYTTTGGKIPVRWTAPEAIQYRKFTSASDVWSYGIVMWEVMSYGERPYWDMSNQDVIKAIEEGYRLPAPMDCPAGLHQLMLDCWQKERAERPKFEQIVGILDKMI'
    }
    return data



if __name__ == "__main__":
    sdb = read_pdb_sequence_db()

    targets = get_target_seq()
    for code, seq in targets.items():
        # toks = find_sequence_homology( sdb, code )[:5]
        # ( pdb, chain ) = align_sequence_structure_for_best_template( toks, code )
        ( pdb, chain, fid, evalue ) = find_sequence_homology( sdb, code, seq )
        print( "\n===> found best homology for %s : %s %s %f %f\n" % ( code, pdb, chain, fid, evalue ) )
        build_structure_from_template( pdb, chain, code, seq )
        break



