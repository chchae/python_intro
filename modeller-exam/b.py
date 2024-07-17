from modeller import *
import tempfile

log.verbose()
env = Environ()
env.io.atom_files_directory = ['.', '../atom_files']


sdb = SequenceDB(env)
sdb.read(seq_database_file='20220710_pdb95.pir', seq_database_format='PIR', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True)

aln = Alignment(env)
aln.append(file='map3k3.fasta', alignment_format='PIR', align_codes='ALL')
prf = aln.to_profile()

prf.build(sdb, matrix_offset=-450, rr_file='${LIB}/blosum62.sim.mat',
          gap_penalties_1d=(-500, -50), n_prof_iterations=1,
          check_profile=False, max_aln_evalue=0.01)

if( False ) :
	prf.write(file='build_profile.prf', profile_format='TEXT')
	aln = prf.to_alignment()
	aln.write(file='build_profile.ali', alignment_format='PIR')


with tempfile.NamedTemporaryFile() as prfile:
	prf.write(file=prfile, profile_format='TEXT')
	with open( prfile.name ) as ifile:
		toks = [ line.split() for line in ifile.readlines() if not line.startswith('#' ) ]
		toks = [ ( tok[1][:4], tok[1][4:], tok[10] ) for tok in toks if float(tok[10]) > 35.0 ]
		toks = sorted( toks, key=lambda x: x[2], reverse=True )
		for tok in toks:
			print( tok[0], tok[1], tok[2] )
			

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
	aln.id_table(matrix_file='family.mat')
	env.dendrogram(matrix_file='family.mat', cluster_cut=-1.0)
except Exception as e:
	print( "\n===>Error : ", e )



