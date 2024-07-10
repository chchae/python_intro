from modeller import *

env = Environ()

env.io.atom_files_directory = ['.', '../atom_files']


aln = Alignment(env)
for (pdb, chain) in (
		('4lg4', 'D' ),
		('4usf', 'A' ),
		('5dew', 'B' ),
		('5kbr', 'A' ),
		('5owq', 'A' ),
		('6hxf', 'A' ),
		('7z4v', 'A' ),
		('8a5j', 'A' ),
		('2x7f', 'E' ),
		('4ux9', 'B' ),
		('5awm', 'A' ),
		('5kbr', 'B' ),
		('6ao5', 'A' ),
		('7b32', 'A' ),
		('8a5j', 'B' ),
		('2x7f', 'D' ),
		('4nzw', 'B' ),
		('6e2n', 'A' ),
		('6oyt', 'C' ),
		('6e2m', 'B' ),
		('6oyt', 'A' ),
		('6e2n', 'B' ),
		('6oyt', 'B' ) ):
    m = Model(env, file=pdb, model_segment=('FIRST:'+chain, 'LAST:'+chain))
    aln.append_model(m, atom_files=pdb, align_codes=pdb+chain)		

aln.malign()
aln.malign3d()
aln.compare_structures()
aln.id_table(matrix_file='family.mat')
env.dendrogram(matrix_file='family.mat', cluster_cut=-1.0)

